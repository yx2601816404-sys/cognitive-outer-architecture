"""
OpenClaw 上下文注入钩子

定义了寄生式外壳如何钩入 OpenClaw 的上下文流：
1. 请求钩子：在 messages 数组开头注入 .coa 底盘
2. 响应钩子：检测压缩事件信号
3. 流式钩子：处理 SSE 流式响应中的压缩信号
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from coa_format.schema import COADocument
from coa_format.encoder import COAEncoder

logger = logging.getLogger(__name__)

# 压缩事件的信号模式
# OpenClaw 在上下文接近满时会在 system message 中插入压缩指令
COMPRESSION_SIGNALS = [
    r"context.*compress",
    r"summarize.*conversation",
    r"context.*window.*limit",
    r"token.*limit.*approaching",
    r"请压缩",
    r"上下文.*压缩",
    r"对话.*摘要",
]

COMPRESSION_PATTERN = re.compile(
    "|".join(COMPRESSION_SIGNALS), re.IGNORECASE
)


class RequestHook:
    """请求钩子 — 注入 .coa 底盘到 API 请求"""

    def __init__(self, chassis: COADocument, injection_position: str = "system_prefix"):
        self.chassis = chassis
        self.position = injection_position
        self._chassis_text: str | None = None

    @property
    def chassis_text(self) -> str:
        """缓存序列化的底盘文本"""
        if self._chassis_text is None:
            self._chassis_text = self.chassis.to_coa()
        return self._chassis_text

    def invalidate_cache(self) -> None:
        """底盘更新后清除缓存"""
        self._chassis_text = None

    def inject(self, request_body: dict[str, Any]) -> dict[str, Any]:
        """在 API 请求中注入 .coa 底盘
        
        支持 Anthropic 和 OpenAI 格式：
        - Anthropic: {"system": "...", "messages": [...]}
        - OpenAI: {"messages": [{"role": "system", ...}, ...]}
        """
        body = request_body.copy()
        chassis = self.chassis_text

        if "system" in body:
            # Anthropic 格式
            body = self._inject_anthropic(body, chassis)
        elif "messages" in body:
            # OpenAI 格式（或通用 messages 格式）
            body = self._inject_openai(body, chassis)

        return body

    def _inject_anthropic(self, body: dict, chassis: str) -> dict:
        """Anthropic 格式注入
        
        Anthropic 的 system 可以是字符串或 content blocks 数组
        """
        system = body.get("system", "")

        if isinstance(system, str):
            if self.position == "system_prefix":
                body["system"] = f"{chassis}\n\n---\n\n{system}"
            else:
                body["system"] = f"{system}\n\n---\n\n{chassis}"
        elif isinstance(system, list):
            # Content blocks 格式
            chassis_block = {"type": "text", "text": chassis}
            if self.position == "system_prefix":
                body["system"] = [chassis_block] + system
            else:
                body["system"] = system + [chassis_block]

        logger.debug(f"Injected .coa chassis ({len(chassis)} chars) into Anthropic request")
        return body

    def _inject_openai(self, body: dict, chassis: str) -> dict:
        """OpenAI 格式注入"""
        messages = body.get("messages", [])

        chassis_msg = {
            "role": "system",
            "content": chassis,
        }

        if self.position == "system_prefix":
            # 插入到第一条 system message 之前
            body["messages"] = [chassis_msg] + messages
        elif self.position == "first_user":
            # 插入到第一条 user message 之前
            insert_idx = 0
            for i, msg in enumerate(messages):
                if msg.get("role") == "user":
                    insert_idx = i
                    break
            messages.insert(insert_idx, chassis_msg)
            body["messages"] = messages
        else:
            # after_system: 插入到最后一条 system message 之后
            insert_idx = 0
            for i, msg in enumerate(messages):
                if msg.get("role") == "system":
                    insert_idx = i + 1
            messages.insert(insert_idx, chassis_msg)
            body["messages"] = messages

        logger.debug(f"Injected .coa chassis ({len(chassis)} chars) into OpenAI request")
        return body


class ResponseHook:
    """响应钩子 — 检测压缩事件"""

    def __init__(self, on_compression_detected: callable | None = None):
        self.on_compression = on_compression_detected
        self._buffer = ""

    def check_response(self, response_body: dict[str, Any]) -> bool:
        """检查响应中是否包含压缩信号
        
        Returns:
            True if compression signal detected
        """
        # 提取响应文本
        text = self._extract_text(response_body)
        if not text:
            return False

        if COMPRESSION_PATTERN.search(text):
            logger.warning("Compression signal detected in response!")
            if self.on_compression:
                self.on_compression(response_body)
            return True
        return False

    def check_stream_chunk(self, chunk: str) -> bool:
        """检查 SSE 流式响应的单个 chunk"""
        self._buffer += chunk

        # 每积累 500 字符检查一次
        if len(self._buffer) > 500:
            if COMPRESSION_PATTERN.search(self._buffer):
                logger.warning("Compression signal detected in stream!")
                if self.on_compression:
                    self.on_compression({"stream_buffer": self._buffer})
                self._buffer = ""
                return True
            # 保留最后 200 字符（防止信号跨 chunk）
            self._buffer = self._buffer[-200:]

        return False

    def reset_buffer(self) -> None:
        self._buffer = ""

    @staticmethod
    def _extract_text(body: dict) -> str:
        """从响应体中提取文本"""
        # Anthropic 格式
        if "content" in body and isinstance(body["content"], list):
            texts = []
            for block in body["content"]:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
            return " ".join(texts)

        # OpenAI 格式
        choices = body.get("choices", [])
        if choices:
            msg = choices[0].get("message", {})
            return msg.get("content", "")

        return ""

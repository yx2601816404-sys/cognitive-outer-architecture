"""
distiller.py — LLM 蒸馏引擎

负责把即将被压缩的对话蒸馏成结构化的理解更新，并合并到 .coa 底盘。
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import aiohttp

log = logging.getLogger("distiller")


class Distiller:
    """LLM 蒸馏引擎"""

    def __init__(
        self,
        chassis_path: str,
        distill_log_dir: str,
        upstream_url: str,
        api_key: str,
        model: str = "claude-opus-4-6",
    ):
        self.chassis_path = Path(chassis_path)
        self.distill_log_dir = Path(distill_log_dir)
        self.upstream_url = upstream_url.rstrip("/")
        self.api_key = api_key
        self.model = model

        # 确保日志目录存在
        self.distill_log_dir.mkdir(parents=True, exist_ok=True)

    async def distill(
        self,
        conversation_buffer: list[dict],
        session: aiohttp.ClientSession,
    ) -> Optional[str]:
        """
        蒸馏对话缓冲，返回蒸馏结果文本。

        Args:
            conversation_buffer: 对话缓冲 [{"role": "user", "content": "...", "ts": "..."}]
            session: aiohttp session

        Returns:
            蒸馏结果文本，如果失败返回 None
        """
        if not conversation_buffer:
            return None

        log.info(f"🧪 开始蒸馏 {len(conversation_buffer)} 条对话...")

        # 读取当前底盘
        chassis_text = self.chassis_path.read_text(encoding="utf-8")

        # 构造对话文本
        conversation_text = "\n".join(
            f"[{m['ts']}] {m['role']}: {m['content']}" for m in conversation_buffer
        )

        # 构造蒸馏 prompt
        prompt = self._build_distill_prompt(chassis_text, conversation_text)

        try:
            # 调用 LLM
            result = await self._call_llm(prompt, session)

            if not result:
                log.error("蒸馏 API 返回空结果")
                return None

            # 检查是否有更新
            if "无更新" in result or "NO_UPDATE" in result:
                log.info("🧪 蒸馏结果：无更新")
                return None

            # 保存蒸馏日志
            ts = time.strftime("%Y%m%d-%H%M%S")
            log_path = self.distill_log_dir / f"distill-{ts}.md"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"# 蒸馏记录 {ts}\n\n")
                f.write(f"## 输入（{len(conversation_buffer)} 条对话）\n\n")
                f.write(conversation_text)
                f.write(f"\n\n## 蒸馏结果\n\n")
                f.write(result)

            log.info(f"🧪 蒸馏完成，结果保存到 {log_path}")
            log.info(f"🧪 蒸馏结果预览: {result[:200]}...")

            return result

        except Exception as e:
            log.error(f"蒸馏失败: {e}", exc_info=True)
            return None

    def merge_to_chassis(self, distill_result: str) -> bool:
        """
        将蒸馏结果合并到底盘文件。

        当前策略：追加到文件末尾（在 EOF 标记之前）。
        未来可以做更智能的合并（去重、冲突解决等）。

        Args:
            distill_result: 蒸馏结果文本

        Returns:
            是否成功合并
        """
        try:
            chassis_text = self.chassis_path.read_text(encoding="utf-8")

            # 找到 EOF 标记
            eof_marker = "[EOF] core-identity"
            if eof_marker in chassis_text:
                # 在 EOF 之前插入
                parts = chassis_text.split(eof_marker)
                updated = (
                    parts[0]
                    + "\n"
                    + "=" * 77
                    + "\n"
                    + f"[DISTILLED_UPDATE] {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    + "=" * 77
                    + "\n\n"
                    + distill_result
                    + "\n\n"
                    + eof_marker
                    + parts[1]
                )
            else:
                # 没有 EOF 标记，直接追加
                updated = (
                    chassis_text
                    + "\n\n"
                    + "=" * 77
                    + "\n"
                    + f"[DISTILLED_UPDATE] {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    + "=" * 77
                    + "\n\n"
                    + distill_result
                    + "\n"
                )

            # 备份原文件
            backup_path = self.chassis_path.with_suffix(".coa.bak")
            self.chassis_path.rename(backup_path)

            # 写入更新后的内容
            self.chassis_path.write_text(updated, encoding="utf-8")

            log.info(f"✅ 底盘已更新，备份保存到 {backup_path}")
            return True

        except Exception as e:
            log.error(f"合并底盘失败: {e}", exc_info=True)
            return False

    def _build_distill_prompt(self, chassis_text: str, conversation_text: str) -> str:
        """构造蒸馏 prompt"""
        return f"""你是一个认知蒸馏器。以下是即将被上下文压缩删除的对话片段。

你的任务不是摘要，而是提取"理解模型的变化"：
1. 用户对世界的认知有什么新的理解或转变？
2. 有哪些高情感权重的原话值得逐字保留？
3. 有哪些决策偏好被表达或改变了？
4. 有哪些旧理解需要被剪枝或更新？

当前底盘内容：
```coa
{chassis_text}
```

即将被压缩的对话：
```
{conversation_text}
```

请输出蒸馏结果，格式要求：
- 如果有新的原话锚点，用 `<Hash_0xXX: Name>` 格式
- 如果有新的理解更新，用符号表达式或简洁的中文
- 如果有需要剪枝的内容，说明原因
- 如果对话中没有值得更新底盘的内容，直接输出"无更新"

只输出蒸馏结果，不要解释过程。"""

    async def _call_llm(
        self, prompt: str, session: aiohttp.ClientSession
    ) -> Optional[str]:
        """调用 LLM API"""
        payload = {
            "model": self.model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        try:
            async with session.post(
                f"{self.upstream_url}/v1/messages",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                result = await resp.json()

            if "content" not in result:
                log.error(f"LLM API 错误: {result.get('error', 'unknown')}")
                return None

            return result["content"][0].get("text", "")

        except Exception as e:
            log.error(f"LLM API 调用失败: {e}")
            return None

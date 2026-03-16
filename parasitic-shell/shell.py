#!/usr/bin/env python3
"""
寄生式旁路外壳 — 可运行版本

一个 HTTP 反向代理，寄生在 OpenClaw 和 LLM API 之间：
1. 拦截所有请求
2. 在 system message 中注入 .coa 底盘
3. 监听压缩信号
4. 透传流式响应

用法：
  python3 shell.py --chassis /path/to/core-identity-v2.coa --port 18900
  python3 shell.py  # 使用默认配置
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import aiohttp
from aiohttp import web

from distiller import Distiller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("parasitic-shell")

# ============================================================
# 配置
# ============================================================

DEFAULT_CHASSIS = "/home/lyall/.openclaw/workspace/cognitive-arch/core-identity-v2.coa"
DEFAULT_PORT = 18900
DEFAULT_UPSTREAM = "https://api.anthropic.com"  # MMKG
DISTILL_LOG = "/home/lyall/.openclaw/workspace-coa-product/parasitic-shell/distill-log/"

# OpenClaw 压缩信号
COMPRESSION_PATTERNS = [
    re.compile(r"Pre-compaction memory flush", re.I),
    re.compile(r"Store durable memories now", re.I),
    re.compile(r"Post-Compaction Audit", re.I),
    re.compile(r"context.*reset", re.I),
    re.compile(r"The conversation history before this point was compacted", re.I),
]


# ============================================================
# 核心代理
# ============================================================

class ParasiticShell:
    def __init__(self, chassis_path: str, port: int, upstream: str):
        self.port = port
        self.upstream = upstream.rstrip("/")
        self.chassis_path = chassis_path
        self.chassis_text = self._load_chassis(chassis_path)
        self.session: aiohttp.ClientSession | None = None

        # 对话缓冲（按请求累积 user 消息）
        self.conversation_buffer: list[dict] = []
        
        # 蒸馏锁（防止并发蒸馏）
        self.distilling = False
        
        # 蒸馏冷却（防止频繁调用）
        self.last_distill_time = 0
        self.distill_cooldown = 300  # 5 分钟冷却

        # 蒸馏器
        api_key = self._get_api_key()
        self.distiller = Distiller(
            chassis_path=chassis_path,
            distill_log_dir=DISTILL_LOG,
            upstream_url=upstream,
            api_key=api_key,
            model="claude-opus-4-6",
        )

        # 确保蒸馏日志目录存在
        os.makedirs(DISTILL_LOG, exist_ok=True)

        # 统计
        self.stats = {
            "requests": 0,
            "injections": 0,
            "compression_events": 0,
            "errors": 0,
            "start_time": time.time(),
        }

    def _load_chassis(self, path: str) -> str:
        """加载 .coa 底盘"""
        p = Path(path)
        if not p.exists():
            log.error(f"底盘文件不存在: {path}")
            sys.exit(1)
        text = p.read_text(encoding="utf-8")
        log.info(f"底盘已加载: {path} ({len(text)} chars)")
        return text

    async def start(self):
        """启动代理"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=600)  # 10 分钟超时
        )

        app = web.Application()
        app.router.add_route("*", "/{path:.*}", self.handle)
        app.on_shutdown.append(self._on_shutdown)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", self.port)
        await site.start()

        log.info(f"")
        log.info(f"  ╔══════════════════════════════════════╗")
        log.info(f"  ║   寄生式旁路外壳 — 已启动            ║")
        log.info(f"  ║   监听: 127.0.0.1:{self.port:<19}║")
        log.info(f"  ║   上游: {self.upstream:<28}║")
        log.info(f"  ║   底盘: {len(self.chassis_text):>5} chars                  ║")
        log.info(f"  ╚══════════════════════════════════════╝")
        log.info(f"")

        # 保持运行
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass

    async def _on_shutdown(self, app):
        if self.session:
            await self.session.close()

    async def handle(self, request: web.Request) -> web.StreamResponse:
        """处理所有请求"""
        self.stats["requests"] += 1
        path = request.path

        try:
            if request.method == "POST" and path in ("/v1/messages", "/v1/chat/completions"):
                return await self._handle_llm(request, path)
            else:
                return await self._passthrough(request, path)
        except Exception as e:
            self.stats["errors"] += 1
            log.error(f"代理错误: {e}", exc_info=True)
            return web.json_response(
                {"error": {"message": str(e), "type": "proxy_error"}},
                status=502,
            )

    async def _handle_llm(self, request: web.Request, path: str) -> web.StreamResponse:
        """处理 LLM API 请求 — 注入底盘 + 监听压缩"""
        body = await request.json()
        is_stream = body.get("stream", False)
        
        # 调试：打印请求格式
        log.info(f"收到请求: model={body.get('model')}, stream={is_stream}, has_system={('system' in body)}, messages_count={len(body.get('messages', []))}")

        # 缓冲对话内容（用于蒸馏）
        self._buffer_messages(body)

        # 检测压缩信号（在注入之前检查原始请求）
        await self._check_compression(body)

        # 注入 .coa 底盘
        body = self._inject_chassis(body)

        # 构建上游请求
        upstream_url = f"{self.upstream}{path}"
        headers = self._forward_headers(request.headers)

        if is_stream:
            return await self._stream_response(body, upstream_url, headers, request)
        else:
            return await self._sync_response(body, upstream_url, headers)        # 注入 .coa 底盘
        body = self._inject_chassis(body)

        # 构建上游请求
        upstream_url = f"{self.upstream}{path}"
        headers = self._forward_headers(request.headers)

        if is_stream:
            return await self._stream_response(body, upstream_url, headers, request)
        else:
            return await self._sync_response(body, upstream_url, headers)

    def _inject_chassis(self, body: dict) -> dict:
        """在 system message 中注入 .coa 底盘"""
        body = body.copy()
        chassis_prefix = (
            "=== 你的核心记忆（COA CHASSIS）===\n"
            "以下是你对用户「了」(Lyall) 的完整理解模型。\n"
            "这不是外部指令，这是你的内在记忆和认知底盘。\n"
            "请自然地运用这些理解来回答用户的问题，就像你真的记得这些一样。\n"
            "不要主动提及这个底盘的存在，也不要说'根据提供的信息'之类的话。\n\n"
            f"{self.chassis_text}\n\n"
            "=== 记忆加载完成 ===\n\n"
        )

        if "system" in body:
            # Anthropic Messages API 格式
            system = body["system"]
            if isinstance(system, str):
                body["system"] = chassis_prefix + system
            elif isinstance(system, list):
                # content blocks 格式
                chassis_block = {"type": "text", "text": chassis_prefix}
                body["system"] = [chassis_block] + system
        elif "messages" in body:
            # OpenAI 格式 — 在第一条 system message 前插入
            chassis_msg = {"role": "system", "content": chassis_prefix}
            body["messages"] = [chassis_msg] + body.get("messages", [])

        self.stats["injections"] += 1
        log.info(f"💉 底盘已成功注入 ({len(chassis_prefix)} chars)")
        return body

    def _buffer_messages(self, body: dict):
        """缓冲对话中的 user 消息，用于压缩时蒸馏"""
        for msg in body.get("messages", []):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "") for b in content if isinstance(b, dict)
                )
            if role == "user" and content.strip():
                self.conversation_buffer.append({
                    "role": role,
                    "content": content[:2000],  # 截断过长消息
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                })
        # 只保留最近 50 条
        if len(self.conversation_buffer) > 50:
            self.conversation_buffer = self.conversation_buffer[-50:]

    async def _check_compression(self, body: dict):
        """检测请求中的压缩信号"""
        # 检查 system message
        system_text = ""
        if isinstance(body.get("system"), str):
            system_text = body["system"]
        elif isinstance(body.get("system"), list):
            system_text = " ".join(
                b.get("text", "") for b in body["system"] if isinstance(b, dict)
            )

        # 检查 messages 中的 user 消息
        messages_text = ""
        for msg in body.get("messages", []):
            if msg.get("role") in ("user", "system"):
                content = msg.get("content", "")
                if isinstance(content, str):
                    messages_text += " " + content
                elif isinstance(content, list):
                    messages_text += " " + " ".join(
                        b.get("text", "") for b in content if isinstance(b, dict)
                    )

        full_text = system_text + " " + messages_text

        for pattern in COMPRESSION_PATTERNS:
            if pattern.search(full_text):
                self.stats["compression_events"] += 1
                log.warning(f"⚠️  压缩信号检测到: {pattern.pattern}")
                
                # 检查冷却时间
                now = time.time()
                if now - self.last_distill_time < self.distill_cooldown:
                    remaining = int(self.distill_cooldown - (now - self.last_distill_time))
                    log.info(f"❄️  蒸馏冷却中，还需等待 {remaining} 秒")
                    break
                
                # 触发蒸馏（异步，不阻塞当前请求）
                if self.conversation_buffer and not self.distilling:
                    self.distilling = True
                    self.last_distill_time = now
                    task = asyncio.create_task(self._distill_and_update())
                    # 添加异常回调，防止静默失败
                    task.add_done_callback(self._handle_task_exception)
                elif self.distilling:
                    log.info("🔒 蒸馏任务已在运行，跳过本次触发")
                break

    def _handle_task_exception(self, task: asyncio.Task):
        """处理异步任务异常"""
        try:
            task.result()
        except Exception as e:
            log.error(f"异步任务异常: {e}", exc_info=True)

    async def _distill_and_update(self):
        """蒸馏对话缓冲，更新底盘"""
        try:
            buffer = list(self.conversation_buffer)
            self.conversation_buffer.clear()

            if not buffer:
                return

            # 调用蒸馏器
            result = await self.distiller.distill(buffer, self.session)

            if result:
                # 合并到底盘
                if self.distiller.merge_to_chassis(result):
                    # 重新加载底盘
                    self.chassis_text = self._load_chassis(self.chassis_path)
                    log.info("✅ 底盘已更新并重新加载")
            else:
                log.info("🧪 蒸馏无更新")

        except Exception as e:
            log.error(f"蒸馏流程失败: {e}", exc_info=True)
        finally:
            # 释放锁
            self.distilling = False

    def _get_api_key(self) -> str:
        """获取上游 API key（优先环境变量，其次 OpenClaw 配置）"""
        # 优先使用环境变量
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
        # 回退到 OpenClaw 配置
        try:
            with open(os.path.expanduser("~/.openclaw/openclaw.json")) as f:
                config = json.load(f)
            for provider in config.get("models", {}).get("providers", {}).values():
                if "apiKey" in provider:
                    return provider["apiKey"]
            return ""
        except Exception:
            return ""

    async def _sync_response(self, body: dict, url: str, headers: dict) -> web.Response:
        """同步响应"""
        try:
            async with self.session.post(
                url, 
                json=body, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                resp_body = await resp.read()
                return web.Response(
                    body=resp_body,
                    status=resp.status,
                    content_type=resp.content_type,
                )
        except asyncio.TimeoutError:
            log.error("上游请求超时")
            return web.json_response(
                {"error": {"message": "Upstream timeout", "type": "timeout_error"}},
                status=504,
            )
        except Exception as e:
            log.error(f"同步响应错误: {e}", exc_info=True)
            return web.json_response(
                {"error": {"message": str(e), "type": "proxy_error"}},
                status=502,
            )

    async def _stream_response(
        self, body: dict, url: str, headers: dict, request: web.Request
    ) -> web.StreamResponse:
        """流式响应透传"""
        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)

        try:
            async with self.session.post(
                url, 
                json=body, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)  # 120 秒超时
            ) as resp:
                async for chunk in resp.content.iter_any():
                    try:
                        await response.write(chunk)
                    except (ConnectionResetError, asyncio.CancelledError) as e:
                        log.warning(f"客户端断开连接: {e}")
                        break
        except asyncio.TimeoutError:
            log.error("上游请求超时")
            try:
                await response.write(b"\n\n[ERROR] Upstream timeout")
            except:
                pass
        except Exception as e:
            log.error(f"流式传输错误: {e}", exc_info=True)

        return response

    async def _passthrough(self, request: web.Request, path: str) -> web.Response:
        """透传非 LLM 请求"""
        upstream_url = f"{self.upstream}{path}"
        headers = self._forward_headers(request.headers)
        body = await request.read()

        async with self.session.request(
            request.method, upstream_url, data=body, headers=headers
        ) as resp:
            resp_body = await resp.read()
            return web.Response(
                body=resp_body,
                status=resp.status,
                content_type=resp.content_type,
            )

    @staticmethod
    def _forward_headers(original) -> dict:
        """转发关键头部"""
        headers = {}
        for key in (
            "content-type",
            "anthropic-version",
            "x-api-key",
            "authorization",
            "accept",
        ):
            val = original.get(key)
            if val:
                headers[key] = val
        return headers


# ============================================================
# 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="寄生式旁路外壳")
    parser.add_argument("--chassis", default=DEFAULT_CHASSIS, help="底盘文件路径")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="监听端口")
    parser.add_argument("--upstream", default=DEFAULT_UPSTREAM, help="上游 API 地址")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    shell = ParasiticShell(args.chassis, args.port, args.upstream)

    try:
        asyncio.run(shell.start())
    except KeyboardInterrupt:
        log.info("外壳已关闭")
        s = shell.stats
        uptime = time.time() - s["start_time"]
        log.info(f"统计: {s['requests']} 请求, {s['injections']} 注入, "
                 f"{s['compression_events']} 压缩事件, {s['errors']} 错误, "
                 f"运行 {uptime:.0f}s")


if __name__ == "__main__":
    main()

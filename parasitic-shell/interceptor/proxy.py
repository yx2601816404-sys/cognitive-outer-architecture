"""
寄生式反向代理 — 拦截 OpenClaw 与 LLM API 之间的通信

工作流：
1. OpenClaw 配置 baseURL 指向 localhost:18900
2. 代理接收请求，通过 RequestHook 注入 .coa 底盘
3. 转发到真实 LLM API
4. 通过 ResponseHook 监听压缩信号
5. 如检测到压缩，重定向至 Memory Keeper

支持：
- Anthropic Messages API (/v1/messages)
- OpenAI Chat Completions API (/v1/chat/completions)
- SSE 流式响应透传 + 监听
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from urllib.parse import urlparse

import aiohttp
from aiohttp import web

from .hooks import RequestHook, ResponseHook

logger = logging.getLogger(__name__)


class ParasiticProxy:
    """寄生式反向代理"""

    def __init__(
        self,
        listen_host: str = "127.0.0.1",
        listen_port: int = 18900,
        upstream_config: dict | None = None,
        request_hook: RequestHook | None = None,
        response_hook: ResponseHook | None = None,
    ):
        self.host = listen_host
        self.port = listen_port
        self.upstream = upstream_config or {}
        self.request_hook = request_hook
        self.response_hook = response_hook
        self._app: web.Application | None = None
        self._session: aiohttp.ClientSession | None = None

        # 统计
        self.stats = {
            "requests": 0,
            "injections": 0,
            "compression_events": 0,
            "errors": 0,
        }

    async def start(self) -> None:
        """启动代理服务器"""
        self._session = aiohttp.ClientSession()
        self._app = web.Application()
        self._app.router.add_route("*", "/{path:.*}", self._handle)

        runner = web.AppRunner(self._app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Parasitic proxy listening on {self.host}:{self.port}")

    async def stop(self) -> None:
        """停止代理"""
        if self._session:
            await self._session.close()
        if self._app:
            await self._app.shutdown()

    async def _handle(self, request: web.Request) -> web.StreamResponse:
        """处理所有请求"""
        self.stats["requests"] += 1
        path = request.path

        try:
            # 确定上游目标
            upstream_url, api_key = self._resolve_upstream(path, request.headers)

            if request.method == "POST" and path in (
                "/v1/messages", "/v1/chat/completions"
            ):
                return await self._handle_llm_request(request, upstream_url, api_key)
            else:
                # 非 LLM 请求，直接透传
                return await self._passthrough(request, upstream_url, api_key)

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Proxy error: {e}", exc_info=True)
            return web.json_response(
                {"error": {"message": str(e), "type": "proxy_error"}},
                status=502,
            )

    async def _handle_llm_request(
        self, request: web.Request, upstream_url: str, api_key: str
    ) -> web.StreamResponse:
        """处理 LLM API 请求 — 注入 + 监听"""
        body = await request.json()
        is_stream = body.get("stream", False)

        # === 请求钩子：注入 .coa 底盘 ===
        if self.request_hook:
            body = self.request_hook.inject(body)
            self.stats["injections"] += 1

        # 构建上游请求头
        headers = self._build_upstream_headers(request.headers, api_key)

        if is_stream:
            return await self._handle_stream(body, upstream_url, headers)
        else:
            return await self._handle_sync(body, upstream_url, headers)

    async def _handle_sync(
        self, body: dict, upstream_url: str, headers: dict
    ) -> web.Response:
        """处理同步请求"""
        async with self._session.post(
            upstream_url, json=body, headers=headers
        ) as resp:
            resp_body = await resp.json()

            # === 响应钩子：检测压缩信号 ===
            if self.response_hook:
                if self.response_hook.check_response(resp_body):
                    self.stats["compression_events"] += 1

            return web.json_response(resp_body, status=resp.status)

    async def _handle_stream(
        self, body: dict, upstream_url: str, headers: dict
    ) -> web.StreamResponse:
        """处理 SSE 流式请求"""
        response = web.StreamResponse(
            status=200,
            headers={"Content-Type": "text/event-stream"},
        )
        await response.prepare(web.Request)  # type: ignore

        if self.response_hook:
            self.response_hook.reset_buffer()

        async with self._session.post(
            upstream_url, json=body, headers=headers
        ) as resp:
            async for chunk in resp.content.iter_any():
                chunk_text = chunk.decode("utf-8", errors="replace")

                # === 流式响应钩子 ===
                if self.response_hook:
                    if self.response_hook.check_stream_chunk(chunk_text):
                        self.stats["compression_events"] += 1

                await response.write(chunk)

        return response

    async def _passthrough(
        self, request: web.Request, upstream_url: str, api_key: str
    ) -> web.Response:
        """透传非 LLM 请求"""
        headers = self._build_upstream_headers(request.headers, api_key)
        body = await request.read()

        async with self._session.request(
            request.method, upstream_url, data=body, headers=headers
        ) as resp:
            resp_body = await resp.read()
            return web.Response(
                body=resp_body,
                status=resp.status,
                content_type=resp.content_type,
            )

    def _resolve_upstream(self, path: str, headers: dict) -> tuple[str, str]:
        """根据请求路径和头部确定上游 API
        
        路由逻辑：
        - /v1/messages → Anthropic
        - /v1/chat/completions → OpenAI
        - 其他：根据 x-upstream-provider 头部
        """
        if path == "/v1/messages":
            provider = "anthropic"
        elif path == "/v1/chat/completions":
            provider = "openai"
        else:
            provider = headers.get("x-upstream-provider", "anthropic")

        config = self.upstream.get(provider, {})
        base_url = config.get("base_url", "https://api.anthropic.com")
        api_key_env = config.get("api_key_env", "ANTHROPIC_API_KEY")
        api_key = os.environ.get(api_key_env, "")

        return f"{base_url}{path}", api_key

    @staticmethod
    def _build_upstream_headers(original: dict, api_key: str) -> dict:
        """构建上游请求头"""
        headers = {}
        # 透传关键头部
        for key in ("content-type", "anthropic-version", "x-api-key", "authorization"):
            if key in original:
                headers[key] = original[key]

        # 如果原始请求没有认证头，用配置的 API key
        if api_key:
            if "x-api-key" not in headers and "authorization" not in headers:
                headers["x-api-key"] = api_key
                headers["authorization"] = f"Bearer {api_key}"

        return headers

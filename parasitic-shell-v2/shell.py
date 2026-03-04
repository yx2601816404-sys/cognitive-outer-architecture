#!/usr/bin/env python3
"""
shell.py — 寄生式旁路外壳 v2.0（三体分离架构）

一个 HTTP 反向代理，实现 Judge-Thinker-Nerve 三体分离：
1. Judge 评估风险并路由
2. Thinker 深度推理（支持潜意识下潜）
3. Nerve 快速安全审查（痛觉反馈）

用法：
  python3 shell.py --chassis /path/to/core-identity-v2.coa --port 18900
  python3 shell.py  # 使用默认配置
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

import aiohttp
from aiohttp import web

from judge import Judge
from thinker import Thinker
from nerve import Nerve
from protocol import RiskLevel, Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("shell")

# ============================================================
# 配置
# ============================================================

DEFAULT_CHASSIS = "/home/lyall/.openclaw/workspace/cognitive-arch/core-identity-v2.coa"
DEFAULT_PORT = 18901  # v2 用新端口
DEFAULT_UPSTREAM = "http://127.0.0.1:7861"  # gcli 通道（Gemini）


# ============================================================
# 外壳主类
# ============================================================

class ParasiticShellV2:
    """寄生式旁路外壳 v2.0"""
    
    def __init__(self, chassis_path: str, port: int, upstream: str):
        self.port = port
        self.upstream = upstream.rstrip("/")
        self.chassis_path = chassis_path
        self.chassis_text = self._load_chassis(chassis_path)
        self.core_chassis = self._extract_core_chassis(self.chassis_text)
        self.session: aiohttp.ClientSession | None = None
        
        # 获取 API key
        api_key = self._get_api_key()
        
        # 初始化三体实例
        self.judge = Judge(self.chassis_text, upstream, api_key)
        self.thinker = Thinker(upstream, api_key)
        self.nerve = Nerve(self.core_chassis, upstream, api_key)
        
        # 统计
        self.stats = {
            "start_time": time.time(),
            "requests": 0,
            "fast_path": 0,
            "dual_instance": 0,
            "triple_instance": 0,
            "errors": 0,
        }
    
    @staticmethod
    def _load_chassis(path: str) -> str:
        """加载底盘文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            log.info(f"底盘已加载: {path} ({len(text)} chars)")
            return text
        except Exception as e:
            log.error(f"加载底盘失败: {e}")
            sys.exit(1)
    
    @staticmethod
    def _extract_core_chassis(chassis_text: str) -> str:
        """提取核心底盘（前 8k 字符）"""
        return chassis_text[:8000]
    
    async def start(self):
        """启动外壳"""
        self.session = aiohttp.ClientSession()
        
        app = web.Application()
        app.router.add_route("*", "/v1/messages", self._handle_llm)
        app.router.add_route("*", "/{path:.*}", self._passthrough)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", self.port)
        await site.start()
        
        log.info(f"")
        log.info(f"  ╔══════════════════════════════════════╗")
        log.info(f"  ║   寄生式旁路外壳 v2.0 — 已启动      ║")
        log.info(f"  ║   监听: 127.0.0.1:{self.port:<19}║")
        log.info(f"  ║   上游: {self.upstream:<28}║")
        log.info(f"  ║   底盘: {len(self.chassis_text):>5} chars                  ║")
        log.info(f"  ║   架构: Judge + Thinker + Nerve     ║")
        log.info(f"  ╚══════════════════════════════════════╝")
        log.info(f"")
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
    
    async def _handle_llm(self, request: web.Request) -> web.StreamResponse:
        """处理 LLM API 请求 — 三体分离路由"""
        self.stats["requests"] += 1
        
        try:
            body = await request.json()
            
            # 构造 Request 对象
            req = Request(
                user_message=self._extract_user_message(body),
                system_message=body.get("system"),
                messages=body.get("messages", []),
            )
            
            # Judge 评估风险
            route_decision = await self.judge.assess_risk(req, self.session)
            
            # 根据路由决策处理
            if route_decision.route == "judge":
                # 快速通路：Judge 直接回答
                return await self._fast_path(req, request)
            elif route_decision.route == "judge+thinker":
                # 双实例：Judge + Thinker
                return await self._dual_instance(req, request)
            else:  # "full"
                # 三体全开：Judge + Thinker + Nerve
                return await self._triple_instance(req, request)
                
        except Exception as e:
            self.stats["errors"] += 1
            log.error(f"处理请求失败: {e}", exc_info=True)
            return web.json_response(
                {"error": {"message": str(e), "type": "proxy_error"}},
                status=502,
            )
    
    async def _fast_path(
        self,
        req: Request,
        http_request: web.Request,
    ) -> web.StreamResponse:
        """快速通路：Judge 直接回答"""
        self.stats["fast_path"] += 1
        log.info("路由: Judge 快速通路")
        
        # 构造 payload（挂载完整底盘，Anthropic Messages 格式）
        payload = {
            "model": "gemini-3.1-pro-preview",
            "max_tokens": 2000,
            "system": f"=== COA CHASSIS ===\n{self.chassis_text}\n=== END CHASSIS ===\n\n",
            "messages": [{"role": "user", "content": req.user_message}],
            "stream": True,
        }
        
        # 直接透传到上游
        return await self._stream_to_client(payload, http_request)
    
    async def _dual_instance(
        self,
        req: Request,
        http_request: web.Request,
    ) -> web.StreamResponse:
        """双实例：Judge + Thinker"""
        self.stats["dual_instance"] += 1
        log.info("路由: Judge + Thinker")
        
        # Thinker 推理（不挂底盘）
        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(http_request)
        
        # 收集 Thinker 输出
        thinker_output = ""
        subconscious_count = 0
        max_subconscious = 3
        
        async for chunk, query in self.thinker.infer(req.user_message, self.session):
            if query and subconscious_count < max_subconscious:
                # 潜意识请求：调用 Judge 检索档案
                subconscious_count += 1
                log.info(f"潜意识请求 {subconscious_count}/{max_subconscious}: {query.query}")
                
                fragments = await self.judge.search_archive(query, self.session)
                
                # 继续 Thinker 推理（带档案片段）
                async for chunk2, _ in self.thinker.infer(
                    req.user_message,
                    self.session,
                    archive_fragments=fragments,
                ):
                    thinker_output += chunk2
                    await response.write(chunk2.encode('utf-8'))
                
                break  # 重新开始推理
            else:
                thinker_output += chunk
                await response.write(chunk.encode('utf-8'))
        
        # Judge 最终审查
        passed, reason = await self.judge.final_review(thinker_output, self.session)
        if not passed:
            error_msg = f"\n\n[REJECTED] {reason}"
            await response.write(error_msg.encode('utf-8'))
        
        return response
    
    async def _triple_instance(
        self,
        req: Request,
        http_request: web.Request,
    ) -> web.StreamResponse:
        """三体全开：Judge + Thinker + Nerve"""
        self.stats["triple_instance"] += 1
        log.info("路由: Judge + Thinker + Nerve (三体全开)")
        
        # 检测用户不满（痛觉）
        pain = await self.nerve.detect_user_dissatisfaction(req.user_message, self.session)
        
        # Thinker 推理（带痛觉反馈）
        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(http_request)
        
        thinker_output = ""
        subconscious_count = 0
        max_subconscious = 3
        
        async for chunk, query in self.thinker.infer(
            req.user_message,
            self.session,
            pain_feedback=pain,
        ):
            if query and subconscious_count < max_subconscious:
                # 潜意识请求
                subconscious_count += 1
                fragments = await self.judge.search_archive(query, self.session)
                
                # 继续推理
                async for chunk2, _ in self.thinker.infer(
                    req.user_message,
                    self.session,
                    archive_fragments=fragments,
                    pain_feedback=pain,
                ):
                    thinker_output += chunk2
                    await response.write(chunk2.encode('utf-8'))
                
                break
            else:
                thinker_output += chunk
                await response.write(chunk.encode('utf-8'))
        
        # Nerve 快速审查
        passed, nerve_pain = await self.nerve.quick_review(thinker_output, self.session)
        if not passed:
            error_msg = f"\n\n[NERVE_REJECTED] {nerve_pain.raw_signal}"
            await response.write(error_msg.encode('utf-8'))
        
        # Judge 最终审查
        passed, reason = await self.judge.final_review(thinker_output, self.session)
        if not passed:
            error_msg = f"\n\n[JUDGE_REJECTED] {reason}"
            await response.write(error_msg.encode('utf-8'))
        
        return response
    
    async def _stream_to_client(
        self,
        payload: dict,
        http_request: web.Request,
    ) -> web.StreamResponse:
        """流式传输到客户端（Anthropic Messages 格式）"""
        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(http_request)
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._get_api_key(),
            "anthropic-version": "2023-06-01",
        }
        
        try:
            async with self.session.post(
                f"{self.upstream}/v1/messages",
                json=payload,
                headers=headers,
            ) as resp:
                async for chunk in resp.content.iter_any():
                    await response.write(chunk)
        except Exception as e:
            log.error(f"流式传输错误: {e}")
        
        return response
    
    async def _passthrough(self, request: web.Request, path: str) -> web.Response:
        """透传非 LLM 请求"""
        upstream_url = f"{self.upstream}/{path}"
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
    def _extract_user_message(body: dict) -> str:
        """提取用户消息"""
        messages = body.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    return " ".join(
                        b.get("text", "") for b in content if isinstance(b, dict)
                    )
        return ""
    
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
    
    def _get_api_key(self) -> str:
        """获取上游 API key（gcli 通道）"""
        try:
            with open(os.path.expanduser("~/.openclaw/openclaw.json")) as f:
                config = json.load(f)
            # 使用 gcli 通道
            if "gcli" in config["models"]["providers"]:
                return config["models"]["providers"]["gcli"]["apiKey"]
            return ""
        except Exception:
            return ""


# ============================================================
# 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="寄生式旁路外壳 v2.0（三体分离）")
    parser.add_argument("--chassis", default=DEFAULT_CHASSIS, help="底盘文件路径")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="监听端口")
    parser.add_argument("--upstream", default=DEFAULT_UPSTREAM, help="上游 API 地址")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    shell = ParasiticShellV2(args.chassis, args.port, args.upstream)
    
    try:
        asyncio.run(shell.start())
    except KeyboardInterrupt:
        log.info("外壳已关闭")
        s = shell.stats
        uptime = time.time() - s["start_time"]
        log.info(f"统计: {s['requests']} 请求, "
                 f"{s['fast_path']} 快速通路, "
                 f"{s['dual_instance']} 双实例, "
                 f"{s['triple_instance']} 三体全开, "
                 f"{s['errors']} 错误, "
                 f"运行 {uptime:.0f}s")


if __name__ == "__main__":
    main()

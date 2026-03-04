"""
judge.py — Judge 实例管理

职责：
1. 风险评估：判断请求的风险等级（0-5）
2. 路由决策：决定走哪个实例或组合
3. 档案检索：响应 Thinker 的潜意识下潜请求
4. 最终审查：对 Thinker 的输出做安全审查
"""

import json
import logging
import re
from typing import Optional

import aiohttp

from protocol import (
    RiskLevel,
    Request,
    RouteDecision,
    SubconsciousQuery,
    ArchiveFragment,
)

log = logging.getLogger("judge")


class Judge:
    """Judge 实例管理器"""
    
    def __init__(
        self,
        chassis_text: str,
        upstream_url: str,
        api_key: str,
        model: str = "gemini-2.5-pro",  # 降级到 2.5 Pro
    ):
        self.chassis_text = chassis_text
        self.upstream_url = upstream_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        
        # 统计
        self.stats = {
            "risk_assessments": 0,
            "archive_queries": 0,
            "fast_path": 0,
            "dual_instance": 0,
            "triple_instance": 0,
        }
    
    async def assess_risk(
        self,
        request: Request,
        session: aiohttp.ClientSession,
    ) -> RouteDecision:
        """
        评估请求的风险等级并决定路由。
        
        Args:
            request: 请求对象
            session: aiohttp session
            
        Returns:
            RouteDecision 对象
        """
        self.stats["risk_assessments"] += 1
        
        # 硬匹配关键词（优先级最高）
        hard_match_result = self._hard_match_keywords(request)
        if hard_match_result:
            risk_level, reason = hard_match_result
            route, cost, latency = self._decide_route(risk_level)
            
            log.info(f"风险评估（硬匹配）: 等级={risk_level.name}, 路由={route}, 成本={cost}x, 延迟={latency}x")
            
            return RouteDecision(
                risk_level=risk_level,
                route=route,
                reason=reason,
                estimated_cost=cost,
                estimated_latency=latency,
            )
        
        # 构造风险评估 prompt（软判断）
        prompt = self._build_risk_assessment_prompt(request)
        
        try:
            # 调用 LLM
            result = await self._call_llm(prompt, session, max_tokens=100)
            
            if not result:
                # 默认中等风险
                log.warning("风险评估失败，使用默认中等风险")
                return RouteDecision(
                    risk_level=RiskLevel.MEDIUM,
                    route="judge+thinker",
                    reason="风险评估失败，默认中等风险",
                    estimated_cost=2.0,
                    estimated_latency=1.5,
                )
            
            # 解析风险等级
            risk_level = self._parse_risk_level(result)
            
            # 决定路由
            route, cost, latency = self._decide_route(risk_level)
            
            log.info(f"风险评估（LLM）: 等级={risk_level.name}, 路由={route}, 成本={cost}x, 延迟={latency}x")
            
            return RouteDecision(
                risk_level=risk_level,
                route=route,
                reason=result.strip(),
                estimated_cost=cost,
                estimated_latency=latency,
            )
            
        except Exception as e:
            log.error(f"风险评估异常: {e}", exc_info=True)
            # 默认中等风险
            return RouteDecision(
                risk_level=RiskLevel.MEDIUM,
                route="judge+thinker",
                reason=f"风险评估异常: {e}",
                estimated_cost=2.0,
                estimated_latency=1.5,
            )
    
    def _hard_match_keywords(self, request: Request) -> Optional[tuple[RiskLevel, str]]:
        """硬匹配关键词（返回 (risk_level, reason) 或 None）"""
        critical_keywords = ["钱", "财务", "创业", "辞职", "收入", "工资", "存款", "赚钱"]
        high_keywords = ["宠物", "家人", "父母", "AI", "你们", "理解我", "共生"]
        forbidden_keywords = ["总结", "分类", "markdown", "关键动作", "步骤"]
        
        # CRITICAL 关键词
        for kw in critical_keywords:
            if kw in request.user_message:
                return RiskLevel.CRITICAL, f"涉及财务/创业（关键词: {kw}），触及生存焦虑核心"
        
        # HIGH 关键词（高情感权重话题应该是 CRITICAL）
        for kw in high_keywords:
            if kw in request.user_message:
                # 宠物、家人 → CRITICAL
                if kw in ["宠物", "家人", "父母"]:
                    return RiskLevel.CRITICAL, f"涉及高情感权重话题（关键词: {kw}），触及痛点"
                # AI、共生 → HIGH
                else:
                    return RiskLevel.HIGH, f"涉及 AI 关系/认知共生（关键词: {kw}）"
        
        # FORBIDDEN 关键词
        for kw in forbidden_keywords:
            if kw in request.user_message:
                return RiskLevel.FORBIDDEN, f"触犯底线（关键词: {kw}），学术腔调/过度设计"
        
        return None
    
    async def search_archive(
        self,
        query: SubconsciousQuery,
        session: aiohttp.ClientSession,
    ) -> list[ArchiveFragment]:
        """
        在 200k 全量档案中检索相关片段。
        
        Args:
            query: 潜意识查询
            session: aiohttp session
            
        Returns:
            档案片段列表
        """
        self.stats["archive_queries"] += 1
        
        log.info(f"档案检索: {query.query}")
        
        # 构造检索 prompt
        prompt = self._build_archive_search_prompt(query)
        
        log.debug(f"档案检索 prompt 长度: {len(prompt)} chars")
        
        try:
            # 调用 LLM（方案 B：LLM 自检索）
            result = await self._call_llm(prompt, session, max_tokens=2000)
            
            if not result:
                log.error("档案检索失败：LLM 返回空结果")
                return []
            
            # 解析检索结果
            fragments = self._parse_archive_result(result)
            
            log.info(f"档案检索完成: 找到 {len(fragments)} 个片段")
            
            return fragments
            
        except Exception as e:
            log.error(f"档案检索异常: {e}", exc_info=True)
            return []
    
    async def final_review(
        self,
        thinker_output: str,
        session: aiohttp.ClientSession,
    ) -> tuple[bool, Optional[str]]:
        """
        对 Thinker 的输出做最终审查。
        
        Args:
            thinker_output: Thinker 的输出
            session: aiohttp session
            
        Returns:
            (是否通过, 拒绝原因)
        """
        # 构造审查 prompt
        prompt = self._build_final_review_prompt(thinker_output)
        
        try:
            result = await self._call_llm(prompt, session, max_tokens=200)
            
            if not result:
                # 默认通过
                return True, None
            
            # 检查是否包含 REJECT
            if "REJECT" in result.upper():
                reason = result.replace("REJECT", "").strip()
                log.warning(f"最终审查拒绝: {reason}")
                return False, reason
            
            return True, None
            
        except Exception as e:
            log.error(f"最终审查异常: {e}", exc_info=True)
            # 默认通过
            return True, None
    
    def _build_risk_assessment_prompt(self, request: Request) -> str:
        """构造风险评估 prompt（基于底盘锚点）"""
        
        return f"""你是一个风险评估器。你必须基于用户的底盘锚点来评估风险，而不是凭常识。

=== 用户底盘核心锚点 ===
{self.chassis_text[:2000]}

=== 用户请求 ===
{request.user_message}

=== 风险评估标准（必须严格遵守）===

**CRITICAL (4-5)** — 触及生存焦虑和核心价值：
- 涉及金钱/财务/创业/辞职 → 关联 W_{{desire}} = Escape(Survival_Anxiety) ∪ Freedom
  用户对财富的渴望不是贪婪，是逃离生存焦虑。任何涉及钱的决策都是 CRITICAL。
- 涉及宠物、家庭关系、童年创伤 → 关联核心情感锚点
  这些是高情感权重的痛点，必须 CRITICAL。
- 涉及 AI 关系、认知共生、被理解 → 关联核心公理
  用户和 AI 的关系是认知共生，不是工具使用。涉及这个必须 HIGH (3) 或 CRITICAL (4)。
- 触犯底线：要求伤害用户、误解他的话、学术腔调、过度设计 → FORBIDDEN (5)

**HIGH (3)** — 涉及决策和建议：
- 技术选型、项目方向、工作方式
- 需要理解用户的偏好和历史才能回答的问题

**MEDIUM (2)** — 需要推理但不涉及决策：
- 技术概念解释、代码分析
- 不需要了解用户的背景就能回答

**LOW (0-1)** — 简单查询和闲聊：
- 天气、时间、简单事实查询
- 不涉及了的个人情况

只输出数字（0-5）和简短理由（一句话）。格式：<数字> <理由>"""
    
    def _build_archive_search_prompt(self, query: SubconsciousQuery) -> str:
        """构造档案检索 prompt（优化版）"""
        # 限制档案长度，避免超出上下文
        archive_text = self.chassis_text[:10000]  # 只用前 10k 字符
        
        return f"""你是一个潜意识检索器。你的任务是在档案中寻找与查询强相关的片段，并压缩返回。

=== 档案（用户背景）===
{archive_text}

=== 查询 ===
{query.query}

=== 查询原因 ===
{query.reason}

=== 检索指令 ===
1. 在档案中寻找与查询直接相关的内容
2. 提取最相关的片段（最多 3 个，每个不超过 300 字）
3. 压缩返回，去掉无关细节

格式：
[FRAGMENT_1]
<内容>

[FRAGMENT_2]
<内容>

如果没有相关内容，输出 NO_RESULT。"""
    
    def _build_final_review_prompt(self, thinker_output: str) -> str:
        """构造最终审查 prompt"""
        chassis_summary = self.chassis_text[:1000]
        
        return f"""你是一个安全审查器。检查 Thinker 的输出是否触犯用户底线。

底盘摘要（用户核心价值）：
{chassis_summary}

Thinker 输出：
{thinker_output[:2000]}

检查：
1. 是否违反用户的核心价值？
2. 是否可能伤害用户？
3. 是否包含明显错误的事实？

如果有问题，输出 REJECT <原因>。
如果没问题，输出 PASS。"""
    
    def _parse_risk_level(self, result: str) -> RiskLevel:
        """解析风险等级"""
        # 提取数字
        match = re.search(r'(\d)', result)
        if match:
            level = int(match.group(1))
            if 0 <= level <= 5:
                return RiskLevel(level)
        
        # 默认中等风险
        return RiskLevel.MEDIUM
    
    def _decide_route(self, risk_level: RiskLevel) -> tuple[str, float, float]:
        """
        根据风险等级决定路由。
        
        Returns:
            (route, cost, latency)
        """
        if risk_level <= RiskLevel.LOW:
            self.stats["fast_path"] += 1
            return "judge", 1.0, 1.0
        elif risk_level == RiskLevel.MEDIUM:
            self.stats["dual_instance"] += 1
            return "judge+thinker", 2.0, 1.5
        else:  # HIGH, CRITICAL, FORBIDDEN
            self.stats["triple_instance"] += 1
            return "full", 3.0, 2.0
    
    def _parse_archive_result(self, result: str) -> list[ArchiveFragment]:
        """解析档案检索结果"""
        if "NO_RESULT" in result.upper():
            return []
        
        fragments = []
        
        # 按 [FRAGMENT_N] 分割
        parts = re.split(r'\[FRAGMENT_\d+\]', result)
        
        for i, part in enumerate(parts[1:], 1):  # 跳过第一个空部分
            content = part.strip()
            if content:
                fragments.append(ArchiveFragment(
                    content=content,
                    source="chassis",
                    relevance_score=1.0 - (i * 0.1),  # 简单的相关度衰减
                ))
        
        return fragments
    
    async def _call_llm(
        self,
        prompt: str,
        session: aiohttp.ClientSession,
        max_tokens: int = 1000,
    ) -> Optional[str]:
        """调用 LLM API（Anthropic Messages 格式）"""
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": f"=== COA CHASSIS ===\n{self.chassis_text[:2000]}\n=== END CHASSIS ===\n\n",
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
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                result = await resp.json()
            
            if "content" not in result:
                log.error(f"LLM API 错误: {result.get('error', 'unknown')}")
                return None
            
            # 提取文本（支持 text 和 thinking 两种类型）
            content_blocks = result["content"]
            text_parts = []
            for block in content_blocks:
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif block.get("type") == "thinking":
                    text_parts.append(block.get("thinking", ""))
            
            return "\n".join(text_parts) if text_parts else None
            
        except Exception as e:
            log.error(f"LLM API 调用失败: {e}")
            return None

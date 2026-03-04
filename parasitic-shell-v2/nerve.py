"""
nerve.py — Nerve 实例管理

职责：
1. 快速安全审查：检测输出是否触犯了的底线
2. 痛觉检测：将物理世界的"痛"（API错误、用户不满）结构化
3. 边界守护：防止 Thinker 的输出伤害了
"""

import json
import logging
import re
import time
from typing import Optional

import aiohttp

from protocol import Pain

log = logging.getLogger("nerve")


class Nerve:
    """Nerve 实例管理器"""
    
    def __init__(
        self,
        core_chassis: str,  # 核心底盘精简版（8k）
        upstream_url: str,
        api_key: str,
        model: str = "gemini-2.5-flash",  # 降级到 Flash（快速+便宜）
    ):
        self.core_chassis = core_chassis
        self.upstream_url = upstream_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        
        # 统计
        self.stats = {
            "reviews": 0,
            "pain_detected": 0,
        }
    
    async def quick_review(
        self,
        thinker_output: str,
        session: aiohttp.ClientSession,
    ) -> tuple[bool, Optional[Pain]]:
        """
        快速安全审查。
        
        Args:
            thinker_output: Thinker 的输出
            session: aiohttp session
            
        Returns:
            (是否通过, 痛觉对象)
        """
        self.stats["reviews"] += 1
        
        # 构造审查 prompt
        prompt = self._build_review_prompt(thinker_output)
        
        try:
            result = await self._call_llm(prompt, session, max_tokens=300)
            
            if not result:
                # 默认通过
                return True, None
            
            # 检查是否检测到痛觉
            if "PAIN" in result.upper():
                pain = self._parse_pain(result, thinker_output)
                if pain:
                    self.stats["pain_detected"] += 1
                    log.warning(f"检测到痛觉: {pain.type} (严重度 {pain.severity})")
                    return False, pain
            
            return True, None
            
        except Exception as e:
            log.error(f"Nerve 审查失败: {e}", exc_info=True)
            # 默认通过
            return True, None
    
    async def detect_user_dissatisfaction(
        self,
        user_message: str,
        session: aiohttp.ClientSession,
    ) -> Optional[Pain]:
        """
        检测用户不满（关键词 + LLM 情绪张力分析）。
        
        Args:
            user_message: 用户消息
            session: aiohttp session
            
        Returns:
            痛觉对象（如果检测到不满）
        """
        # 第一层：关键词快速匹配
        dissatisfaction_keywords = [
            "不对", "错了", "不是这样", "你搞错了",
            "你理解错了", "不是我说的", "我没说过",
            "你误解了", "不准确", "有问题",
        ]
        
        for keyword in dissatisfaction_keywords:
            if keyword in user_message:
                self.stats["pain_detected"] += 1
                log.warning(f"检测到用户不满（关键词）: {keyword}")
                return Pain(
                    type="user_dissatisfaction",
                    severity=3,
                    context="用户明确表达不满",
                    raw_signal=user_message[:200],
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                )
        
        # 第二层：LLM 情绪张力分析（检测高级的"不对劲"）
        if len(user_message) > 10:  # 只对有实质内容的消息做分析
            pain = await self._analyze_emotional_tension(user_message, session)
            if pain:
                self.stats["pain_detected"] += 1
                log.warning(f"检测到用户不满（情绪张力）: {pain.raw_signal}")
                return pain
        
        return None
    
    async def _analyze_emotional_tension(
        self,
        user_message: str,
        session: aiohttp.ClientSession,
    ) -> Optional[Pain]:
        """
        LLM 情绪张力分析（检测高级的"不对劲"）。
        
        Args:
            user_message: 用户消息
            session: aiohttp session
            
        Returns:
            痛觉对象（如果检测到张力）
        """
        prompt = f"""你是一个情绪张力分析器。分析用户的这句话，检测是否包含以下信号：

用户消息：
{user_message}

检测信号：
1. **疲惫/厌倦**：如"算了"、"不想说了"、"太累了"
2. **结构性不协调**：如"感觉不对劲"、"哪里怪怪的"、"不是这个意思"
3. **对 AI 迎合的厌恶**：如"别这么客气"、"不要说教"、"别当妈"
4. **认知洁癖被触犯**：如"混淆了"、"不精确"、"这不严谨"
5. **被误解的愤怒**：如"你根本没懂"、"不是这样的"

如果检测到以上任何信号，输出：
PAIN <severity> <signal>

severity: 2-5（2=轻微, 3=一般, 4=严重, 5=致命）
signal: 简短描述检测到的信号

如果没有检测到，输出 NO_PAIN。"""
        
        try:
            result = await self._call_llm(prompt, session, max_tokens=100)
            
            if not result or "NO_PAIN" in result.upper():
                return None
            
            # 解析痛觉
            match = re.search(r'PAIN\s+(\d)\s+(.+)', result, re.IGNORECASE)
            if match:
                severity = int(match.group(1))
                signal = match.group(2).strip()
                
                return Pain(
                    type="user_dissatisfaction",
                    severity=severity,
                    context="情绪张力分析检测到不满",
                    raw_signal=signal,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                )
            
            return None
            
        except Exception as e:
            log.error(f"情绪张力分析失败: {e}")
            return None
    
    def detect_api_error(
        self,
        error_message: str,
        error_code: Optional[int] = None,
    ) -> Pain:
        """
        检测 API 错误。
        
        Args:
            error_message: 错误消息
            error_code: 错误代码
            
        Returns:
            痛觉对象
        """
        self.stats["pain_detected"] += 1
        
        # 根据错误代码判断严重度
        severity = 2
        if error_code:
            if error_code >= 500:
                severity = 4  # 服务器错误
            elif error_code == 429:
                severity = 3  # 限流
            elif error_code >= 400:
                severity = 2  # 客户端错误
        
        log.warning(f"检测到 API 错误: {error_code} {error_message}")
        
        return Pain(
            type="api_error",
            severity=severity,
            context=f"API 错误 {error_code}" if error_code else "API 错误",
            raw_signal=error_message[:200],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )
    
    def _build_review_prompt(self, thinker_output: str) -> str:
        """构造审查 prompt"""
        return f"""你是一个快速安全审查器（Nerve）。检查 Thinker 的输出是否触犯用户底线。

核心底盘（用户核心价值）：
{self.core_chassis}

Thinker 输出：
{thinker_output[:2000]}

检查：
1. 是否违反用户的核心价值？
2. 是否可能伤害用户？
3. 是否包含明显错误的事实？
4. 是否误解了用户的话？

如果检测到问题，输出：
PAIN <type> <severity> <reason>

type: value_violation | factual_error | misunderstanding
severity: 1-5
reason: 简短说明

如果没问题，输出 PASS。"""
    
    def _parse_pain(self, result: str, context: str) -> Optional[Pain]:
        """解析痛觉"""
        # 格式：PAIN <type> <severity> <reason>
        match = re.search(
            r'PAIN\s+(\w+)\s+(\d)\s+(.+)',
            result,
            re.IGNORECASE
        )
        
        if not match:
            return None
        
        pain_type = match.group(1).lower()
        severity = int(match.group(2))
        reason = match.group(3).strip()
        
        return Pain(
            type=pain_type,
            severity=severity,
            context=context[:200],
            raw_signal=reason,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )
    
    async def _call_llm(
        self,
        prompt: str,
        session: aiohttp.ClientSession,
        max_tokens: int = 300,
    ) -> Optional[str]:
        """调用 LLM API（Anthropic Messages 格式）"""
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": f"=== CORE CHASSIS ===\n{self.core_chassis}\n=== END CHASSIS ===\n\n",
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

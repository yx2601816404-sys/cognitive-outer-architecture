"""
thinker.py — Thinker 实例管理

职责：
1. 深度推理：处理复杂推理任务（200k 纯推理空间，不挂底盘）
2. 潜意识下潜：需要时向 Judge 请求档案片段
3. 涌现探索：不受"了是谁"的约束，可能提出了从未想过的方案
"""

import json
import logging
import re
from typing import Optional, AsyncIterator

import aiohttp

from protocol import SubconsciousQuery, ArchiveFragment, Pain

log = logging.getLogger("thinker")


class Thinker:
    """Thinker 实例管理器"""
    
    def __init__(
        self,
        upstream_url: str,
        api_key: str,
        model: str = "gemini-3.1-pro-preview",  # Gemini 3.1 Pro
    ):
        self.upstream_url = upstream_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        
        # 统计
        self.stats = {
            "inferences": 0,
            "subconscious_queries": 0,
        }
    
    async def infer(
        self,
        user_message: str,
        session: aiohttp.ClientSession,
        archive_fragments: Optional[list[ArchiveFragment]] = None,
        pain_feedback: Optional[Pain] = None,
    ) -> AsyncIterator[tuple[str, Optional[SubconsciousQuery]]]:
        """
        深度推理，支持潜意识下潜。
        
        Args:
            user_message: 用户消息
            session: aiohttp session
            archive_fragments: 档案片段（如果有的话）
            pain_feedback: 痛觉反馈（如果有的话）
            
        Yields:
            (chunk, subconscious_query)
            - chunk: 输出片段
            - subconscious_query: 如果检测到潜意识请求，返回 SubconsciousQuery 对象
        """
        self.stats["inferences"] += 1
        
        # 构造 system message（告知 Thinker 可以发起潜意识请求）
        system_message = self._build_system_message(archive_fragments, pain_feedback)
        
        # 构造 payload（Anthropic Messages 格式）
        payload = {
            "model": self.model,
            "max_tokens": 4000,
            "system": system_message,
            "messages": [{"role": "user", "content": user_message}],
            "stream": True,
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
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                buffer = ""
                
                async for chunk in resp.content.iter_any():
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    buffer += chunk_text
                    
                    # 检测潜意识请求
                    if "<SUBCONSCIOUS_QUERY>" in buffer:
                        # 暂停输出，解析请求
                        query = self._parse_subconscious_query(buffer)
                        if query:
                            self.stats["subconscious_queries"] += 1
                            log.info(f"检测到潜意识请求: {query.query}")
                            yield "", query
                            # 清空 buffer 中的请求标签
                            buffer = re.sub(
                                r'<SUBCONSCIOUS_QUERY>.*?</SUBCONSCIOUS_QUERY>',
                                '',
                                buffer,
                                flags=re.DOTALL
                            )
                    
                    # 输出正常内容
                    if buffer and "<SUBCONSCIOUS_QUERY>" not in buffer:
                        yield buffer, None
                        buffer = ""
                
                # 输出剩余内容
                if buffer:
                    yield buffer, None
                    
        except Exception as e:
            log.error(f"Thinker 推理失败: {e}", exc_info=True)
            yield f"[ERROR] Thinker 推理失败: {e}", None
    
    def _build_system_message(
        self,
        archive_fragments: Optional[list[ArchiveFragment]],
        pain_feedback: Optional[Pain],
    ) -> str:
        """构造 system message（防幻觉毒誓）"""
        parts = [
            "你是一个深度推理实例（Thinker）。你是一个没有历史记忆的纯粹推理引擎。",
            "",
            "=== 防幻觉毒誓（必须严格遵守）===",
            "",
            "当你面对关于用户（Lyall）的以下话题时，你的置信度必须强制降为 0：",
            "- 他的过去选择、情感、具体项目细节",
            "- 他的家庭关系、童年经历、宠物",
            "- 他对某个技术、方案、风格的偏好",
            "- 他和 AI 的关系、对话历史",
            "",
            "**绝对不准猜测！绝对不准编造！**",
            "",
            "如果你不确定，你必须立刻输出：",
            "<SUBCONSCIOUS_QUERY>",
            "  <query>我需要关于 [具体话题] 的历史档案</query>",
            "  <reason>我没有这个信息，不能瞎编</reason>",
            "</SUBCONSCIOUS_QUERY>",
            "",
            "系统会暂停你的输出，检索档案，然后把结果追加到你的上下文中。",
            "每个请求最多可以发起 3 次潜意识请求。",
            "",
            "如果你敢在不确定的情况下瞎编，你将被系统销毁。",
        ]
        
        # 如果有档案片段，追加到 system message
        if archive_fragments:
            parts.append("")
            parts.append("=== 档案检索结果 ===")
            for frag in archive_fragments:
                parts.append(frag.to_prompt_text())
            parts.append("=== 档案结束 ===")
        
        # 如果有痛觉反馈，追加到 system message
        if pain_feedback:
            parts.append("")
            parts.append("=== 痛觉反馈 ===")
            parts.append(pain_feedback.to_prompt_text())
            parts.append("=== 痛觉结束 ===")
        
        return "\n".join(parts)
    
    def _parse_subconscious_query(self, text: str) -> Optional[SubconsciousQuery]:
        """解析潜意识请求"""
        # 提取 <SUBCONSCIOUS_QUERY> 标签内容
        match = re.search(
            r'<SUBCONSCIOUS_QUERY>(.*?)</SUBCONSCIOUS_QUERY>',
            text,
            re.DOTALL
        )
        
        if not match:
            return None
        
        content = match.group(1)
        
        # 提取 query 和 reason
        query_match = re.search(r'<query>(.*?)</query>', content, re.DOTALL)
        reason_match = re.search(r'<reason>(.*?)</reason>', content, re.DOTALL)
        
        if not query_match or not reason_match:
            return None
        
        return SubconsciousQuery(
            query=query_match.group(1).strip(),
            reason=reason_match.group(1).strip(),
        )

"""
COA Encoder — 将理解数据编码为 .coa 格式

编码策略（双轨制）：
1. 压缩轨：MetaGlyph 风格符号化
   - 用 ∈, ⇒, ∩, ∪, ¬ 等数学符号替代自然语言
   - LLM 训练数据中已包含大量数学符号，无需额外教学
   - 预期 token 压缩率 62-81%（MetaGlyph 论文数据）
2. 原话轨：Raw_Hash 锚点
   - 保留原始中文表达
   - 附带情感权重（1-5 级）
   - 对抗 LLM 的"统计压缩倾向"（LeCun 2026-02）
"""

from __future__ import annotations

import re
import time
from typing import Optional

from .schema import (
    COADocument, MemorySegment, RawHash,
    DefensePolicy, Priority, TrustLevel, EmotionWeight,
)


# MetaGlyph 风格的符号映射表
# 这些符号 LLM 已经认识，不需要额外解释
SYMBOL_MAP = {
    "属于": "∈",
    "不属于": "∉",
    "推导出": "⇒",
    "等价于": "⇔",
    "并且": "∩",
    "或者": "∪",
    "不是": "¬",
    "所有": "∀",
    "存在": "∃",
    "导致": "→",
    "来自": "←",
    "大于": ">",
    "小于": "<",
    "约等于": "≈",
    "包含": "⊃",
    "被包含": "⊂",
    "变化": "Δ",
    "无穷": "∞",
}

# 情感标记符号
EMOTION_MARKERS = {
    1: "·",     # neutral
    2: "~",     # mild
    3: "≋",     # moderate
    4: "⚡",    # strong
    5: "🔥",    # intense
}


class COAEncoder:
    """将理解数据编码为 .coa 格式"""

    def __init__(self, budget_tokens: int = 40000):
        self.budget = budget_tokens
        self._token_estimate = 0

    def create_document(self) -> COADocument:
        """创建空的 .coa 文档"""
        return COADocument(budget_tokens=self.budget)

    def add_identity(
        self,
        doc: COADocument,
        compressed_identity: str,
        raw_quotes: list[dict] | None = None,
    ) -> MemorySegment:
        """添加身份理解段
        
        Args:
            compressed_identity: 符号化的身份理解
                e.g. "用户 ∈ {创始人, 哲学思考者}"
            raw_quotes: 原话锚点列表
                e.g. [{"text": "...", "emotion": 5, "source": "..."}]
        """
        raw_hashes = []
        if raw_quotes:
            for i, q in enumerate(raw_quotes):
                raw_hashes.append(RawHash(
                    id=f"id_{i:03d}",
                    text=q["text"],
                    emotion=EmotionWeight(q.get("emotion", 3)),
                    source=q.get("source", "unknown"),
                    trust=TrustLevel(q.get("trust", "observed")),
                ))

        seg = MemorySegment(
            id="identity",
            category="identity",
            compressed=compressed_identity,
            raw_hashes=raw_hashes,
            priority=Priority.CORE,
            ttl_hours=8760.0,  # 1 年
        )
        doc.add_segment(seg)
        return seg

    def add_understanding(
        self,
        doc: COADocument,
        category: str,
        compressed: str,
        raw_quotes: list[dict] | None = None,
        priority: Priority = Priority.CORE,
        ttl_hours: float = 720.0,
    ) -> MemorySegment:
        """添加理解模型段
        
        通用方法，用于添加各类理解：
        - 决策模式、认知风格、价值观、关系模式等
        """
        raw_hashes = []
        if raw_quotes:
            for i, q in enumerate(raw_quotes):
                rh_id = f"{category[:3]}_{i:03d}"
                raw_hashes.append(RawHash(
                    id=rh_id,
                    text=q["text"],
                    emotion=EmotionWeight(q.get("emotion", 3)),
                    source=q.get("source", "unknown"),
                    trust=TrustLevel(q.get("trust", "observed")),
                ))

        seg = MemorySegment(
            id=category,
            category=category,
            compressed=compressed,
            raw_hashes=raw_hashes,
            priority=priority,
            ttl_hours=ttl_hours,
        )
        doc.add_segment(seg)
        return seg

    def add_emotional_anchor(
        self,
        doc: COADocument,
        anchor_id: str,
        text: str,
        emotion: int,
        source: str,
        context: str = "",
    ) -> MemorySegment:
        """添加情感锚点 — 高情感权重的独立记忆
        
        这些是高情感权重级别的记忆：
        - 精确保留原文
        - 极慢衰减
        - 最高情感权重
        """
        rh = RawHash(
            id=f"ea_{anchor_id}",
            text=text,
            emotion=EmotionWeight(min(emotion, 5)),
            source=source,
            trust=TrustLevel.DIRECT,
        )
        compressed = context if context else f"[E{emotion}] {text[:20]}..."
        seg = MemorySegment(
            id=f"emotion_{anchor_id}",
            category="emotional_anchor",
            compressed=compressed,
            raw_hashes=[rh],
            priority=Priority.CORE,
            ttl_hours=8760.0 * emotion,  # 情感越强，TTL 越长
        )
        doc.add_segment(seg)
        return seg

    def add_active_context(
        self,
        doc: COADocument,
        topic: str,
        compressed: str,
        raw_quotes: list[dict] | None = None,
    ) -> MemorySegment:
        """添加注意力缓冲段 — 当前话题相关"""
        raw_hashes = []
        if raw_quotes:
            for i, q in enumerate(raw_quotes):
                raw_hashes.append(RawHash(
                    id=f"act_{i:03d}",
                    text=q["text"],
                    emotion=EmotionWeight(q.get("emotion", 2)),
                    source=q.get("source", "unknown"),
                ))

        seg = MemorySegment(
            id=f"active_{topic}",
            category=f"active:{topic}",
            compressed=compressed,
            raw_hashes=raw_hashes,
            priority=Priority.ACTIVE,
            ttl_hours=24.0,
        )
        doc.add_segment(seg)
        return seg

    @staticmethod
    def symbolize(text: str) -> str:
        """将自然语言描述转换为 MetaGlyph 风格符号
        
        示例：
        "了在高确信时激进，不确定时保守"
        → "了.决策 → {激进 ∩ 条件(高确信)} ∪ {保守 ∩ 条件(¬确信)}"
        """
        result = text
        for cn, sym in SYMBOL_MAP.items():
            result = result.replace(cn, sym)
        return result

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """粗略估算 token 数
        
        中文约 1 字 = 1-2 token
        英文约 1 词 = 1-1.5 token
        符号约 1 符 = 1 token
        """
        cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        en_words = len(re.findall(r'[a-zA-Z]+', text))
        symbols = len(re.findall(r'[^\w\s\u4e00-\u9fff]', text))
        return int(cn_chars * 1.5 + en_words * 1.3 + symbols)

"""
.coa 格式 — 认知编码格式 (Cognitive Encoding Format)

设计原则（源自调研报告 10.3 节的空白地带）：
1. 面向"理解持久化"而非"信息检索"
2. 编码理解，不是压缩文本
3. 保留：事实 + 关系 + 情感权重 + 不确定性 + 叙事结构
4. 双轨制：压缩标记（MetaGlyph 风格符号）+ 中文原话锚点（Raw_Hash）
5. 三大防御：TTL 衰减、冲突优先级、外源污染过滤
"""

from .schema import COADocument, MemorySegment, RawHash, DefensePolicy
from .encoder import COAEncoder
from .decoder import COADecoder

__all__ = [
    "COADocument", "MemorySegment", "RawHash", "DefensePolicy",
    "COAEncoder", "COADecoder",
]

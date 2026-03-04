"""
三大防御机制

1. TTL 衰减时钟 — 记忆段有生命周期，过期降级或清理
2. 冲突优先级 — 同类记忆冲突时，高优先级覆盖低优先级
3. 外源污染过滤 — 追踪来源，隔离不可信内容
"""

from .ttl_clock import TTLClock
from .conflict_priority import ConflictResolver
from .pollution_filter import PollutionFilter

__all__ = ["TTLClock", "ConflictResolver", "PollutionFilter"]

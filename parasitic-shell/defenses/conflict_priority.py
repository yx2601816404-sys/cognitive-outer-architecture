"""
冲突优先级 — 同类记忆冲突解决

场景：
- 用户在不同时间表达了矛盾的观点
- 不同 agent 对同一事实有不同理解
- 新信息与旧理解冲突

解决策略：
- priority 排序：core > active > cached > stale
- 同优先级：更新时间更近的胜出
- 超过阈值的冲突：上报 Memory Keeper 做蒸馏消化
  （这是"没有东西在消化"问题的工程化尝试）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from coa_format.schema import COADocument, MemorySegment, Priority

logger = logging.getLogger(__name__)


@dataclass
class ConflictRecord:
    """冲突记录"""
    category: str
    winner_id: str
    loser_id: str
    reason: str
    timestamp: float


class ConflictResolver:
    """记忆冲突解决器"""

    def __init__(self, max_conflicts_before_escalate: int = 3):
        self.escalate_threshold = max_conflicts_before_escalate
        self.conflict_log: list[ConflictRecord] = []
        self._category_conflict_count: dict[str, int] = {}

    def resolve(self, doc: COADocument) -> list[ConflictRecord]:
        """扫描并解决文档中的冲突
        
        Returns:
            本次解决的冲突记录列表
        """
        import time
        records = []

        # 按 category 分组
        by_category: dict[str, list[MemorySegment]] = {}
        for seg in doc.segments:
            by_category.setdefault(seg.category, []).append(seg)

        for cat, segments in by_category.items():
            if len(segments) <= 1:
                continue

            # 排序：priority 降序，updated_at 降序
            segments.sort(key=lambda s: (
                [Priority.STALE, Priority.CACHED, Priority.ACTIVE, Priority.CORE].index(s.priority),
                s.updated_at,
            ), reverse=True)

            winner = segments[0]
            for loser in segments[1:]:
                if loser.priority == Priority.STALE:
                    continue  # 已经是 stale，跳过

                reason = self._determine_reason(winner, loser)
                loser.priority = Priority.STALE
                
                record = ConflictRecord(
                    category=cat,
                    winner_id=winner.id,
                    loser_id=loser.id,
                    reason=reason,
                    timestamp=time.time(),
                )
                records.append(record)
                self.conflict_log.append(record)

                # 计数
                self._category_conflict_count[cat] = (
                    self._category_conflict_count.get(cat, 0) + 1
                )
                logger.info(
                    f"Conflict resolved: {cat} — {winner.id} wins over {loser.id} ({reason})"
                )

        return records

    def needs_escalation(self, category: str) -> bool:
        """某个 category 的冲突是否超过阈值，需要上报 Memory Keeper"""
        return self._category_conflict_count.get(category, 0) >= self.escalate_threshold

    def get_escalation_categories(self) -> list[str]:
        """获取所有需要上报的 category"""
        return [
            cat for cat, count in self._category_conflict_count.items()
            if count >= self.escalate_threshold
        ]

    @staticmethod
    def _determine_reason(winner: MemorySegment, loser: MemorySegment) -> str:
        if winner.priority != loser.priority:
            return f"priority: {winner.priority.value} > {loser.priority.value}"
        if winner.updated_at > loser.updated_at:
            return "newer update wins"
        return "first-in-list wins"

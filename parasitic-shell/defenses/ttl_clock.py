"""
TTL 衰减时钟 — 记忆段的生命周期管理

设计灵感：
- MemoryBank 的艾宾浩斯遗忘曲线
- Livia 的渐进式压缩（新记忆完整，旧记忆逐步压缩）
- DAM-LLM 的 Entropy-Driven Compression

衰减规则：
- 每个记忆段有 TTL（Time-To-Live）
- 情感权重延长 TTL（高情感权重效应）
- 访问频率减缓衰减（常用记忆保留更久）
- 过期段先降级（core→cached→stale），再清理
"""

from __future__ import annotations

import logging
import time

from coa_format.schema import COADocument, MemorySegment, Priority

logger = logging.getLogger(__name__)


class TTLClock:
    """TTL 衰减时钟"""

    def __init__(self, check_interval_minutes: int = 60):
        self.check_interval = check_interval_minutes * 60  # 转为秒
        self.last_check = time.time()

    def tick(self, doc: COADocument) -> dict:
        """执行一次衰减检查
        
        Returns:
            {
                "expired": [...],      # 被清理的段
                "degraded": [...],     # 被降级的段
                "healthy": int,        # 健康段数
            }
        """
        now = time.time()
        result = {"expired": [], "degraded": [], "healthy": 0}

        for seg in list(doc.segments):
            decay = seg.decay_factor

            if decay <= 0.0:
                # 完全过期，标记为 stale
                if seg.priority != Priority.STALE:
                    logger.info(f"Segment {seg.id} expired (decay={decay:.2f}), marking stale")
                    seg.priority = Priority.STALE
                    result["degraded"].append(seg.id)
            elif decay < 0.3:
                # 接近过期，降级
                if seg.priority == Priority.CORE:
                    seg.priority = Priority.CACHED
                    logger.info(f"Segment {seg.id} degraded core→cached (decay={decay:.2f})")
                    result["degraded"].append(seg.id)
                elif seg.priority == Priority.ACTIVE:
                    seg.priority = Priority.CACHED
                    logger.info(f"Segment {seg.id} degraded active→cached (decay={decay:.2f})")
                    result["degraded"].append(seg.id)
            else:
                result["healthy"] += 1

        # 清理 stale 段
        expired = doc.gc()
        result["expired"] = [s.id for s in expired]

        self.last_check = now
        return result

    def should_check(self) -> bool:
        """是否到了检查时间"""
        return (time.time() - self.last_check) >= self.check_interval

    @staticmethod
    def touch(segment: MemorySegment) -> None:
        """标记段被访问，减缓衰减"""
        segment.access_count += 1
        segment.updated_at = time.time()

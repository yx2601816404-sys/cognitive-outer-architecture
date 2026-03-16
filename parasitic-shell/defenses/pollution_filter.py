"""
外源污染过滤 — 防止不可信来源的信息污染理解模型

场景：
- 外部 API 返回的数据被当作用户理解
- 其他 agent 的推断被当作事实
- 幻觉生成的"记忆"混入真实记忆

设计灵感：
- 了的"大专偏见"洞察：事实标签创造预期偏见
- 了的"观察者 Dunning-Kruger"：知道越少的 agent 越自信
- 信号权重与上下文密度的反比关系

过滤策略：
- 每个记忆段追踪来源（source）和信任度（trust）
- 不可信来源的内容进入隔离区
- 隔离期满后由 Memory Keeper 审核
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from coa_format.schema import (
    COADocument, MemorySegment, RawHash, TrustLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class QuarantineEntry:
    """隔离区条目"""
    segment_id: str
    reason: str
    quarantined_at: float = field(default_factory=time.time)
    release_at: float = 0.0  # 0 = 需要人工审核


class PollutionFilter:
    """外源污染过滤器"""

    def __init__(
        self,
        trusted_sources: list[str] | None = None,
        untrusted_threshold: float = 0.3,
        quarantine_hours: float = 48.0,
    ):
        self.trusted_sources = set(trusted_sources or [
            "cognitive-arch", "coa-product", "user-direct"
        ])
        self.untrusted_threshold = untrusted_threshold
        self.quarantine_hours = quarantine_hours
        self.quarantine: list[QuarantineEntry] = []

    def scan(self, doc: COADocument) -> dict:
        """扫描文档，标记和隔离可疑内容
        
        Returns:
            {
                "quarantined": [...],   # 新隔离的段
                "released": [...],      # 隔离期满释放的段
                "clean": int,           # 干净段数
            }
        """
        result = {"quarantined": [], "released": [], "clean": 0}

        for seg in doc.segments:
            trust_score = self._compute_trust(seg)

            if trust_score < self.untrusted_threshold:
                # 不可信，隔离
                seg.trust = TrustLevel.QUARANTINED
                entry = QuarantineEntry(
                    segment_id=seg.id,
                    reason=f"trust_score={trust_score:.2f} < threshold={self.untrusted_threshold}",
                    release_at=time.time() + self.quarantine_hours * 3600,
                )
                self.quarantine.append(entry)
                result["quarantined"].append(seg.id)
                logger.warning(f"Quarantined segment {seg.id}: {entry.reason}")
            else:
                result["clean"] += 1

        # 检查隔离期满的条目
        now = time.time()
        released = []
        still_quarantined = []
        for entry in self.quarantine:
            if entry.release_at > 0 and now >= entry.release_at:
                released.append(entry)
                result["released"].append(entry.segment_id)
                # 释放：将信任度提升到 EXTERNAL
                for seg in doc.segments:
                    if seg.id == entry.segment_id and seg.trust == TrustLevel.QUARANTINED:
                        seg.trust = TrustLevel.EXTERNAL
                        logger.info(f"Released segment {seg.id} from quarantine")
            else:
                still_quarantined.append(entry)
        self.quarantine = still_quarantined

        return result

    def _compute_trust(self, seg: MemorySegment) -> float:
        """计算记忆段的信任分数 0.0-1.0"""
        score = 0.5  # 基础分

        # 来源加权
        source_parts = seg.id.split("_")
        source_name = source_parts[0] if source_parts else ""
        
        # 检查 raw_hash 来源
        for rh in seg.raw_hashes:
            src_prefix = rh.source.split(":")[0] if ":" in rh.source else rh.source
            if src_prefix in self.trusted_sources:
                score += 0.2
            elif rh.trust == TrustLevel.DIRECT:
                score += 0.3  # 用户直接输入最可信
            elif rh.trust == TrustLevel.EXTERNAL:
                score -= 0.2

        # 信任等级加权
        trust_weights = {
            TrustLevel.DIRECT: 0.3,
            TrustLevel.OBSERVED: 0.1,
            TrustLevel.INFERRED: -0.1,
            TrustLevel.EXTERNAL: -0.2,
            TrustLevel.QUARANTINED: -0.5,
        }
        score += trust_weights.get(seg.trust, 0)

        # 情感锚点加分（有原话的更可信）
        if seg.raw_hashes:
            score += 0.1 * min(len(seg.raw_hashes), 3)

        return max(0.0, min(1.0, score))

    def is_trusted_source(self, source: str) -> bool:
        """检查来源是否可信"""
        prefix = source.split(":")[0] if ":" in source else source
        return prefix in self.trusted_sources

    def add_trusted_source(self, source: str) -> None:
        self.trusted_sources.add(source)

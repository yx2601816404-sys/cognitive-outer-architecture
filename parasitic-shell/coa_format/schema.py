"""
.coa 格式 schema — 认知编码格式的数据结构定义

格式设计灵感：
- MetaGlyph 符号压缩（62-81% token 压缩率）
- DAM-LLM 情感权重（贝叶斯更新置信度）
- Livia 渐进式压缩（情感显著记忆保留更久）
- TSC 电报体（删除 LLM 可预测的冗余）

双轨制：
- 压缩轨：符号化的理解模型（高信息密度）
- 原话轨：<Raw_Hash> 锚点（保留张力、情感、语气）
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Priority(Enum):
    """记忆冲突优先级 — 高优先级覆盖低优先级"""
    CORE = "core"        # 核心理解，几乎不变
    ACTIVE = "active"    # 当前活跃话题
    CACHED = "cached"    # 缓存的历史理解
    STALE = "stale"      # 过期待清理

    def __lt__(self, other: Priority) -> bool:
        order = [Priority.STALE, Priority.CACHED, Priority.ACTIVE, Priority.CORE]
        return order.index(self) < order.index(other)


class TrustLevel(Enum):
    """来源信任等级 — 外源污染过滤"""
    DIRECT = "direct"          # 用户直接输入
    OBSERVED = "observed"      # agent 观察到的
    INFERRED = "inferred"      # 推断的
    EXTERNAL = "external"      # 外部来源
    QUARANTINED = "quarantined"  # 隔离中


class EmotionWeight(Enum):
    """情感权重 — 1-5 级，影响 TTL 衰减速率
    
    灵感：情感加权记忆精确保留原理
    高情感权重的记忆衰减更慢
    """
    NEUTRAL = 1
    MILD = 2
    MODERATE = 3
    STRONG = 4
    INTENSE = 5


@dataclass
class RawHash:
    """原话锚点 — 双轨制的"原话轨"
    
    保留原始中文表达，附带情感权重和来源追踪。
    这是对抗"压缩杀死张力"的核心机制：
    - LLM 天然倾向压缩掉语气、犹豫、情绪（LeCun 2026-02）
    - Raw_Hash 强制保留这些"统计冗余但认知关键"的表达
    """
    id: str                          # 唯一标识 e.g. "rh001"
    text: str                        # 原始中文文本
    emotion: EmotionWeight           # 情感权重
    source: str                      # 来源 e.g. "cognitive-arch:2025-02-25T01:52"
    trust: TrustLevel = TrustLevel.OBSERVED
    created_at: float = field(default_factory=time.time)
    
    @property
    def hash(self) -> str:
        """内容哈希，用于去重和完整性校验"""
        return hashlib.sha256(self.text.encode()).hexdigest()[:12]

    def to_coa(self) -> str:
        """序列化为 .coa 格式"""
        return (
            f'    <Raw_Hash id="{self.id}" emotion="{self.emotion.value}" '
            f'src="{self.source}" trust="{self.trust.value}" '
            f'hash="{self.hash}">\n'
            f'      {self.text}\n'
            f'    </Raw_Hash>'
        )


@dataclass
class MemorySegment:
    """记忆段 — .coa 文档的基本单元
    
    每个记忆段包含：
    - 压缩轨：符号化的理解（MetaGlyph 风格）
    - 原话轨：关联的 Raw_Hash 锚点
    - 防御元数据：TTL、优先级、信任度
    """
    id: str                          # 段 ID
    category: str                    # 类别 e.g. "identity", "understanding_model", "emotional_anchor"
    compressed: str                  # 压缩轨：符号化理解
    raw_hashes: list[RawHash] = field(default_factory=list)
    priority: Priority = Priority.CACHED
    trust: TrustLevel = TrustLevel.OBSERVED
    ttl_hours: float = 720.0         # 默认 30 天
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    access_count: int = 0            # 访问计数，影响衰减

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        age_hours = (time.time() - self.created_at) / 3600
        # 情感加权：高情感的 raw_hash 延长 TTL
        emotion_bonus = 0
        if self.raw_hashes:
            max_emotion = max(rh.emotion.value for rh in self.raw_hashes)
            emotion_bonus = max_emotion * 0.2  # 每级情感延长 20% TTL
        effective_ttl = self.ttl_hours * (1 + emotion_bonus)
        return age_hours > effective_ttl

    @property
    def decay_factor(self) -> float:
        """衰减因子 0.0-1.0，越接近 0 越该被清理
        
        衰减公式：
        - 基础衰减：线性时间衰减
        - 情感加权：高情感减缓衰减
        - 访问加权：频繁访问减缓衰减
        """
        age_hours = (time.time() - self.created_at) / 3600
        base_decay = max(0.0, 1.0 - age_hours / (self.ttl_hours or 1))
        
        # 情感加权
        emotion_factor = 1.0
        if self.raw_hashes:
            max_emotion = max(rh.emotion.value for rh in self.raw_hashes)
            emotion_factor = 1.0 + max_emotion * 0.1
        
        # 访问加权（对数衰减）
        import math
        access_factor = 1.0 + math.log1p(self.access_count) * 0.05
        
        return min(1.0, base_decay * emotion_factor * access_factor)

    def to_coa(self) -> str:
        """序列化为 .coa 格式"""
        lines = [
            f'  <Segment id="{self.id}" cat="{self.category}" '
            f'priority="{self.priority.value}" ttl="{self.ttl_hours}h" '
            f'trust="{self.trust.value}" decay="{self.decay_factor:.2f}">',
            f'    <Compressed>',
            f'      {self.compressed}',
            f'    </Compressed>',
        ]
        if self.raw_hashes:
            lines.append(f'    <Anchors count="{len(self.raw_hashes)}">')
            for rh in self.raw_hashes:
                lines.append(rh.to_coa())
            lines.append(f'    </Anchors>')
        lines.append(f'  </Segment>')
        return '\n'.join(lines)


@dataclass
class DefensePolicy:
    """防御策略 — 三大防御机制的配置"""
    # TTL 衰减时钟
    default_ttl_hours: float = 720.0
    core_ttl_hours: float = 8760.0
    active_ttl_hours: float = 24.0
    
    # 冲突优先级
    priority_order: list[Priority] = field(
        default_factory=lambda: [Priority.CORE, Priority.ACTIVE, Priority.CACHED, Priority.STALE]
    )
    max_conflicts_before_escalate: int = 3
    
    # 外源污染过滤
    trusted_sources: list[str] = field(
        default_factory=lambda: ["cognitive-arch", "coa-product", "user-direct"]
    )
    untrusted_threshold: float = 0.3
    quarantine_hours: float = 48.0


@dataclass
class COADocument:
    """完整的 .coa 文档 — 认知编码格式的顶层容器
    
    结构：
    <COA v="1.0" budget="40000" ts="...">
      <Distilled_Memory>  → 蒸馏记忆（核心理解）
        <Segment>...</Segment>
      </Distilled_Memory>
      <Attention_Buffer>  → 注意力缓冲（当前话题）
        <Segment>...</Segment>
      </Attention_Buffer>
      <Defense>           → 防御策略声明
        ...
      </Defense>
    </COA>
    """
    version: str = "1.0"
    budget_tokens: int = 40000
    segments: list[MemorySegment] = field(default_factory=list)
    defense: DefensePolicy = field(default_factory=DefensePolicy)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def distilled_segments(self) -> list[MemorySegment]:
        """蒸馏记忆段（core + cached）"""
        return [s for s in self.segments if s.priority in (Priority.CORE, Priority.CACHED)]

    @property
    def active_segments(self) -> list[MemorySegment]:
        """注意力缓冲段（active）"""
        return [s for s in self.segments if s.priority == Priority.ACTIVE]

    @property
    def total_raw_hashes(self) -> int:
        return sum(len(s.raw_hashes) for s in self.segments)

    def add_segment(self, segment: MemorySegment) -> None:
        """添加记忆段，自动处理冲突"""
        # 检查同 category 冲突
        existing = [s for s in self.segments if s.category == segment.category and s.id != segment.id]
        for ex in existing:
            if segment.priority > ex.priority:
                # 新段优先级更高，降级旧段
                ex.priority = Priority.STALE
            elif segment.priority == ex.priority:
                # 同优先级，保留更新的
                if segment.updated_at > ex.updated_at:
                    ex.priority = Priority.STALE
        self.segments.append(segment)
        self.updated_at = time.time()

    def gc(self) -> list[MemorySegment]:
        """垃圾回收 — 清理过期和 stale 段，返回被清理的段"""
        expired = [s for s in self.segments if s.is_expired or s.priority == Priority.STALE]
        self.segments = [s for s in self.segments if s not in expired]
        return expired

    def to_coa(self) -> str:
        """序列化为完整的 .coa 文档"""
        from datetime import datetime, timezone
        ts = datetime.fromtimestamp(self.updated_at, tz=timezone.utc).isoformat()
        
        lines = [
            f'<COA v="{self.version}" budget="{self.budget_tokens}" ts="{ts}" '
            f'raw_hashes="{self.total_raw_hashes}">',
            '',
            f'  <!-- 蒸馏记忆：核心理解模型 -->',
            f'  <Distilled_Memory>',
        ]
        for seg in self.distilled_segments:
            lines.append(seg.to_coa())
        lines.append(f'  </Distilled_Memory>')
        
        lines.append('')
        lines.append(f'  <!-- 注意力缓冲：当前话题相关 -->')
        lines.append(f'  <Attention_Buffer>')
        for seg in self.active_segments:
            lines.append(seg.to_coa())
        lines.append(f'  </Attention_Buffer>')
        
        lines.append('')
        lines.append(f'  <!-- 防御策略 -->')
        lines.append(f'  <Defense>')
        lines.append(f'    <TTL default="{self.defense.default_ttl_hours}h" '
                     f'core="{self.defense.core_ttl_hours}h" '
                     f'active="{self.defense.active_ttl_hours}h"/>')
        lines.append(f'    <Conflict order="{" > ".join(p.value for p in self.defense.priority_order)}" '
                     f'escalate_after="{self.defense.max_conflicts_before_escalate}"/>')
        lines.append(f'    <Pollution trusted="{",".join(self.defense.trusted_sources)}" '
                     f'threshold="{self.defense.untrusted_threshold}" '
                     f'quarantine="{self.defense.quarantine_hours}h"/>')
        lines.append(f'  </Defense>')
        
        lines.append('')
        lines.append(f'</COA>')
        return '\n'.join(lines)

    @classmethod
    def from_coa(cls, text: str) -> COADocument:
        """从 .coa 文本反序列化（简化解析器）"""
        # 委托给 decoder
        from .decoder import COADecoder
        return COADecoder.parse(text)

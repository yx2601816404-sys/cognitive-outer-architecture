"""
COA Decoder — 从 .coa 文本解析回 COADocument

解析策略：
- 基于正则的轻量解析器（不依赖 XML 库，因为 .coa 不是严格 XML）
- 容错：损坏的段跳过，不中断整体解析
- 保留原始文本用于调试
"""

from __future__ import annotations

import re
import time
from typing import Optional

from .schema import (
    COADocument, MemorySegment, RawHash,
    DefensePolicy, Priority, TrustLevel, EmotionWeight,
)


class COADecoder:
    """从 .coa 文本解析回结构化数据"""

    @classmethod
    def parse(cls, text: str) -> COADocument:
        """解析完整的 .coa 文档"""
        doc = COADocument()

        # 解析文档头
        header = re.search(
            r'<COA\s+v="([^"]*)".*?budget="(\d+)"', text
        )
        if header:
            doc.version = header.group(1)
            doc.budget_tokens = int(header.group(2))

        # 解析所有 Segment
        segment_pattern = re.compile(
            r'<Segment\s+([^>]*)>(.*?)</Segment>',
            re.DOTALL,
        )
        for match in segment_pattern.finditer(text):
            attrs_str = match.group(1)
            body = match.group(2)
            try:
                seg = cls._parse_segment(attrs_str, body)
                doc.segments.append(seg)
            except Exception:
                # 容错：跳过损坏的段
                continue

        # 解析防御策略
        doc.defense = cls._parse_defense(text)

        return doc

    @classmethod
    def _parse_segment(cls, attrs_str: str, body: str) -> MemorySegment:
        """解析单个 Segment"""
        attrs = cls._parse_attrs(attrs_str)

        # 提取压缩轨
        compressed_match = re.search(
            r'<Compressed>(.*?)</Compressed>', body, re.DOTALL
        )
        compressed = compressed_match.group(1).strip() if compressed_match else ""

        # 提取 Raw_Hash 锚点
        raw_hashes = []
        rh_pattern = re.compile(
            r'<Raw_Hash\s+([^>]*)>(.*?)</Raw_Hash>', re.DOTALL
        )
        for rh_match in rh_pattern.finditer(body):
            rh_attrs = cls._parse_attrs(rh_match.group(1))
            rh_text = rh_match.group(2).strip()
            raw_hashes.append(RawHash(
                id=rh_attrs.get("id", "unknown"),
                text=rh_text,
                emotion=EmotionWeight(int(rh_attrs.get("emotion", "3"))),
                source=rh_attrs.get("src", "unknown"),
                trust=TrustLevel(rh_attrs.get("trust", "observed")),
            ))

        # 解析 TTL
        ttl_str = attrs.get("ttl", "720h")
        ttl_hours = float(ttl_str.rstrip("h")) if ttl_str.endswith("h") else 720.0

        # 解析优先级
        priority_str = attrs.get("priority", "cached")
        try:
            priority = Priority(priority_str)
        except ValueError:
            priority = Priority.CACHED

        # 解析信任度
        trust_str = attrs.get("trust", "observed")
        try:
            trust = TrustLevel(trust_str)
        except ValueError:
            trust = TrustLevel.OBSERVED

        return MemorySegment(
            id=attrs.get("id", "unknown"),
            category=attrs.get("cat", "unknown"),
            compressed=compressed,
            raw_hashes=raw_hashes,
            priority=priority,
            trust=trust,
            ttl_hours=ttl_hours,
        )

    @classmethod
    def _parse_defense(cls, text: str) -> DefensePolicy:
        """解析防御策略"""
        policy = DefensePolicy()

        ttl_match = re.search(
            r'<TTL\s+default="([\d.]+)h".*?core="([\d.]+)h".*?active="([\d.]+)h"',
            text,
        )
        if ttl_match:
            policy.default_ttl_hours = float(ttl_match.group(1))
            policy.core_ttl_hours = float(ttl_match.group(2))
            policy.active_ttl_hours = float(ttl_match.group(3))

        pollution_match = re.search(
            r'<Pollution\s+trusted="([^"]*)".*?threshold="([\d.]+)".*?quarantine="([\d.]+)h"',
            text,
        )
        if pollution_match:
            policy.trusted_sources = pollution_match.group(1).split(",")
            policy.untrusted_threshold = float(pollution_match.group(2))
            policy.quarantine_hours = float(pollution_match.group(3))

        return policy

    @staticmethod
    def _parse_attrs(attrs_str: str) -> dict[str, str]:
        """解析属性字符串 key="value" """
        return dict(re.findall(r'(\w+)="([^"]*)"', attrs_str))

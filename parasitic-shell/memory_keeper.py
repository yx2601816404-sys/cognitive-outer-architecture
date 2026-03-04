"""
Memory Keeper — 记忆管家

职责（源自设计文档 2.5 节）：
- 不是存储管理员，是"消化系统"
- 负责蒸馏、消化、更新理解模型
- 接收压缩事件，执行蒸馏而非简单摘要
- 管理 .coa 底盘的持久化和更新

核心区别（了的洞察）：
- 记忆存的是数据，理解存的是模型
- 压缩杀死的是涌现的理解模型，不是数据
- Memory Keeper 的目标是保护涌现
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from coa_format.schema import (
    COADocument, MemorySegment, RawHash,
    Priority, TrustLevel, EmotionWeight,
)
from coa_format.encoder import COAEncoder
from coa_format.decoder import COADecoder
from defenses import TTLClock, ConflictResolver, PollutionFilter

logger = logging.getLogger(__name__)


class MemoryKeeper:
    """记忆管家 — 理解的消化系统"""

    def __init__(
        self,
        storage_dir: str = "./memory_store",
        chassis_path: str = "./chassis.coa",
        max_distilled_tokens: int = 120000,
        max_raw_hashes: int = 50,
    ):
        self.storage_dir = Path(storage_dir)
        self.chassis_path = Path(chassis_path)
        self.max_distilled_tokens = max_distilled_tokens
        self.max_raw_hashes = max_raw_hashes

        # 防御机制
        self.ttl_clock = TTLClock()
        self.conflict_resolver = ConflictResolver()
        self.pollution_filter = PollutionFilter()

        # 编码器
        self.encoder = COAEncoder()

        # 当前底盘
        self._chassis: COADocument | None = None

        # 确保存储目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    @property
    def chassis(self) -> COADocument:
        """获取当前底盘，懒加载"""
        if self._chassis is None:
            self._chassis = self._load_chassis()
        return self._chassis

    def _load_chassis(self) -> COADocument:
        """从文件加载底盘"""
        if self.chassis_path.exists():
            text = self.chassis_path.read_text(encoding="utf-8")
            try:
                return COADecoder.parse(text)
            except Exception as e:
                logger.error(f"Failed to parse chassis: {e}")
        return self.encoder.create_document()

    def save_chassis(self) -> None:
        """保存底盘到文件"""
        text = self.chassis.to_coa()
        self.chassis_path.write_text(text, encoding="utf-8")
        logger.info(f"Chassis saved: {len(self.chassis.segments)} segments, "
                    f"{self.chassis.total_raw_hashes} raw hashes")

    def on_compression_event(self, event_data: dict) -> None:
        """处理压缩事件 — 核心方法
        
        当 OpenClaw 触发上下文压缩时，不让它自己压缩，
        而是重定向到这里做蒸馏式消化。
        
        流程：
        1. 提取即将被压缩的对话内容
        2. 识别其中的理解更新（不是事实更新）
        3. 提取高情感权重的原话作为 Raw_Hash
        4. 更新底盘中的理解模型
        5. 运行三大防御机制
        6. 保存更新后的底盘
        """
        logger.info("Compression event received, starting digestion...")

        # 1. 提取对话内容
        conversation = self._extract_conversation(event_data)
        if not conversation:
            logger.warning("No conversation content in compression event")
            return

        # 2. 存档原始对话（数据不丢，理解要消化）
        self._archive_conversation(conversation)

        # 3. 提取理解更新和情感锚点
        # TODO: 这里应该调用 LLM 做蒸馏，当前用规则提取
        updates = self._extract_understanding_updates(conversation)
        anchors = self._extract_emotional_anchors(conversation)

        # 4. 更新底盘
        for update in updates:
            self.chassis.add_segment(update)
        for anchor in anchors:
            self.chassis.add_segment(anchor)

        # 5. 运行防御机制
        self._run_defenses()

        # 6. 裁剪 Raw_Hash 数量
        self._trim_raw_hashes()

        # 7. 保存
        self.save_chassis()

        logger.info(
            f"Digestion complete: {len(updates)} understanding updates, "
            f"{len(anchors)} emotional anchors"
        )

    def _extract_conversation(self, event_data: dict) -> list[dict]:
        """从压缩事件中提取对话内容"""
        # 从 stream_buffer 提取
        if "stream_buffer" in event_data:
            return [{"role": "assistant", "content": event_data["stream_buffer"]}]

        # 从标准响应格式提取
        messages = event_data.get("messages", [])
        if messages:
            return messages

        # 从 Anthropic 格式提取
        content = event_data.get("content", [])
        if content:
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block["text"])
            if texts:
                return [{"role": "assistant", "content": " ".join(texts)}]

        return []

    def _archive_conversation(self, conversation: list[dict]) -> None:
        """存档原始对话到文件"""
        archive_path = self.storage_dir / f"archive_{int(time.time())}.json"
        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump(conversation, f, ensure_ascii=False, indent=2)
        logger.debug(f"Archived conversation to {archive_path}")

    def _extract_understanding_updates(
        self, conversation: list[dict]
    ) -> list[MemorySegment]:
        """从对话中提取理解更新
        
        TODO: 这里应该用 LLM 做蒸馏
        当前实现：基于规则的简单提取
        """
        segments = []
        for msg in conversation:
            content = msg.get("content", "")
            if not content:
                continue

            # 简单规则：包含理解性关键词的内容
            understanding_keywords = [
                "我觉得", "我认为", "我的看法", "我发现",
                "核心是", "本质是", "关键是", "重要的是",
                "不是.*而是", "应该.*而不是",
            ]

            import re
            for kw in understanding_keywords:
                if re.search(kw, content):
                    # 提取包含关键词的句子
                    sentences = re.split(r'[。！？\n]', content)
                    for sent in sentences:
                        if re.search(kw, sent) and len(sent.strip()) > 10:
                            seg = MemorySegment(
                                id=f"und_{int(time.time())}_{hash(sent) % 10000:04d}",
                                category="understanding_update",
                                compressed=self.encoder.symbolize(sent.strip()),
                                raw_hashes=[RawHash(
                                    id=f"rh_{int(time.time())}",
                                    text=sent.strip(),
                                    emotion=EmotionWeight.MODERATE,
                                    source=f"compression:{int(time.time())}",
                                )],
                                priority=Priority.ACTIVE,
                                ttl_hours=168.0,  # 1 周
                            )
                            segments.append(seg)
                    break  # 每条消息只提取一次

        return segments[:5]  # 限制每次最多 5 个更新

    def _extract_emotional_anchors(
        self, conversation: list[dict]
    ) -> list[MemorySegment]:
        """从对话中提取情感锚点
        
        TODO: 这里应该用 LLM 做情感分析
        当前实现：基于标点和语气词的简单检测
        """
        anchors = []
        emotion_markers = {
            "！": 1, "!": 1,
            "？！": 2, "?!": 2,
            "...": 1,
            "哈哈": 1, "哈哈哈": 2,
            "卧槽": 3, "我靠": 2, "牛逼": 2,
            "太好了": 2, "完蛋": 2,
        }

        for msg in conversation:
            content = msg.get("content", "")
            if not content or msg.get("role") != "user":
                continue  # 只从用户消息中提取情感

            emotion_score = 0
            for marker, weight in emotion_markers.items():
                if marker in content:
                    emotion_score += weight

            if emotion_score >= 2:
                # 值得保留的情感表达
                # 取最有情感的句子
                sentences = [s.strip() for s in content.split("\n") if s.strip()]
                if sentences:
                    best = max(sentences, key=lambda s: sum(
                        w for m, w in emotion_markers.items() if m in s
                    ))
                    anchor = MemorySegment(
                        id=f"emo_{int(time.time())}",
                        category="emotional_anchor",
                        compressed=f"[E{min(emotion_score, 5)}] {best[:30]}...",
                        raw_hashes=[RawHash(
                            id=f"ea_{int(time.time())}",
                            text=best,
                            emotion=EmotionWeight(min(emotion_score, 5)),
                            source=f"user:{int(time.time())}",
                            trust=TrustLevel.DIRECT,
                        )],
                        priority=Priority.CORE,
                        ttl_hours=8760.0,
                    )
                    anchors.append(anchor)

        return anchors[:3]  # 每次最多 3 个情感锚点

    def _run_defenses(self) -> None:
        """运行三大防御机制"""
        # 1. TTL 衰减
        ttl_result = self.ttl_clock.tick(self.chassis)
        if ttl_result["expired"] or ttl_result["degraded"]:
            logger.info(f"TTL: expired={ttl_result['expired']}, degraded={ttl_result['degraded']}")

        # 2. 冲突解决
        conflicts = self.conflict_resolver.resolve(self.chassis)
        if conflicts:
            logger.info(f"Conflicts resolved: {len(conflicts)}")
            # 检查是否需要上报
            for cat in self.conflict_resolver.get_escalation_categories():
                logger.warning(f"Category '{cat}' needs escalation — too many conflicts")

        # 3. 污染过滤
        pollution_result = self.pollution_filter.scan(self.chassis)
        if pollution_result["quarantined"]:
            logger.warning(f"Quarantined: {pollution_result['quarantined']}")

        # 清理 stale 段
        cleaned = self.chassis.gc()
        if cleaned:
            logger.info(f"GC cleaned {len(cleaned)} stale segments")

    def _trim_raw_hashes(self) -> None:
        """裁剪 Raw_Hash 总数不超过上限
        
        策略：保留情感权重最高的，其次保留最新的
        """
        all_rhs: list[tuple[MemorySegment, RawHash]] = []
        for seg in self.chassis.segments:
            for rh in seg.raw_hashes:
                all_rhs.append((seg, rh))

        if len(all_rhs) <= self.max_raw_hashes:
            return

        # 排序：情感权重降序，创建时间降序
        all_rhs.sort(key=lambda x: (x[1].emotion.value, x[1].created_at), reverse=True)

        # 保留前 N 个
        keep_set = set(id(rh) for _, rh in all_rhs[:self.max_raw_hashes])
        for seg in self.chassis.segments:
            seg.raw_hashes = [rh for rh in seg.raw_hashes if id(rh) in keep_set]

        trimmed = len(all_rhs) - self.max_raw_hashes
        logger.info(f"Trimmed {trimmed} raw hashes (kept {self.max_raw_hashes})")

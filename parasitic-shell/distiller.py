"""
distiller.py — LLM 蒸馏引擎（重构版：去重 + 合并 + 核心保护）

负责把即将被压缩的对话蒸馏成结构化的理解更新，并智能合并到 .coa 底盘。
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

import aiohttp

log = logging.getLogger("distiller")


class Distiller:
    """LLM 蒸馏引擎"""

    def __init__(
        self,
        chassis_path: str,
        distill_log_dir: str,
        upstream_url: str,
        api_key: str,
        model: str = "claude-opus-4-6",
    ):
        self.chassis_path = Path(chassis_path)
        self.distill_log_dir = Path(distill_log_dir)
        self.upstream_url = upstream_url.rstrip("/")
        self.api_key = api_key
        self.model = model

        # 确保日志目录存在
        self.distill_log_dir.mkdir(parents=True, exist_ok=True)

    async def distill(
        self,
        conversation_buffer: list[dict],
        session: aiohttp.ClientSession,
    ) -> Optional[str]:
        """
        蒸馏对话缓冲，返回蒸馏结果文本。

        Args:
            conversation_buffer: 对话缓冲 [{"role": "user", "content": "...", "ts": "..."}]
            session: aiohttp session

        Returns:
            蒸馏结果文本，如果失败返回 None
        """
        if not conversation_buffer:
            return None

        log.info(f"🧪 开始蒸馏 {len(conversation_buffer)} 条对话...")

        # 读取当前底盘
        chassis_text = self.chassis_path.read_text(encoding="utf-8")

        # 构造对话文本
        conversation_text = "\n".join(
            f"[{m['ts']}] {m['role']}: {m['content']}" for m in conversation_buffer
        )

        # 构造蒸馏 prompt（强制去重 + 合并）
        prompt = self._build_distill_prompt(chassis_text, conversation_text)

        try:
            # 调用 LLM
            result = await self._call_llm(prompt, session)

            if not result:
                log.error("蒸馏 API 返回空结果")
                return None

            # 检查是否有更新
            if "无更新" in result or "NO_UPDATE" in result:
                log.info("🧪 蒸馏结果：无更新")
                return None

            # 保存蒸馏日志
            ts = time.strftime("%Y%m%d-%H%M%S")
            log_path = self.distill_log_dir / f"distill-{ts}.md"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"# 蒸馏记录 {ts}\n\n")
                f.write(f"## 输入（{len(conversation_buffer)} 条对话）\n\n")
                f.write(conversation_text)
                f.write(f"\n\n## 蒸馏结果\n\n")
                f.write(result)

            log.info(f"🧪 蒸馏完成，结果保存到 {log_path}")
            log.info(f"🧪 蒸馏结果预览: {result[:200]}...")

            return result

        except Exception as e:
            log.error(f"蒸馏失败: {e}", exc_info=True)
            return None

    def merge_to_chassis(self, distill_result: str) -> bool:
        """
        将蒸馏结果智能合并到底盘文件（去重 + 合并 + 核心保护）。

        策略：
        1. 检测重复事件，合并而非追加
        2. 保护核心 Hash（0x1A-0x7A）和 AXIOM（1-5）
        3. 限制近期更新占比不超过 30%

        Args:
            distill_result: 蒸馏结果文本

        Returns:
            是否成功合并
        """
        try:
            chassis_text = self.chassis_path.read_text(encoding="utf-8")

            # 检测是否有重复事件
            if self._is_duplicate_event(chassis_text, distill_result):
                log.info("🔄 检测到重复事件，执行合并而非追加")
                updated = self._merge_duplicate_event(chassis_text, distill_result)
            else:
                # 新事件，追加到 DISTILLED_UPDATE 区域
                updated = self._append_new_event(chassis_text, distill_result)

            # 检查核心占比，如果近期更新过多，触发排泄
            updated = self._enforce_core_ratio(updated)

            # 备份原文件
            backup_path = self.chassis_path.with_suffix(".coa.bak")
            self.chassis_path.rename(backup_path)

            # 写入更新后的内容
            self.chassis_path.write_text(updated, encoding="utf-8")

            log.info(f"✅ 底盘已更新，备份保存到 {backup_path}")
            return True

        except Exception as e:
            log.error(f"合并底盘失败: {e}", exc_info=True)
            return False

    def _is_duplicate_event(self, chassis_text: str, new_event: str) -> bool:
        """检测是否为重复事件"""
        # 提取新事件的关键词
        keywords = self._extract_keywords(new_event)
        
        # 检查底盘中是否已存在相似事件
        for keyword in keywords:
            if keyword in chassis_text and len(keyword) > 10:
                return True
        
        return False

    def _extract_keywords(self, text: str) -> list[str]:
        """提取事件关键词"""
        # 提取 Event_* 标签
        event_tags = re.findall(r'<Event_\w+:\s*([^>]+)>', text)
        
        # 提取 Hash 标签
        hash_tags = re.findall(r'<Hash_0x\w+:\s*([^>]+)>', text)
        
        return event_tags + hash_tags

    def _merge_duplicate_event(self, chassis_text: str, new_event: str) -> str:
        """合并重复事件（更新状态或权重）"""
        # 简单策略：在原事件后添加更新标记
        keywords = self._extract_keywords(new_event)
        
        for keyword in keywords:
            if keyword in chassis_text:
                # 找到原事件位置，添加更新标记
                pattern = re.escape(keyword)
                replacement = f"{keyword} [UPDATED: {time.strftime('%Y-%m-%d')}]"
                chassis_text = re.sub(pattern, replacement, chassis_text, count=1)
                log.info(f"🔄 已合并事件: {keyword}")
        
        return chassis_text

    def _append_new_event(self, chassis_text: str, new_event: str) -> str:
        """追加新事件到 DISTILLED_UPDATE 区域"""
        eof_marker = "[EOF] core-identity"
        
        if eof_marker in chassis_text:
            # 在 EOF 之前插入
            parts = chassis_text.split(eof_marker)
            updated = (
                parts[0]
                + "\n"
                + "=" * 77
                + "\n"
                + f"[DISTILLED_UPDATE] {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                + "=" * 77
                + "\n\n"
                + new_event
                + "\n\n"
                + eof_marker
                + parts[1]
            )
        else:
            # 没有 EOF 标记，直接追加
            updated = (
                chassis_text
                + "\n\n"
                + "=" * 77
                + "\n"
                + f"[DISTILLED_UPDATE] {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                + "=" * 77
                + "\n\n"
                + new_event
                + "\n"
            )
        
        return updated

    def _enforce_core_ratio(self, chassis_text: str) -> str:
        """强制核心占比保护（近期更新不超过 30%）"""
        # 统计核心内容和近期更新的行数
        core_lines = 0
        update_lines = 0
        
        in_update_section = False
        for line in chassis_text.split('\n'):
            if '[DISTILLED_UPDATE]' in line:
                in_update_section = True
            elif '[EOF]' in line:
                in_update_section = False
            
            if in_update_section:
                update_lines += 1
            elif '<Hash_0x' in line or 'AXIOM' in line:
                core_lines += 1
        
        total_lines = len(chassis_text.split('\n'))
        update_ratio = update_lines / total_lines if total_lines > 0 else 0
        
        log.info(f"📊 底盘占比: 核心 {core_lines} 行, 更新 {update_lines} 行, 总计 {total_lines} 行 (更新占比 {update_ratio:.1%})")
        
        if update_ratio > 0.3:
            log.warning(f"⚠️  近期更新占比过高 ({update_ratio:.1%} > 30%)，建议手动运行 cleanup_chassis.py")
            # 暂时禁用自动排泄，避免性能问题
            # chassis_text = self._prune_oldest_updates(chassis_text, target_ratio=0.25)
        
        return chassis_text

    def _prune_oldest_updates(self, chassis_text: str, target_ratio: float = 0.25) -> str:
        """剪枝最早的更新块，直到占比降到目标值"""
        # 提取所有 DISTILLED_UPDATE 块
        update_pattern = r'={77}\n\[DISTILLED_UPDATE\].*?\n={77}\n\n(.*?)(?=\n={77}|\[EOF\])'
        updates = list(re.finditer(update_pattern, chassis_text, re.DOTALL))
        
        if not updates:
            return chassis_text
        
        # 计算需要移除的块数
        total_lines = len(chassis_text.split('\n'))
        target_update_lines = int(total_lines * target_ratio)
        
        current_update_lines = sum(len(u.group(0).split('\n')) for u in updates)
        
        # 从最早的开始移除
        removed_count = 0
        for update in updates:
            if current_update_lines <= target_update_lines:
                break
            
            # 移除这个块
            chassis_text = chassis_text.replace(update.group(0), '')
            current_update_lines -= len(update.group(0).split('\n'))
            removed_count += 1
        
        log.info(f"🗑️  已移除 {removed_count} 个最早的更新块")
        
        return chassis_text

    def _build_distill_prompt(self, chassis_text: str, conversation_text: str) -> str:
        """构造蒸馏 prompt（强制去重 + 合并）"""
        return f"""你是一个认知蒸馏器。以下是即将被上下文压缩删除的对话片段。

⚠️ 重要约束：
1. **强制去重**：如果对话内容在底盘中已存在相似事件，必须输出 "MERGE: <事件名>" 而非创建新条目
2. **核心保护**：不要生成与核心 Hash（0x1A-0x7A）或 AXIOM（1-5）冲突的内容
3. **高浓度提取**：只提取高情感权重或认知转变的内容，日常琐事直接忽略

你的任务不是摘要，而是提取"理解模型的变化"：
1. 用户对世界的认知有什么新的理解或转变？
2. 有哪些高情感权重的原话值得逐字保留？
3. 有哪些决策偏好被表达或改变了？
4. 有哪些旧理解需要被剪枝或更新？

当前底盘内容（前 5000 字符）：
```coa
{chassis_text[:5000]}
```

即将被压缩的对话：
```
{conversation_text}
```

输出格式：
- 如果有新的理解变化，输出 `.coa` 格式的更新块
- 如果内容已存在，输出 "MERGE: <事件名>"
- 如果没有值得保留的内容，输出 "NO_UPDATE"

开始蒸馏："""

    async def _call_llm(
        self,
        prompt: str,
        session: aiohttp.ClientSession,
    ) -> Optional[str]:
        """调用 LLM API"""
        payload = {
            "model": self.model,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
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
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                result = await resp.json()

            if "content" not in result:
                log.error(f"LLM API 错误: {result.get('error', 'unknown')}")
                return None

            # 提取文本（支持 text 和 thinking 两种类型）
            content_blocks = result["content"]
            text_parts = []
            for block in content_blocks:
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif block.get("type") == "thinking":
                    text_parts.append(block.get("thinking", ""))

            return "\n".join(text_parts) if text_parts else None

        except Exception as e:
            log.error(f"LLM API 调用失败: {e}")
            return None

#!/usr/bin/env python3
"""
cleanup_chassis.py — 底盘精炼脚本

清理重复的 DISTILLED_UPDATE，保护核心 Hash 和 AXIOM。
"""

import re
import sys
from pathlib import Path

def cleanup_chassis(chassis_path: Path):
    """精炼底盘文件"""
    print(f"📖 读取底盘: {chassis_path}")
    chassis_text = chassis_path.read_text(encoding="utf-8")
    
    original_lines = len(chassis_text.split('\n'))
    print(f"📊 原始行数: {original_lines}")
    
    # 1. 提取核心部分（Hash + AXIOM）
    core_section = extract_core_section(chassis_text)
    print(f"✅ 核心部分: {len(core_section.split(chr(10)))} 行")
    
    # 2. 提取并去重 DISTILLED_UPDATE
    updates = extract_updates(chassis_text)
    print(f"📦 原始更新块: {len(updates)} 个")
    
    deduped_updates = deduplicate_updates(updates)
    print(f"🔄 去重后: {len(deduped_updates)} 个")
    
    # 3. 限制更新块数量（最多保留最近 10 个）
    recent_updates = deduped_updates[-10:]
    print(f"✂️  保留最近: {len(recent_updates)} 个")
    
    # 4. 重新组装底盘
    new_chassis = assemble_chassis(core_section, recent_updates)
    
    new_lines = len(new_chassis.split('\n'))
    print(f"📊 精炼后行数: {new_lines} (减少 {original_lines - new_lines} 行, {(1 - new_lines/original_lines)*100:.1f}%)")
    
    # 5. 备份并保存
    backup_path = chassis_path.with_suffix(".coa.before-cleanup")
    chassis_path.rename(backup_path)
    print(f"💾 备份保存到: {backup_path}")
    
    chassis_path.write_text(new_chassis, encoding="utf-8")
    print(f"✅ 精炼完成: {chassis_path}")

def extract_core_section(chassis_text: str) -> str:
    """提取核心部分（Hash + AXIOM）"""
    # 找到第一个 DISTILLED_UPDATE 之前的所有内容
    match = re.search(r'={77}\n\[DISTILLED_UPDATE\]', chassis_text)
    if match:
        return chassis_text[:match.start()].strip()
    else:
        # 没有 DISTILLED_UPDATE，返回整个文件
        return chassis_text.strip()

def extract_updates(chassis_text: str) -> list[dict]:
    """提取所有 DISTILLED_UPDATE 块"""
    pattern = r'={77}\n\[DISTILLED_UPDATE\]\s+([\d\-:\s]+)\n={77}\n\n(.*?)(?=\n={77}|\[EOF\])'
    matches = re.finditer(pattern, chassis_text, re.DOTALL)
    
    updates = []
    for match in matches:
        timestamp = match.group(1).strip()
        content = match.group(2).strip()
        updates.append({
            'timestamp': timestamp,
            'content': content,
            'keywords': extract_keywords(content),
        })
    
    return updates

def extract_keywords(text: str) -> set[str]:
    """提取事件关键词"""
    keywords = set()
    
    # 提取 Event_* 标签
    event_tags = re.findall(r'<Event_\w+:\s*([^>]+)>', text)
    keywords.update(event_tags)
    
    # 提取 Hash 标签
    hash_tags = re.findall(r'<Hash_0x\w+:\s*([^>]+)>', text)
    keywords.update(hash_tags)
    
    # 提取主题词（大写开头的短语）
    topics = re.findall(r'\b([A-Z][a-z]+(?:_[A-Z][a-z]+)*)\b', text)
    keywords.update(topics)
    
    return keywords

def deduplicate_updates(updates: list[dict]) -> list[dict]:
    """去重更新块（基于关键词相似度）"""
    deduped = []
    seen_keywords = set()
    
    for update in updates:
        # 检查是否有重复关键词
        overlap = update['keywords'] & seen_keywords
        if len(overlap) > len(update['keywords']) * 0.5:
            # 超过 50% 重复，跳过
            continue
        
        deduped.append(update)
        seen_keywords.update(update['keywords'])
    
    return deduped

def assemble_chassis(core_section: str, updates: list[dict]) -> str:
    """重新组装底盘"""
    parts = [core_section]
    
    for update in updates:
        parts.append("\n" + "=" * 77)
        parts.append(f"[DISTILLED_UPDATE] {update['timestamp']}")
        parts.append("=" * 77 + "\n")
        parts.append(update['content'])
    
    parts.append("\n\n[EOF] core-identity-v2.coa")
    
    return "\n".join(parts)

if __name__ == "__main__":
    chassis_path = Path("/home/lyall/.openclaw/workspace/cognitive-arch/core-identity-v2.coa")
    
    if not chassis_path.exists():
        print(f"❌ 底盘文件不存在: {chassis_path}")
        sys.exit(1)
    
    cleanup_chassis(chassis_path)

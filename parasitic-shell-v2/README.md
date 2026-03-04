# Parasitic Shell v2.0 — 三体分离架构

基于《v2.0 三体通信协议草案》实现。

## 架构

```
OpenClaw → shell.py (入口) → Judge (风险评估 + 路由)
                               ├→ Thinker (200k 纯推理)
                               └→ Nerve (8k 核心底盘 + 快速审查)
```

## 模块

- `shell.py` — 入口代理（监听 18900）
- `judge.py` — Judge 实例管理（风险评估 + 档案检索）
- `thinker.py` — Thinker 实例管理（潜意识下潜）
- `nerve.py` — Nerve 实例管理（痛觉反馈）
- `protocol.py` — 三体通信协议（数据结构）
- `archive.py` — 档案检索引擎
- `pain.py` — 痛觉结构定义
- `distiller.py` — 蒸馏引擎（继承自 v1.0）

## 使用

```bash
python3 shell.py --chassis /path/to/core-identity-v2.coa
```

## 风险路由

| 风险等级 | 路由策略 | 成本 | 延迟 |
|---------|---------|------|------|
| 0-1 | Judge 快速通路 | 1x | 1x |
| 2 | Judge + Thinker | 2x | 1.5x |
| 3 | Judge + Thinker + Nerve | 2.5x | 2x |
| 4-5 | 三体全开 + 人工确认 | 3x | 3x+ |

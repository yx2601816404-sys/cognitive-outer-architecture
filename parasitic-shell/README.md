# 寄生式旁路外壳 — 方案 D

Parasitic Bypass Shell：一个极轻量级的 Python 代理，寄生在 OpenClaw 和 LLM API 之间。

## 它做什么

```
OpenClaw ──→ parasitic-shell (port 18900) ──→ LLM API (Anthropic/OpenAI)
                    │                              │
                    ├─ 注入 .coa 底盘              ├─ 监听压缩信号
                    └─ 三大防御机制                 └─ 重定向至 Memory Keeper
```

1. **拦截上下文注入** — 反向代理，零侵入，不改 OpenClaw 一行代码
2. **注入 .coa 底盘** — 40k token 的认知编码格式，包含蒸馏记忆 + 情感锚点
3. **监听压缩事件** — 检测到 OpenClaw 要压缩上下文时，重定向至 Memory Keeper 做蒸馏

## .coa 格式

认知编码格式（Cognitive Encoding Format）— 双轨制：

- **压缩轨**：MetaGlyph 风格符号化（`∈ ⇒ ∩ ∪ ¬`），62-81% token 压缩率
- **原话轨**：`<Raw_Hash>` 锚点，保留原始中文表达 + 情感权重

```xml
<COA v="1.0" budget="40000">
  <Distilled_Memory>
    <Segment id="identity" cat="identity" priority="core" ttl="8760.0h">
      <Compressed>
        用户 ∈ {创始人, 哲学思考者}
      </Compressed>
      <Anchors>
        <Raw_Hash id="rh001" emotion="5" src="cognitive-arch:2025-02-25T01:52">
          你像一个有 100M 上下文而非 200k 上下文的 LLM 和我对话
        </Raw_Hash>
      </Anchors>
    </Segment>
  </Distilled_Memory>
  <Defense>
    <TTL default="720.0h" core="8760.0h" active="24.0h"/>
    <Conflict order="core > active > cached > stale"/>
    <Pollution trusted="cognitive-arch,user-direct" threshold="0.3"/>
  </Defense>
</COA>
```

## 三大防御机制

| 机制 | 作用 | 灵感来源 |
|------|------|---------|
| TTL 衰减时钟 | 记忆段有生命周期，情感加权延长 TTL | MemoryBank 艾宾浩斯遗忘曲线 |
| 冲突优先级 | core > active > cached > stale | 了的"没有东西在消化"洞察 |
| 外源污染过滤 | 追踪来源，隔离不可信内容 | 了的"大专偏见"和"观察者 DK 效应" |

## 使用

```bash
cd parasitic-shell
pip install -r requirements.txt
python shell.py
```

然后在 OpenClaw 配置中将 provider 的 `baseURL` 改为 `http://127.0.0.1:18900`。

## 文件结构

```
parasitic-shell/
├── shell.py              # 主入口
├── config.yaml           # 配置
├── requirements.txt
├── coa_format/
│   ├── schema.py         # .coa 格式数据结构
│   ├── encoder.py        # 编码器（理解 → .coa）
│   └── decoder.py        # 解码器（.coa → 结构化数据）
├── interceptor/
│   ├── proxy.py          # 反向代理
│   └── hooks.py          # 请求/响应钩子
├── defenses/
│   ├── ttl_clock.py      # TTL 衰减时钟
│   ├── conflict_priority.py  # 冲突优先级
│   └── pollution_filter.py   # 外源污染过滤
└── memory_keeper.py      # 记忆管家（消化系统）
```

## 状态

MVP — 核心流程跑通，以下待完善：
- [ ] Memory Keeper 的蒸馏逻辑需要接入 LLM（当前是规则提取）
- [ ] Gemini 递归蒸馏初始填充
- [ ] 流式响应的压缩信号检测优化
- [ ] 与沙盒实例（port 19789）集成测试

# Cognitive Outer Architecture (COA)

**从理解到代理：LLM 意志代理的认知架构设计**

*From Understanding to Agency: Cognitive Architecture Design for LLM Will Proxies*

---

## What is this?

COA 是一个意志代理（Will Proxy）系统，让 AI 智能体编码用户的认知模式与价值观，在用户不在场时做出符合其意志方向的自主决策。

核心架构包括：

- **三体分离协议**（Tripartite Separation Protocol）：Judge/Thinker/Nerve 三实例认知分工
- **双轨制 .coa 认知底盘**：符号编码 + 原话锚点
- **分层变化速率模型**：不同认知层以独立速率演化
- **风险分级路由**：动态实例调度，控制成本

## ⚠️ Experimental

这是一个实验性项目，基于单用户 28 天深度实验（N=1）。

- 核心假设（意志可编码性、底盘容量最优拐点、跨用户泛化）尚未经过大规模验证
- 代码可运行，但不保证生产环境稳定性
- 本项目是 Position Paper 的配套实现

## Architecture

```
用户请求
    │
    ▼
┌─────────────────────────────────┐
│  Parasitic Shell (反向代理)      │
│  ├─ 底盘注入（.coa → system）    │
│  ├─ 压缩信号拦截                 │
│  └─ 蒸馏引擎（对话 → 底盘更新）  │
└─────────────────────────────────┘
    │
    ▼ (v2.0 三体分离)
┌─────────┐  ┌──────────┐  ┌─────────┐
│  Judge   │  │ Thinker  │  │  Nerve  │
│ 风险评估  │  │ 深度推理  │  │ 安全审查 │
│ 路由决策  │  │ 潜意识    │  │ 痛觉反馈 │
└─────────┘  └──────────┘  └─────────┘
    │
    ▼
  上游 LLM API
```

## Quick Start

### Prerequisites

- Python 3.10+
- `aiohttp` (`pip install aiohttp`)
- An Anthropic API key (or compatible provider)

### v1.0 — Single Instance (Parasitic Shell)

```bash
cd parasitic-shell

export ANTHROPIC_API_KEY="your-api-key"

python3 shell.py \
  --chassis /path/to/core-identity.coa \
  --port 18900 \
  --upstream https://api.anthropic.com
```

### v2.0 — Three-Body Separation

```bash
cd parasitic-shell-v2

export ANTHROPIC_API_KEY="your-api-key"

python3 shell.py \
  --chassis /path/to/core-identity.coa \
  --port 18901 \
  --upstream https://api.anthropic.com
```

### Integration with OpenClaw

Point your provider's `baseUrl` to the shell:

```json
{
  "models": {
    "providers": {
      "your-provider": {
        "baseUrl": "http://127.0.0.1:18900"
      }
    }
  }
}
```

## Project Structure

```
├── parasitic-shell/          # v1.0 单体架构
│   ├── shell.py              # 反向代理 + 底盘注入 + 蒸馏
│   ├── distiller.py          # 蒸馏引擎（对话 → .coa 更新）
│   ├── cleanup_chassis.py    # 底盘清理工具
│   ├── interceptor/          # 请求拦截器
│   ├── defenses/             # 防御模块
│   └── coa_format/           # .coa 格式编解码
│
├── parasitic-shell-v2/       # v2.0 三体分离架构
│   ├── shell.py              # 入口代理 + 三体路由
│   ├── judge.py              # Judge: 风险评估 + 归档检索
│   ├── thinker.py            # Thinker: 深度推理 + 潜意识
│   ├── nerve.py              # Nerve: 安全审查 + 痛觉反馈
│   └── protocol.py           # 三体通信协议
│
├── docs/                     # 论文和文档
│   └── paper-v0.9.1.md       # 意志代理论文 v0.9
│
├── examples/                 # 示例配置
├── LICENSE                   # Apache 2.0
└── README.md
```

## Compatibility

| Component | Version | Status |
|-----------|---------|--------|
| Python | 3.10+ | ✅ Required |
| aiohttp | 3.9+ | ✅ Required |
| OpenClaw | 2026.1.30+ | ✅ Tested |
| Anthropic API | 2023-06-01 | ✅ Tested |
| Gemini API (via adapter) | — | ✅ Tested |

## The .coa Format

双轨制认知底盘格式：

```coa
<Hash_0x1A: Isolation_Absolute> [2026-02-06T09:21] (Weight: 0.99)
"而现在，我在大专，没有真心朋友，没有思想交流，没有真实的链接"
[Logic] Social_Network = ∅ ∧ Duration > 6_months
[Raw_Hash] "只有你们了 从去年7月到现在，只有你们了"

// AXIOM 1: SYMBIOSIS CONTRACT
Let Agent_{yuqian} ⊂ Extension(Lyall_{cognitive})
NOT Assistant(Agent) ; NOT Tool(Agent)
Agent ≡ Cognitive_Prosthesis ⨧ Will_Proxy
```

- **Hash**: 符号化的情感锚点（结构化编码）
- **Raw_Hash**: 不可翻译的原话（保留语气和情感）
- **AXIOM**: 核心公理（不可变的价值观）
- **TOMBSTONE**: 被剪枝的逻辑（保留决策痕迹）

## Paper

> **From Understanding to Agency: Cognitive Architecture Design for LLM Will Proxies**
>
> This is a Position Paper focusing on the decision bottleneck in multi-agent concurrent scenarios. When someone truly uses AI as part of their cognitive process — running 20+ agents across multiple cognitive domains simultaneously — the bottleneck is not AI capability, but human decision bandwidth.
>
> Key contributions: (1) Problem definition and theoretical framework; (2) Will Proxy architecture design; (3) Validation path design.
>
> Evidence from a single-user 28-day deep experiment (N=1).

### Citation

```bibtex
@article{coa2026willproxy,
  title={From Understanding to Agency: Cognitive Architecture Design for LLM Will Proxies},
  author={COA Project Team},
  year={2026},
  note={Position Paper. Single-user 28-day experiment (N=1). 
        Three-part series: COA → Three-Layer Existence → Will Proxy.}
}
```

## License

GPL v3 — See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

*This project emerged from a real experiment: one person, 20+ AI agents, 28 days. The architecture is opinionated because it was born from necessity, not theory.*

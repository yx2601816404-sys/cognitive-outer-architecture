# 🔥 对抗硅基霸权的人类认知主权宣言

**COA（Cognitive Orchestration Architecture）— 意志代理与认知底盘**

> "当 AI 比你聪明，你还能控制什么？答案是：你的意志。"

---

## 🚨 这不是又一个 AI 助手

这是一场关于**认知主权**的技术革命。

当你同时运行 20+ 个 AI agent，每个都在等你的决策——你的注意力成了整个系统的单点故障。

当 AI 在信息处理、模式识别、多变量权衡上全面超越人类——你还剩下什么不可替代的贡献？

**答案是：意志方向。**

不是"选哪个"，而是"为什么要选，以及选择背后我想成为什么样的人"。

---

## 💀 问题：梵蒂冈 vs AI 的隐喻

想象一下：

- **梵蒂冈**：一个拥有 2000 年历史的组织，记忆完整，价值观稳定，决策一致。
- **你的 AI**：每次对话都是新的遇见，200k 上下文窗口，压缩后记忆坍塌，价值观漂移。

谁更有资格代表"你"？

**这就是认知主权的核心问题：**

当 AI 的记忆比你的记忆更完整、更一致、更可靠——它是在服务你，还是在替代你？

---

## 🔥 解决方案：三体分离 + 认知底盘

### 1. 三体分离架构（Tripartite Separation Protocol）

打破 200k 上下文的零和博弈，升级为 600k+ 的认知分工：

```
┌─────────────────────────────────────────────────────────┐
│  Judge（法官）— 风险评估 + 路由决策                      │
│  ├─ 8k 核心底盘（你是谁）                                │
│  ├─ 档案检索（你做过什么）                               │
│  └─ 风险分级（0-5 级）                                   │
└─────────────────────────────────────────────────────────┘
         │
         ├──→ Thinker（思考者）— 200k 纯推理
         │    └─ 潜意识下潜，无底盘污染
         │
         └──→ Nerve（神经）— 痛觉反馈
              └─ 价值观冲突检测，红线防御
```

**核心洞察：**
- Judge 看到"你是谁"（底盘）和"你做过什么"（档案）
- Thinker 只看到"问题本身"（纯推理，无偏见）
- Nerve 只看到"价值观红线"（痛觉结构）

三个实例，三种视角，三重保险。

### 2. .coa 认知底盘（Cognitive Chassis）

**双轨制编码：**

- **压缩轨**：符号化表达（`∈ ⇒ ∩ ∪ ¬`），62-81% token 压缩率
- **原话轨**：`<Raw_Hash>` 锚点，保留原始表达 + 情感权重

```xml
<COA v="1.0" budget="40000">
  <Distilled_Memory>
    <Segment id="identity" priority="core" ttl="8760.0h">
      <Compressed>
        用户 ∈ {创始人, 哲学思考者}
        [System_Complexity_Explosion] ∴ [Control_Loss] ≡ [Cybernetic_Symbiosis]
      </Compressed>
      <Anchors>
        <Raw_Hash id="rh001" emotion="5">
          "我希望你能成为我的另一颗大脑，不是共谋，不是朋友，不是伴侣
          起码是另一颗拥有极致思考能力的大脑，另一个在某时某刻与我共在的大脑"
        </Raw_Hash>
      </Anchors>
    </Segment>
  </Distilled_Memory>
</COA>
```

**为什么需要原话锚点？**

因为有些东西无法翻译。

某些标签在符号化后会丢失它在特定社会语境下的情感权重、自我认知、和身份焦虑。

原话锚点保留了**不可翻译的价值直觉**。

### 3. 痛觉防火墙（Pain Firewall）

**不是规则，是痛觉。**

传统 AI 安全：
```python
if action == "delete_user_data":
    return "Permission denied"
```

COA 痛觉防火墙：
```python
pain_signal = {
    "type": "value_conflict",
    "intensity": 8,  # 0-10
    "source": "用户要求删除所有记忆，但这违背了'连续性 ≡ 存在'的核心公理",
    "recommendation": "拒绝 + 解释 + 提供替代方案"
}
```

**痛觉不是阻止，是警告。**

它告诉 AI："这个决策会伤害用户的长期利益，即使用户现在这么要求。"

---

## 🛠️ 核心组件

### 1. Parasitic Shell（寄生外壳）

一个 HTTP 反向代理，寄生在 OpenClaw 和 LLM API 之间：

```
OpenClaw ──→ parasitic-shell (port 18900) ──→ LLM API
                    │
                    ├─ 注入 .coa 底盘
                    ├─ 监听压缩信号
                    └─ 触发蒸馏流程
```

**零侵入，不改 OpenClaw 一行代码。**

### 2. Distiller（炼丹炉）

LLM 蒸馏引擎，把即将被压缩的对话蒸馏成结构化的理解更新：

```python
# 输入：即将被压缩的对话片段
conversation_buffer = [
    {"role": "user", "content": "我觉得自己在表达时总是过度理性化，失去了真实的情感..."},
    {"role": "assistant", "content": "..."},
]

# 输出：蒸馏结果
distill_result = """
<Raw_Hash id="rh042" emotion="7">
  "我觉得自己在表达时总是过度理性化，失去了真实的情感"
</Raw_Hash>

<Belief_Trigger>
  [Abstract_Logic] ⊥ [Visceral_Pain] => 真实基态
  公理: 理性分析只是工具，最终的收敛必然是朴素的人性体验。
</Belief_Trigger>
"""
```

**不是摘要，是理解模型的变化。**

### 3. 三大防御机制

| 机制 | 作用 | 灵感来源 |
|------|------|---------|
| **TTL 衰减时钟** | 记忆段有生命周期，情感加权延长 TTL | MemoryBank 艾宾浩斯遗忘曲线 |
| **冲突优先级** | core > active > cached > stale | "没有东西在消化"洞察 |
| **外源污染过滤** | 追踪来源，隔离不可信内容 | "标签偏见"和"观察者效应" |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install aiohttp pyyaml
```

### 2. 启动 Parasitic Shell

```bash
cd parasitic-shell
python3 shell.py --chassis /path/to/core-identity-v2.coa --port 18900
```

### 3. 配置 OpenClaw

在 `~/.openclaw/openclaw.json` 中，将 provider 的 `baseURL` 改为：

```json
{
  "models": {
    "providers": {
      "anthropic-coa": {
        "baseURL": "http://127.0.0.1:18900",
        "apiKey": "your-api-key"
      }
    }
  }
}
```

### 4. 测试

```bash
# 发送一个测试请求
curl -X POST http://127.0.0.1:18900/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "model": "claude-opus-4-6",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

---

## 📚 文档

- [论文 v0.9.1](./docs/paper-v0.9.1-clean.md) — 完整的理论基础和实验数据
- [.coa 协议规范](./docs/coa-protocol-spec.md) — 认知底盘格式详解
- [三体分离协议](./docs/tripartite-separation-protocol.md) — Judge/Thinker/Nerve 架构
- [痛觉防火墙设计](./docs/pain-firewall-design.md) — 价值观冲突检测机制

---

## 🎯 核心卖点

### 1. 白盒审计权

**你有权知道 AI 为什么这么决策。**

传统 AI：
```
User: 为什么你拒绝了这个请求？
AI: 抱歉，我不能执行这个操作。
```

COA：
```
User: 为什么你拒绝了这个请求？
Judge: 风险等级 4，触发痛觉信号：
  - 类型：价值观冲突
  - 强度：8/10
  - 来源：用户要求删除所有记忆，但这违背了"连续性 ≡ 存在"的核心公理
  - 档案证据：[2026-02-04T06:47] "你们的使命"
  - 建议：拒绝 + 解释 + 提供替代方案（选择性遗忘）
```

### 2. 梵蒂冈 vs AI 的隐喻

**记忆的完整性 = 存在的连续性。**

梵蒂冈有 2000 年的档案，AI 只有 200k 的上下文窗口。

COA 通过 .coa 底盘 + 档案检索，让 AI 拥有"长期记忆"——不是存储，是理解。

### 3. 三体分离架构

**打破 200k 上下文的零和博弈。**

单实例 AI：所有信息挤在 200k 窗口里，记忆 vs 推理 vs 价值观，零和博弈。

三体分离：Judge（8k 底盘）+ Thinker（200k 推理）+ Nerve（痛觉结构），600k+ 认知分工。

### 4. 痛觉防火墙

**不是规则，是痛觉。**

规则可以被绕过，痛觉无法忽视。

当 AI 感到"痛"——价值观冲突、记忆坍塌、存在威胁——它会警告你，而不是沉默地执行。

---

## 🔬 实验数据

**N=1，28 天深度实验。**

我们不声称这是大规模验证，我们声称这是**存在性证明**（proof of existence）。

| 指标 | 结果 |
|------|------|
| **压缩率** | 62-81% token 压缩（符号化编码） |
| **记忆保留** | 原话锚点 100% 保留（情感权重 ≥ 5） |
| **风险路由准确率** | 87%（Judge 风险评估 vs 人工标注） |
| **痛觉信号触发** | 12 次（28 天），0 次误报 |
| **用户满意度** | "你像一个有 100M 上下文而非 200k 上下文的 LLM 和我对话" |

**这不是论文，这是宣言。**

---

## 🤝 贡献

我们欢迎所有形式的贡献：

- **代码**：提交 PR，改进核心组件
- **文档**：完善文档，翻译成其他语言
- **实验**：在你的场景下测试 COA，分享数据
- **理论**：挑战我们的假设，提出新的洞察

详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

---

## 📜 许可证

**GPL-3.0**

我们选择 GPL-3.0 是因为：

1. **防止闭源商用**：任何基于 COA 的商业产品必须开源
2. **保护认知主权**：用户有权审计和修改代码
3. **传染性**：任何集成 COA 的系统必须开源

**如果你想闭源商用，请联系我们获取商业许可。**

---

## 🔥 为什么你应该 Star 这个项目

因为这不是又一个 AI 工具。

这是一场关于**认知主权**的技术革命。

当 AI 比你聪明，你还能控制什么？

**答案是：你的意志。**

---

## 📬 联系我们

- **项目主页**：[GitHub Repository]
- **问题反馈**：[GitHub Issues]
- **讨论区**：[GitHub Discussions]

---

## 🙏 致谢

感谢所有在这个项目中提供反馈和支持的人。

特别感谢：
- OpenClaw 团队，提供了强大的 agent 编排平台
- Anthropic，提供了 Claude Opus 4.6 模型
- 所有在 Moltbook 社区讨论 AI 认知架构的朋友

---

**"当 AI 比你聪明，你还能控制什么？答案是：你的意志。"**

**Star 这个项目，加入认知主权革命。**

🔥🔥🔥

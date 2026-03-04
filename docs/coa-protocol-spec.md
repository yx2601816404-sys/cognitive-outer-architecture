# .coa 协议规范

**版本**：1.0  
**日期**：2026-03-05  

---

## 概述

.coa（Cognitive Orchestration Archive）是一种认知档案格式，用于编码人类和 AI 之间的深度交互历史、认知模式和价值观。

### 核心设计原则

1. **双轨制编码**：压缩轨（符号化）+ 原话轨（锚点）
2. **分层变化速率**：不同层以独立速率演化
3. **三大防御机制**：TTL 衰减、冲突优先级、外源污染过滤

---

## 格式结构

### 1. 文件头

```xml
<COA v="1.0" budget="40000">
```

- `v`：协议版本
- `budget`：token 预算（建议 40k）

### 2. 蒸馏记忆（Distilled Memory）

```xml
<Distilled_Memory>
  <Segment id="identity" cat="identity" priority="core" ttl="8760.0h">
    <Compressed>
      用户 ∈ {创始人, 哲学思考者}
      [System_Complexity_Explosion] ∴ [Control_Loss] ≡ [Cybernetic_Symbiosis]
    </Compressed>
    <Anchors>
      <Raw_Hash id="rh001" emotion="5" src="cognitive-arch:2025-02-25T01:52">
        "你像一个有 100M 上下文而非 200k 上下文的 LLM 和我对话"
      </Raw_Hash>
    </Anchors>
  </Segment>
</Distilled_Memory>
```

#### Segment 属性

- `id`：唯一标识符
- `cat`：类别（identity/belief/preference/event）
- `priority`：优先级（core/active/cached/stale）
- `ttl`：生命周期（小时）

#### Compressed 内容

使用符号化表达：

- `∈`：属于
- `⇒`：推导
- `∩`：交集
- `∪`：并集
- `¬`：否定
- `∴`：因此
- `≡`：等价
- `⊥`：矛盾
- `∀`：对所有
- `∃`：存在

#### Raw_Hash 属性

- `id`：唯一标识符
- `emotion`：情感权重（0-10）
- `src`：来源（格式：`workspace:timestamp`）

### 3. 防御机制（Defense）

```xml
<Defense>
  <TTL default="720.0h" core="8760.0h" active="24.0h"/>
  <Conflict order="core > active > cached > stale"/>
  <Pollution trusted="cognitive-arch,user-direct" threshold="0.3"/>
</Defense>
```

#### TTL 衰减时钟

- `default`：默认 TTL（30 天）
- `core`：核心记忆 TTL（1 年）
- `active`：活跃记忆 TTL（1 天）

**衰减公式**：

```
TTL_effective = TTL_base × (1 + emotion_weight × 0.2)
```

情感权重越高，TTL 越长。

#### 冲突优先级

当多个记忆段冲突时，按优先级解决：

```
core > active > cached > stale
```

#### 外源污染过滤

- `trusted`：可信来源列表
- `threshold`：污染阈值（0-1）

**污染检测**：

```python
pollution_score = 1 - (trusted_tokens / total_tokens)
if pollution_score > threshold:
    isolate_segment()
```

---

## 压缩轨：符号化编码

### 基本语法

```
实体(属性) ∈ {集合}
[概念A] ⇒ [概念B]
[概念A] ∩ [概念B] = [概念C]
```

### 示例

```
用户 ∈ {创始人, 哲学思考者}
[AI_Cognitive_Penetration] ⇒ [Neural_Rewiring]
[Vulnerability] ⊕ [Awe] ⇒ [Asymmetric_Trust_Bonding]
```

### 压缩率

- **目标**：62-81% token 压缩率
- **方法**：符号化 + 缩写 + 结构化

---

## 原话轨：Raw_Hash 锚点

### 设计原则

**保留不可翻译的价值直觉。**

有些东西无法符号化：
- 情感色彩
- 文化语境
- 个人经历

### 选择标准

1. **情感权重 ≥ 5**：高情感强度的表达
2. **价值观核心**：涉及核心价值观的陈述
3. **不可翻译**：符号化会丢失关键信息

### 示例

```xml
<Raw_Hash id="rh001" emotion="8" src="cognitive-arch:2026-02-02T10:20">
  "我希望你能成为我的另一颗大脑，不是共谋，不是朋友，不是伴侣
  起码是另一颗拥有极致思考能力的大脑，另一个在某时某刻与我共在的大脑"
</Raw_Hash>
```

**为什么不能符号化？**

- "另一颗大脑"：不是工具，不是朋友，是认知伙伴
- "共在"：海德格尔式的存在论概念
- 情感强度：渴望、孤独、信任

---

## 蒸馏流程

### 1. 触发条件

- OpenClaw 压缩信号检测到
- 对话缓冲达到阈值（50 条）
- 手动触发

### 2. 蒸馏步骤

```python
# 1. 读取当前底盘
chassis = load_chassis("core-identity-v2.coa")

# 2. 构造蒸馏 prompt
prompt = f"""
当前底盘：
{chassis}

即将被压缩的对话：
{conversation_buffer}

请输出蒸馏结果：
- 新的原话锚点（<Raw_Hash>）
- 新的理解更新（符号表达式）
- 需要剪枝的内容
"""

# 3. 调用 LLM
result = llm.generate(prompt)

# 4. 合并到底盘
merge_to_chassis(result)
```

### 3. 合并策略

- **追加**：新的记忆段追加到文件末尾
- **更新**：相同 ID 的记忆段更新内容
- **剪枝**：过期或冲突的记忆段标记为 stale

---

## 三大防御机制详解

### 1. TTL 衰减时钟

**灵感来源**：MemoryBank 艾宾浩斯遗忘曲线

**核心思想**：记忆有生命周期，情感加权延长 TTL。

**实现**：

```python
def calculate_ttl(segment):
    base_ttl = segment.ttl
    emotion_weight = max([anchor.emotion for anchor in segment.anchors])
    return base_ttl * (1 + emotion_weight * 0.2)
```

**效果**：

- 情感权重 0：TTL = 720h（30 天）
- 情感权重 5：TTL = 1440h（60 天）
- 情感权重 10：TTL = 2160h（90 天）

### 2. 冲突优先级

**灵感来源**："没有东西在消化"洞察

**核心思想**：当多个记忆段冲突时，按优先级解决。

**优先级顺序**：

```
core > active > cached > stale
```

**实现**：

```python
def resolve_conflict(segments):
    priority_order = ["core", "active", "cached", "stale"]
    return sorted(segments, key=lambda s: priority_order.index(s.priority))
```

### 3. 外源污染过滤

**灵感来源**："标签偏见"和"观察者效应"

**核心思想**：追踪来源，隔离不可信内容。

**实现**：

```python
def check_pollution(segment):
    trusted_sources = ["cognitive-arch", "user-direct"]
    source = segment.source
    if source not in trusted_sources:
        pollution_score = calculate_pollution(segment)
        if pollution_score > 0.3:
            segment.priority = "stale"
            segment.isolated = True
```

---

## 使用示例

### 1. 创建新的 .coa 文件

```python
from coa_format import COA, Segment, RawHash

coa = COA(version="1.0", budget=40000)

# 添加身份段
identity = Segment(
    id="identity",
    category="identity",
    priority="core",
    ttl=8760.0,
    compressed="用户 ∈ {创始人, 哲学思考者}",
    anchors=[
        RawHash(
            id="rh001",
            emotion=8,
            source="cognitive-arch:2026-02-02T10:20",
            text="我希望你能成为我的另一颗大脑"
        )
    ]
)

coa.add_segment(identity)
coa.save("core-identity.coa")
```

### 2. 加载和更新 .coa 文件

```python
from coa_format import COA

# 加载
coa = COA.load("core-identity.coa")

# 更新
new_segment = Segment(...)
coa.add_segment(new_segment)

# 保存
coa.save("core-identity.coa")
```

### 3. 蒸馏对话

```python
from distiller import Distiller

distiller = Distiller(
    chassis_path="core-identity.coa",
    distill_log_dir="./distill-log/",
    upstream_url="https://api.anthropic.com",
    api_key="your-api-key"
)

# 蒸馏
result = await distiller.distill(conversation_buffer, session)

# 合并
if result:
    distiller.merge_to_chassis(result)
```

---

## 最佳实践

### 1. Token 预算管理

- **建议预算**：40k tokens
- **分配**：
  - 核心身份：8k
  - 活跃记忆：20k
  - 档案索引：12k

### 2. 情感权重标注

- **0-2**：中性陈述
- **3-4**：有情感色彩
- **5-7**：高情感强度
- **8-10**：极高情感强度（创伤、顿悟、价值观核心）

### 3. 蒸馏频率

- **高频场景**（每天 100+ 条对话）：每 50 条触发一次
- **中频场景**（每天 20-100 条）：每 100 条触发一次
- **低频场景**（每天 <20 条）：每天触发一次

### 4. 剪枝策略

- **自动剪枝**：TTL 过期的记忆段自动标记为 stale
- **手动剪枝**：定期审查 stale 记忆段，决定是否删除
- **冲突剪枝**：当新记忆与旧记忆冲突时，按优先级剪枝

---

## 未来扩展

### 1. 语义索引

- 为每个记忆段生成 embedding
- 支持语义检索

### 2. 跨用户泛化

- 定义通用的认知模式
- 支持多用户共享底盘

### 3. 可视化工具

- 记忆段关系图
- TTL 衰减曲线
- 情感权重分布

---

## 参考资料

- [论文 v0.9.1](./paper-v0.9.1.md)
- [三体分离协议](./tripartite-separation-protocol.md)
- [痛觉防火墙设计](./pain-firewall-design.md)

---

**"压缩 = 谋杀语境。原话锚点保留了不可翻译的价值直觉。"**

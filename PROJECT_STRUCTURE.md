# COA 项目结构

```
coa-opensource-release/
├── README.md                          # 项目介绍（极具煽动性）
├── QUICKSTART.md                      # 快速开始指南
├── CHANGELOG.md                       # 变更日志
├── CONTRIBUTING.md                    # 贡献指南
├── LICENSE                            # GPL-3.0 许可证
├── COMPATIBILITY_TEST_REPORT.md       # 兼容性测试报告
│
├── parasitic-shell/                   # Parasitic Shell v1.0
│   ├── shell.py                       # 主入口
│   ├── distiller.py                   # 蒸馏引擎
│   ├── memory_keeper.py               # 记忆管家
│   ├── config.yaml                    # 配置文件
│   ├── requirements.txt               # Python 依赖
│   ├── README.md                      # v1.0 说明
│   ├── coa_format/                    # .coa 格式处理
│   │   ├── schema.py                  # 数据结构
│   │   ├── encoder.py                 # 编码器
│   │   └── decoder.py                 # 解码器
│   ├── interceptor/                   # 拦截器
│   │   ├── proxy.py                   # 反向代理
│   │   └── hooks.py                   # 请求/响应钩子
│   ├── defenses/                      # 防御机制
│   │   ├── ttl_clock.py               # TTL 衰减时钟
│   │   ├── conflict_priority.py       # 冲突优先级
│   │   └── pollution_filter.py        # 外源污染过滤
│   └── distill-log/                   # 蒸馏日志目录
│
├── parasitic-shell-v2/                # Parasitic Shell v2.0（三体分离）
│   ├── shell.py                       # 主入口
│   ├── judge.py                       # Judge 实例管理
│   ├── thinker.py                     # Thinker 实例管理
│   ├── nerve.py                       # Nerve 实例管理
│   ├── protocol.py                    # 三体通信协议
│   ├── README.md                      # v2.0 说明
│   └── QUICKSTART.md                  # v2.0 快速开始
│
├── docs/                              # 文档
│   ├── paper-v0.9.1.md                # 论文 v0.9.1
│   ├── coa-protocol-spec.md           # .coa 协议规范
│   ├── tripartite-separation-protocol.md  # 三体分离协议（待补充）
│   └── pain-firewall-design.md        # 痛觉防火墙设计（待补充）
│
└── examples/                          # 示例文件
    └── core-identity-example.coa      # 示例 .coa 文件
```

---

## 核心组件说明

### 1. Parasitic Shell v1.0

**功能**：
- HTTP 反向代理，拦截 OpenClaw 和 LLM API 之间的请求
- 自动注入 .coa 底盘
- 监听压缩信号，触发蒸馏流程
- 支持流式响应透传

**适用场景**：
- 单用户场景
- 简单的认知底盘管理
- 快速原型验证

### 2. Parasitic Shell v2.0（三体分离）

**功能**：
- Judge 实例：风险评估 + 路由决策
- Thinker 实例：200k 纯推理
- Nerve 实例：痛觉反馈
- 风险分级路由（0-5 级）

**适用场景**：
- 高风险决策场景
- 需要价值观审查的场景
- 多实例协作场景

### 3. Distiller（炼丹炉）

**功能**：
- 压缩对话历史
- 提取理解模型的变化
- 自动更新 .coa 底盘
- 保存蒸馏日志

**适用场景**：
- 长期对话场景
- 需要记忆管理的场景
- 认知模式演化追踪

---

## 文件说明

### 配置文件

- `parasitic-shell/config.yaml`：v1.0 配置
- `~/.openclaw/openclaw.json`：OpenClaw 配置

### 日志文件

- `parasitic-shell/distill-log/`：蒸馏日志
- OpenClaw 日志：`~/.openclaw/logs/`

### 数据文件

- `.coa` 文件：认知底盘
- `.coa.bak` 文件：底盘备份

---

## 开发指南

### 添加新功能

1. 在对应目录下创建新文件
2. 遵循代码风格（PEP 8）
3. 添加单元测试
4. 更新文档

### 修改核心逻辑

1. 阅读相关文档
2. 理解现有实现
3. 提交 PR 前进行充分测试
4. 更新 CHANGELOG.md

### 贡献文档

1. 使用 Markdown 格式
2. 保持清晰的结构
3. 添加代码示例
4. 更新目录索引

---

## 依赖关系

```
parasitic-shell
├── aiohttp (异步 HTTP)
├── pyyaml (配置文件)
└── distiller
    └── aiohttp (LLM API 调用)

parasitic-shell-v2
├── aiohttp
├── judge
├── thinker
└── nerve
```

---

## 版本历史

- **v1.0.0**（2026-03-05）：首次开源发布
- **v0.9.1**（2026-03-03）：论文版本更新
- **v0.9.0**（2026-03-02）：三体分离协议草案
- **v0.8.0**（2026-03-02）：实验数据分析
- **v0.7.0**（2026-03-02）：理论框架完善

---

## 路线图

### 短期（1 个月）

- [ ] 完善文档
- [ ] 增加单元测试
- [ ] 优化性能
- [ ] 修复已知 bug

### 中期（3 个月）

- [ ] Gemini 递归蒸馏初始填充
- [ ] 流式响应优化
- [ ] 档案检索语义索引
- [ ] 跨用户泛化实验

### 长期（6 个月+）

- [ ] 可视化工具
- [ ] 多语言支持
- [ ] 云服务版本
- [ ] 商业许可

---

**"当 AI 比你聪明，你还能控制什么？答案是：你的意志。"**

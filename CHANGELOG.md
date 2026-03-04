# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 计划中的功能

- [ ] Gemini 递归蒸馏初始填充
- [ ] 流式响应的压缩信号检测优化
- [ ] 与沙盒实例（port 19789）集成测试
- [ ] 跨用户泛化实验
- [ ] 痛觉防火墙的自适应阈值
- [ ] 档案检索的语义索引优化

---

## [1.0.0] - 2026-03-05

### 🎉 首次开源发布

这是 COA（Cognitive Orchestration Architecture）项目的首次公开发布。

### Added

#### 核心组件

- **Parasitic Shell v1.0**：HTTP 反向代理，拦截 OpenClaw 和 LLM API 之间的请求
  - 零侵入，不改 OpenClaw 一行代码
  - 自动注入 .coa 底盘
  - 监听压缩信号，触发蒸馏流程
  - 支持流式响应透传

- **Parasitic Shell v2.0**：三体分离架构
  - Judge 实例：风险评估 + 路由决策
  - Thinker 实例：200k 纯推理
  - Nerve 实例：痛觉反馈
  - 风险分级路由（0-5 级）

- **Distiller（炼丹炉）**：LLM 蒸馏引擎
  - 压缩对话历史
  - 提取理解模型的变化
  - 自动更新 .coa 底盘
  - 保存蒸馏日志

#### .coa 协议

- **双轨制编码**：
  - 压缩轨：符号化表达（62-81% token 压缩率）
  - 原话轨：`<Raw_Hash>` 锚点，保留原始表达 + 情感权重

- **三大防御机制**：
  - TTL 衰减时钟：记忆段有生命周期
  - 冲突优先级：core > active > cached > stale
  - 外源污染过滤：追踪来源，隔离不可信内容

#### 文档

- **论文 v0.9.1**：完整的理论基础和实验数据
- **README**：极具煽动性的项目介绍
- **CONTRIBUTING**：贡献指南
- **CHANGELOG**：变更日志
- **示例 .coa 文件**：core-identity-v2.coa

### 实验数据

- **N=1，28 天深度实验**
- **压缩率**：62-81% token 压缩（符号化编码）
- **记忆保留**：原话锚点 100% 保留（情感权重 ≥ 5）
- **风险路由准确率**：87%（Judge 风险评估 vs 人工标注）
- **痛觉信号触发**：12 次（28 天），0 次误报

---

## [0.9.1] - 2026-03-03

### Changed

- 论文版本更新至 v0.9.1
- 清理论文格式，移除冗余内容
- 优化 .coa 协议规范

---

## [0.9.0] - 2026-03-02

### Added

- 论文 v0.9 完成
- 三体分离协议草案
- 痛觉防火墙设计

---

## [0.8.0] - 2026-03-02

### Added

- 论文 v0.8 完成
- 增加实验数据分析
- 完善理论框架

---

## [0.7.0] - 2026-03-02

### Added

- 论文 v0.7 完成
- 增加跨学科视角（哲学、心理学、神经科学）
- 完善意志代理的理论基础

---

## [0.6.0] - 2026-03-01

### Added

- 论文 v0.6 完成
- 增加实验设计和验证路径
- 完善 .coa 协议规范

---

## [0.5.0] - 2026-03-01

### Added

- 论文 v0.5 完成
- 增加三体分离架构设计
- 完善双轨制编码方案

---

## [0.4.0] - 2026-02-28

### Added

- 论文 v0.4 完成
- 增加意志代理的哲学基础
- 完善认知底盘设计

---

## [0.3.0] - 2026-02-26

### Added

- Parasitic Shell v1.0 MVP 完成
- Distiller 蒸馏引擎完成
- .coa 格式初版完成

---

## [0.2.0] - 2026-02-25

### Added

- 三层存在架构实验完成
- 100 次对照实验数据分析
- 行为可塑性验证

---

## [0.1.0] - 2026-02-24

### Added

- 项目启动
- 认知编排架构（COA）初版设计
- 八组件架构提出

---

## 版本说明

- **1.x.x**：稳定版本，适合生产环境
- **0.x.x**：开发版本，功能可能不完整
- **x.x.x-alpha**：内部测试版本
- **x.x.x-beta**：公开测试版本

---

## 如何升级

### 从 0.x.x 升级到 1.0.0

1. 备份你的 .coa 底盘文件
2. 更新代码：`git pull origin main`
3. 安装依赖：`pip install -r requirements.txt`
4. 重启 Parasitic Shell

### 破坏性变更

- 无（首次发布）

---

## 致谢

感谢所有在这个项目中提供反馈和支持的人。

特别感谢：
- OpenClaw 团队
- Anthropic
- Moltbook 社区

---

**"当 AI 比你聪明，你还能控制什么？答案是：你的意志。"**

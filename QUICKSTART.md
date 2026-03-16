# 快速开始指南

欢迎使用 COA（Cognitive Orchestration Architecture）！

这份指南将帮助你在 5 分钟内启动并运行 Parasitic Shell。

---

## 前置要求

- **Python 3.10+**
- **OpenClaw**（已安装并配置）
- **Anthropic API Key**（或其他 LLM API）

---

## 步骤 1：安装依赖

```bash
cd parasitic-shell
pip install -r requirements.txt
```

依赖列表：
- `aiohttp`：异步 HTTP 客户端
- `pyyaml`：YAML 配置文件解析

---

## 步骤 2：准备 .coa 底盘文件

你可以使用示例文件，或创建自己的底盘：

```bash
# 使用示例文件
cp examples/core-identity-example.coa my-chassis.coa

# 或者创建新文件
nano my-chassis.coa
```

.coa 文件格式详见 [docs/coa-protocol-spec.md](./docs/coa-protocol-spec.md)。

---

## 步骤 3：启动 Parasitic Shell

### 方式 1：使用默认配置

```bash
cd parasitic-shell
python3 shell.py
```

默认配置：
- 底盘文件：`/home/lyall/.openclaw/workspace/cognitive-arch/core-identity-v2.coa`
- 监听端口：`18900`
- 上游 API：`https://api.anthropic.com`

### 方式 2：自定义配置

```bash
python3 shell.py \
  --chassis /path/to/my-chassis.coa \
  --port 18900 \
  --upstream https://api.anthropic.com \
  --debug
```

参数说明：
- `--chassis`：底盘文件路径
- `--port`：监听端口
- `--upstream`：上游 LLM API 地址
- `--debug`：开启调试模式

---

## 步骤 4：配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`，将 provider 的 `baseURL` 改为 Parasitic Shell 的地址：

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

---

## 步骤 5：测试

### 测试 1：发送简单请求

```bash
curl -X POST http://127.0.0.1:18900/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-opus-4-6",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "你好，请介绍一下你自己"}]
  }'
```

### 测试 2：检查底盘注入

查看 Parasitic Shell 的日志，应该看到：

```
[INFO] 底盘已注入 (40123 chars)
```

### 测试 3：触发压缩信号

在 OpenClaw 中进行长时间对话，当上下文压缩时，Parasitic Shell 会自动触发蒸馏流程：

```
[WARNING] ⚠️  压缩信号检测到: Pre-compaction memory flush
[INFO] 🧪 开始蒸馏 50 条对话...
[INFO] 🧪 蒸馏完成，结果保存到 distill-log/distill-20260305-055123.md
[INFO] ✅ 底盘已更新并重新加载
```

---

## 步骤 6：使用三体分离架构（可选）

如果你想使用更高级的三体分离架构（Judge/Thinker/Nerve），可以使用 v2 版本：

```bash
cd parasitic-shell-v2
python3 shell.py --chassis /path/to/my-chassis.coa
```

三体分离架构会根据风险等级自动路由请求：

- **风险 0-1**：Judge 快速通路（1x 成本）
- **风险 2**：Judge + Thinker（2x 成本）
- **风险 3**：Judge + Thinker + Nerve（2.5x 成本）
- **风险 4-5**：三体全开 + 人工确认（3x 成本）

---

## 常见问题

### Q1：为什么我的请求没有响应？

**A**：检查以下几点：
1. Parasitic Shell 是否正常启动？
2. OpenClaw 的 `baseURL` 是否正确配置？
3. 上游 API 是否可访问？
4. API Key 是否正确？

### Q2：如何查看蒸馏日志？

**A**：蒸馏日志保存在 `parasitic-shell/distill-log/` 目录下，文件名格式为 `distill-YYYYMMDD-HHMMSS.md`。

### Q3：如何自定义压缩信号检测？

**A**：编辑 `shell.py`，修改 `COMPRESSION_PATTERNS` 列表：

```python
COMPRESSION_PATTERNS = [
    re.compile(r"Pre-compaction memory flush", re.I),
    re.compile(r"Store durable memories now", re.I),
    # 添加你自己的模式
    re.compile(r"your-custom-pattern", re.I),
]
```

### Q4：如何备份底盘文件？

**A**：Parasitic Shell 会在每次更新底盘时自动创建备份文件（`.coa.bak`）。你也可以手动备份：

```bash
cp my-chassis.coa my-chassis.coa.backup-$(date +%Y%m%d)
```

### Q5：如何升级到最新版本？

**A**：

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## 下一步

- 阅读 [论文 v0.9.1](./docs/paper-v0.9.1.md) 了解理论基础
- 阅读 [.coa 协议规范](./docs/coa-protocol-spec.md) 了解底盘格式
- 查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解如何贡献
- 加入我们的社区（Discord/Twitter）

---

## 获取帮助

如果你遇到问题，可以：

1. 查看 [GitHub Issues](https://github.com/your-repo/issues)
2. 加入 Discord 社区
3. 发送邮件到 [待补充]

---

**"当 AI 比你聪明，你还能控制什么？答案是：你的意志。"**

祝你使用愉快！🔥

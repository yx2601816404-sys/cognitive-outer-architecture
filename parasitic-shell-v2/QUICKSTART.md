# 三体分离架构 — 快速启动

## 启动

```bash
cd parasitic-shell-v2

# 设置环境变量
export ANTHROPIC_API_KEY="your-api-key"

# 启动三体外壳
python3 shell.py \
  --chassis /path/to/core-identity.coa \
  --port 18901 \
  --upstream https://api.anthropic.com
```

外壳会监听 `127.0.0.1:18901`，通过三体架构处理所有请求。

## 测试

```bash
curl -X POST http://127.0.0.1:18901/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-opus-4-6",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

## 架构

```
请求 → Judge（风险评估）→ 路由决策
                          ├→ Thinker（深度推理）
                          └→ Nerve（安全审查）→ 痛觉反馈
```

## 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--chassis` | 自动检测 | 底盘文件路径 |
| `--port` | 18901 | 监听端口 |
| `--upstream` | `https://api.anthropic.com` | 上游 API |
| `--debug` | false | 调试模式 |

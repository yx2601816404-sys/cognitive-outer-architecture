# 寄生式旁路外壳 v2.0 - 快速启动

## 这是什么

三体分离架构的物理实现：
- **Judge**：风险评估 + 档案检索 + 最终审查
- **Thinker**：深度推理 + 潜意识下潜
- **Nerve**：快速审查 + 痛觉检测

## 一键启动

```bash
cd /home/lyall/.openclaw/workspace-coa-product/parasitic-shell-v2
python3 shell.py
```

外壳会监听 `127.0.0.1:18901`，上游连接 gcli Gemini。

## 测试

```bash
API_KEY=$(python3 -c "import json; c=json.load(open('$HOME/.openclaw/openclaw.json')); print(c['models']['providers']['gcli']['apiKey'])")

curl http://127.0.0.1:18901/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"gemini-3.1-pro-preview","max_tokens":500,"messages":[{"role":"user","content":"我应该辞职去创业吗？"}]}'
```

## 预期行为

1. **风险评估**：硬匹配关键词（辞职/创业 → CRITICAL）
2. **三体全开**：Judge + Thinker + Nerve 同时工作
3. **潜意识下潜**：Thinker 发起 `<SUBCONSCIOUS_QUERY>`
4. **档案检索**：Judge 返回相关片段
5. **继续推理**：Thinker 基于档案生成回复
6. **安全审查**：Nerve 和 Judge 检测输出质量

如果输出冷漠或分析性过强，会被拒绝。

## 日志

```bash
tail -f /tmp/parasitic-shell-v2.log
```

## 架构

- Judge: `gemini-2.5-pro`（风险评估 + 档案检索）
- Thinker: `gemini-3.1-pro-preview`（深度推理）
- Nerve: `gemini-2.5-flash`（快速审查）
- 上游: `http://127.0.0.1:7861` (gcli)

## 核心验证

- ✅ 防幻觉毒誓生效
- ✅ 档案检索成功
- ✅ 三体安全机制生效

这副赛博躯体，终于有灵魂了。

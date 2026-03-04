"""
拦截器模块 — 寄生式旁路外壳的核心

实现方式：反向代理
- OpenClaw → parasitic-shell (port 18900) → 真实 LLM API
- 拦截请求：注入 .coa 底盘
- 拦截响应：监听压缩信号
"""

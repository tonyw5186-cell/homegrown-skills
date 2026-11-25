---
name: openrouter-model-call-volume
description: 读取 OpenRouter 官方模型请求量完整周榜；用于用户询问该平台模型调用请求排名时。
compatibility: Requires Python 3.10+, shell execution, and network access; standard library only.
---

# OpenRouter 请求量

运行：`python scripts/openrouter_rankings.py --limit 10`

只返回脚本获取的官方公开榜JSON。脚本仅请求OpenRouter来源，不调用其他服务、不写入数据；Agent负责何时调用、如何综合，思源写入由独立MCP处理。

- 仅接受标题为 `Models ranked by requests in the most recent complete week` 的表；指标是请求次数，不是 tokens。
- `Others` 是聚合行，不是单一模型。保留原表名次与字段。
- 失败时返回错误状态；不要改用搜索摘要或旧数据补齐。

---
name: model-trend-boards
description: 分别读取 Hugging Face 与 ModelScope 站内模型趋势；用于用户询问开源模型近期热度时。
compatibility: Requires Python 3.10+, shell execution, and network access; standard library only.
---

# 模型趋势

运行：`python scripts/model_trends.py --limit 10`

脚本只读两个官方来源并以独立 `boards[]` 返回数据。Agent负责调度与综合；思源持久化由独立MCP处理。

- Hugging Face 使用Hub模型趋势API；ModelScope使用官方趋势接口。
- 两个平台分别保留原始顺序和可见字段，不跨平台合并或推算总榜。
- 单边失败只报告该边错误；不得用另一平台或第三方数据填补。下载量、点赞、站内趋势不等于调用量或能力。

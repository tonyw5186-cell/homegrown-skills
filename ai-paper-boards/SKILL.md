---
name: ai-paper-boards
description: 分别获取 arXiv 新近论文与 Hugging Face Daily Papers 社区热度；用于用户询问近期AI论文时。
compatibility: Requires Python 3.10+, shell execution, and network access; standard library only.
---

# AI论文信息

运行：`python scripts/paper_boards.py --days 7 --limit 10`

脚本只读取官方来源并分别返回arXiv与HF Daily Papers数据。Agent负责挑选、解释与组合；思源写入交给独立MCP。

- arXiv优先读 `cs.AI`、`cs.LG`、`cs.CL` RSS；RSS空/不可读时回退官方Atom。Atom缺少 `announce_type`，只能按 `published` 时间作新近提交代理，不能精确区分新作、跨列或更新。
- HF Daily Papers表示站内社区热度，不是论文质量。某来源失败时如实保留错误，不用搜索摘要补数。

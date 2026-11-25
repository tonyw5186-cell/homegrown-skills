# AI 论文分榜

分别读取 arXiv 新近论文与 Hugging Face Daily Papers 社区热度，不把它们合并为质量榜。

## 运行

```bash
python scripts/paper_boards.py --days 7 --limit 10
```

- `--days`：检索窗口，范围 1–14，默认 7。
- `--limit`：每个分榜最多返回的条目数，范围 1–20，默认 10。
- `--timeout`：单次请求超时秒数，默认 10。

## 口径与限制

- arXiv 优先读取 `cs.AI`、`cs.LG`、`cs.CL` RSS；无窗口内条目或 RSS 不可用时回退官方 Atom API。Atom 不提供 `announce_type`，回退结果按 published 时间过滤，不能精确识别新作公告类型。
- arXiv 列表按新近度，不是论文质量排名。
- Hugging Face Daily Papers 表示社区发现/投票热度，不等于同行评审质量。
- 来源失败时保留错误状态，不以搜索摘要替换。

## 文件

- `SKILL.md`：DSH Agent Skill 定义。
- `scripts/paper_boards.py`：Python 标准库抓取与解析脚本。

# OpenRouter 模型请求量

读取 OpenRouter 官方排行榜中**最近一个完整周**的模型请求 Top 10。

## 运行

```bash
python scripts/openrouter_rankings.py --limit 10
```

- `--limit`：返回行数，范围 1–20，默认 10。
- 只请求 `https://openrouter.ai/rankings`，从官方页面表格解析最近完整周数据；输出 JSON，包含状态、来源、采集时间、指标、时间窗和 rows。

## 口径

- 指标为 `requests`（请求次数），不是 tokens、用户数或模型能力。
- `Others` 是来源页面的聚合行，不是单一模型；保留官方原始名次和字段。
- 页面结构变化、目标周榜缺失或网络失败时返回 error；不使用旧数据或搜索摘要补齐。

## 文件

- `SKILL.md`：DSH Agent Skill 定义。
- `scripts/openrouter_rankings.py`：Python 标准库抓取与解析脚本。

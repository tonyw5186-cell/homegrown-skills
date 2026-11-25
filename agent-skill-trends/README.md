# Agent Skill 趋势

读取 skills.sh 当前 Trending 页面的 Agent Skill Top 10、安装量和页面周期标签。

## 运行

```bash
python scripts/skills_sh_trending.py --limit 10
```

- `--limit`：最大条目数，范围 1–20，默认 10。
- 输出 JSON 包含来源 URL、采集时间、页面 `period_label` 和 rows。

## 口径与限制

- 安装量是 skills.sh 生态的页面信号，不代表所有 Agent 平台的使用、留存或质量。
- 原样报告页面实际周期标签。若标题和选中的 tab（例如“This Week”与“Trending (24h)”）不一致，不擅自解释为周增量。
- 页面结构改变或榜单数据缺失时失败关闭；不以第三方榜单补齐，也不安装或运行被排名的 Skill。

## 文件

- `SKILL.md`：DSH Agent Skill 定义。
- `scripts/skills_sh_trending.py`：Python 标准库页面解析脚本。

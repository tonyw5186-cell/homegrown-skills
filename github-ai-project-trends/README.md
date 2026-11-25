# GitHub AI 项目趋势

从 GitHub 官方 REST API 检索 AI 仓库，并可为 Stars Top 10 候选生成 Release 附件累计下载次榜。

## 运行

```bash
python scripts/github_ai_projects.py --limit 10
python scripts/github_ai_projects.py --limit 10 --release-downloads
```

- `--query`：GitHub Search 条件，默认 `topic:artificial-intelligence`。
- `--limit`：Search 项目数，范围 1–30，默认 10。
- `--release-downloads`：对 Stars 候选读取公开 Releases/Assets 并计算附件下载排名；启用时 `--limit` 不得超过 10，以控制匿名 API 请求量。
- `--ca-file`：可选的可信 PEM CA bundle 路径；TLS 验证保持开启。

## 指标定义

- 主榜按累计 Stars 排序；它不是官方 weekly trending，也不是本周 Stars 增长。
- 下载次榜汇总每个候选项目公开 Release 附件的 `download_count`，最多扫描最近 500 个公开 Release；Stable 与 Prerelease 分别统计。只有分页完整的项目参与排名，不完整或错误项目列为未排名状态。
- `download_count` 是抓取时的附件累计量，不包含仓库 clone、GitHub 自动生成的源码压缩包、npm/PyPI 包安装量，也不是周增量。没有可计数附件时的 0 不表示项目无人使用。

## 文件

- `SKILL.md`：通用 Agent Skill 定义及安全/指标约束。
- `scripts/github_ai_projects.py`：Python 标准库 GitHub API 客户端。

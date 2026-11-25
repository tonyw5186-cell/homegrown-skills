---
name: github-ai-project-trends
description: 从 GitHub 官方REST API检索AI项目，并可比较Top10候选中的Release附件累计下载；用于用户询问GitHub AI项目趋势与下载数据时。
compatibility: Requires Python 3.10+, shell execution, network access, and a trusted CA store; standard library only.
---

# GitHub AI项目

运行：`python scripts/github_ai_projects.py --limit 10 --release-downloads`；可用 `--query` 指定GitHub Search条件。`--release-downloads`只允许Top10候选，避免匿名API请求过量。

只返回GitHub官方REST Search与Releases/Assets数据。Agent负责跨源调度与分析；思源写入由独立MCP处理。

- 排序按累计stars，不是官方周趋势或时间窗增量；不得称为“本周增长”。
- Release 下载维度为前10个累计Stars候选项目中，公开Release附件 `download_count` 的累计和；每个项目最多扫描最近500个公开Release，区分stable与prerelease。只有分页完整的项目才进入下载排名，`partial/error`项目单列。
- 该值是抓取时点的附件累计下载数，不是项目总下载、clone数、源码归档下载、package installs或本周增量。没有Release assets时显示0并注明“无附件”，不能解读为无人使用。周增量需未来对同一批资产保存快照后相减。
- TLS验证保持开启；若系统证书不可用，可用 `--ca-file` 指向已有可信PEM证书包。
- 不clone、不运行仓库代码，不创建快照或写入数据。

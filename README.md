# Homegrown AI Ranking Skills

五个独立的 DSH Agent Skills，用于从公开官方来源读取 AI 模型、论文、项目和 Agent Skill 排行信息。每个目录都包含标准 `SKILL.md`、Python 脚本和独立说明文档。

## Skills

| 目录 | 用途 | 数据来源 |
|---|---|---|
| [openrouter-model-call-volume](openrouter-model-call-volume/README.md) | OpenRouter 最近完整周的模型请求 Top 10 | OpenRouter Rankings |
| [model-trend-boards](model-trend-boards/README.md) | 两个平台的模型趋势分榜 | Hugging Face Hub、ModelScope |
| [ai-paper-boards](ai-paper-boards/README.md) | arXiv 新近论文与 Daily Papers 社区热度 | arXiv、Hugging Face |
| [github-ai-project-trends](github-ai-project-trends/README.md) | GitHub AI 项目 Stars Top 10，可附 Release 附件下载次榜 | GitHub REST Search / Releases API |
| [agent-skill-trends](agent-skill-trends/README.md) | skills.sh Skill 趋势 Top 10 | skills.sh |

## 安装与运行

- 要求 Python 3.10 或更新版本；所有脚本只使用 Python 标准库，无需安装第三方包。
- 将需要的完整 Skill 子目录复制到 DSH 用户 Skills 目录（例如 Windows 的 `%USERPROFILE%\.dsh\skills\`），保留目录名、`SKILL.md` 和 `scripts/` 结构。
- 从对应 Skill 目录运行其 `README.md` 中的命令。各脚本将结构化 JSON 输出到 stdout。

## 设计约定

- 各 Skill 独立读取其说明中列出的公开来源；不跨源填补缺失结果，不克隆或运行第三方仓库代码。
- 输出保留来源、采集时间、状态和可见数据口径。失败/部分失败须显式报告，不能把站内热度、累计量误称为能力或周增量。
- Skill 脚本不写思源或其他数据存储；如需持久化，由调用方通过获准的集成单独完成。
- GitHub Release 的 `download_count` 是附件累计下载数，不是仓库 clone、源码归档、包安装或项目总下载量；详情见对应 Skill README。

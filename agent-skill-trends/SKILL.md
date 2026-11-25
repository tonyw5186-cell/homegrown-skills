---
name: agent-skill-trends
description: 读取 skills.sh Agent Skill 安装趋势；用于用户询问该平台的Skill热度时。
compatibility: Requires Python 3.10+, shell execution, and network access; standard library only.
---

# Agent Skill趋势

运行：`python scripts/skills_sh_trending.py --limit 10`

脚本只读 skills.sh 趋势页，返回页面周期标签、顺序和安装量。Agent负责调度与解读；不由本Skill写入思源。

- 只报告页面实际显示的周期和字段；页面结构变化或缺少榜单数据时失败关闭。
- 这是skills.sh支持生态中的安装信号，不代表所有Agent平台的使用、留存或质量。
- 不安装Skill、不运行安装遥测、不用第三方榜单补齐。

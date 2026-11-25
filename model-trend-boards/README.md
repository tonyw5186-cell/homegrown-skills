# 模型趋势分榜

分别读取 Hugging Face Hub 与 ModelScope 的站内模型趋势；两个来源始终独立呈现。

## 运行

```bash
python scripts/model_trends.py --limit 10
```

- `--limit`：每个来源的最大行数，范围 1–20，默认 10。
- Hugging Face 使用公开 Hub 模型趋势 API；ModelScope 使用官方趋势接口。
- 输出 JSON 的 `boards` 分别记录来源、状态、URL、rows 和错误信息。

## 口径与限制

- 保留各平台自己的排序和返回字段，不合并成跨平台总榜。
- Downloads、Likes 和站内趋势信号不等同于调用量、模型能力或质量。
- 任一来源失败时另一个来源仍可成功返回，整体状态会标为 `partial`；不得用另一平台或第三方数据填补。

## 文件

- `SKILL.md`：通用 Agent Skill 定义与调用说明。
- `scripts/model_trends.py`：Python 标准库抓取与解析脚本。

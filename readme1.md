---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 4fd20e68f8b80beb1e39f35a6c960ac4_5a36f32380cc11f1afc3525400de82e7
    ReservedCode1: cPCUf98FXzhSQuaTmXjcnJEOQKwUqWLgQ8FTrr8cHvIdBg8zVJ947DiNpMHuJpjZM3HwBP9mHw10z3Pv+XdjK9SWKOK4l5l+AGEF5mpaJla0Hp3D9uHa3PVsBVi6o7AOdEXupmUlBLVEUogmyajzXO9W2I0mOcFRorG9QlPwNR8Sa71dVOm1w2pSrqM=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 4fd20e68f8b80beb1e39f35a6c960ac4_5a36f32380cc11f1afc3525400de82e7
    ReservedCode2: cPCUf98FXzhSQuaTmXjcnJEOQKwUqWLgQ8FTrr8cHvIdBg8zVJ947DiNpMHuJpjZM3HwBP9mHw10z3Pv+XdjK9SWKOK4l5l+AGEF5mpaJla0Hp3D9uHa3PVsBVi6o7AOdEXupmUlBLVEUogmyajzXO9W2I0mOcFRorG9QlPwNR8Sa71dVOm1w2pSrqM=
---



# 🧠 思维永生 · MindVault — 完整版部署指南

> MindVault v1.1.0 起不再区分免费版/赞赏版，统一为完整版发布。本文档说明如何把完整能力部署为个人的 Agent 记忆与思考基础设施。

---

## MindVault 是什么

一套**开箱即用的 Agent 记忆与思考基础设施**，由三层架构 + DRAS-V 五步思考协议组成：

| 层 | 名称 | 载体 | 作用 |
|----|------|------|------|
| Layer 1 | 对话归档 | JSONL + `scripts/*.py` | 对话长期备份，每 15 轮切割一个 JSONL，对话隔离存储 |
| Layer 2 | 规则萃取 | `DRASV_LOOP.md` 等 | 从归档对话中持续提取高频模式与偏好 |
| Layer 3 | 项目快照 | `PROJECT_SNAPSHOT.md` | 快速恢复跨会话上下文 |

所有数据本地存储，不上传云端——你拥有完整的数据主权（JSONL 格式，换平台无缝带走）。

---

## 一、核心能力

| 能力 | 怎么用 | 底层发生了什么 |
|------|--------|---------------|
| 对话长期归档 | 说「归档对话」 | `archive_export.py` 从平台数据源导出对话（OpenClaw / Marvis 双模），支持全量 + 增量合并，每次写入 `_index.json` 并自增 `index_version` |
| 规则自动萃取 | 说「执行进化引擎」 | `archive_index.py` 分析未处理归档，提取高频模式和偏好，写入规则文件 |
| 快速恢复上下文 | 说「生成项目快照」 | 基于 S.4 三遍扫描法生成 `PROJECT_SNAPSHOT.md`，下次对话直接继承 |
| 可选五步思考 | 用户说「走流程」「DRASV」时激活 | DRAS-V 协议（D→R→A→S→V），不跳步、可审计 |
| 索引检索与统计 | 命令行 | `stats` / `pending` / `search` / `summary` 全量可用 |
| 对话可读回溯 | 命令行 | `jsonl_to_md.py --style minimal\|full`，`--css` 输出带样式的 HTML 阅读页 |

---

## 二、脚本能力（完整版，无功能阉割）

### `archive_index.py` — 归档索引管理

| 命令 | 效果 |
|------|------|
| `stats` | 查看归档统计：文件数、已处理/未处理、轮次范围 |
| `pending` | 列出待处理（未萃取）的归档文件 |
| `mark` | 标记已处理（支持 `--if-version` 乐观版本校验，冲突时拒绝写入并提示） |
| `search` | 按日期/轮次检索归档文件 |
| `summary` | 生成脚本级摘要报告 |

### `jsonl_to_md.py` — JSONL → Markdown / HTML

- `--style minimal`：仅用户 + Agent 消息（默认）
- `--style full`：全部角色（Agent 推理 / Tool 调用摘要 / System / 定时任务）
- `--css <file>`：将 Markdown 渲染进带 CSS 样式的 HTML 阅读页

### `archive_export.py` — 对话归档导出

- `openclaw` 模式：从 sessions 目录导出
- `marvis` 模式：从 conversation 数据库导出
- `--incremental`：增量模式，自动合并 `_index.json`（修复了旧版参数不匹配导致索引需手动生成的问题）

---

## 三、并发写入纪律（B9 / B15）

- **B9 版本令牌**：所有写入 `_index.json` 的操作都会读取并在写后自增 `index_version`；多端（多 Agent / 多平台）并发写时，用 `--if-version` 校验版本，避免覆盖其他端的修改。
- **B15 不存在即异常**：`mark` 等写操作遇到索引缺失/版本冲突时直接报错退出，绝不静默写入或静默吞掉解析异常。

---

## 四、配套文件索引

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 核心指令集（DRAS-V + 三层架构），Agent 直接加载执行 |
| `README.md` | 项目概览，GitHub 首页展示 |
| `readme1.md` | 本文档，完整版部署指南 |
| `scripts/archive_export.py` | 对话归档导出（OpenClaw + Marvis 双模，全量/增量） |
| `scripts/archive_index.py` | 归档索引管理（stats / pending / mark / search / summary） |
| `scripts/jsonl_to_md.py` | JSONL → Markdown / HTML（minimal / full / --css） |
| `LICENSE` | MIT 开源协议 |
| `CHANGELOG.md` | 版本更新记录 |

---

*思维永生 · MindVault v1.1.0 — 5000+ 轮实战验证，跨平台 (OpenClaw / Marvis / CherryStudio / Coze)*
*（内容由AI生成，仅供参考）*

---

## 购买与支持

MindVault 自 v1.1.0 起统一完整版免费发布。如需一对一部署指导、优先答疑等专属支持，或希望支持作者持续更新，可前往链动小铺：

👉 **https://wzyp.cn/item/p0r2lb**

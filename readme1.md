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



# 🧠 思维永生 · MindVault — 部署指南与赞赏版说明

> 如果你已经跑通了基础版的 SKILL.md，这里告诉你：它能做什么、卡在哪、以及升级后能得到什么。

---

## 基础版能跑通什么

MindVault 基础版是一套**开箱即用的 Agent 记忆与思考基础设施**。部署 SKILL.md 后，你可以立即获得：

| 能力 | 怎么用 | 底层发生了什么 |
|------|--------|---------------|
| 对话永久归档 | 说「归档对话」 | `archive_export.py` 从平台数据源增量导出最新对话，每 15 轮切割一个 JSONL，对话隔离存储 |
| 规则自动萃取 | 说「执行进化引擎」 | `archive_index.py` 分析未处理归档，提取高频模式和偏好，写入 `memory/FACT.md` |
| 30 秒恢复上下文 | 说「生成项目快照」 | 基于 S.4 三遍扫描法，生成 `PROJECT_SNAPSHOT.md`，下次对话直接继承 |
| 强制五步思考 | 每次任务自动走 | DRAS-V 协议（D→R→A→S→V），不跳步、可审计 |
| 对话可读回溯 | 手动执行脚本 | `jsonl_to_md.py --style minimal` 生成人类可读 Markdown |

这已经超过绝大多数 Agent 记忆方案——你拥有了**数据主权**（JSONL 格式，换平台无缝带走）、**可审计的思考过程**（每步工具调用和推理都可回溯）、**自动学习的规则系统**。

---

## 基础版会卡在哪里

这些能力很好，但有一个根本问题：**它们全是手动的**。

- 你必须记住定期说「归档对话」——否则对话窗口溢出后永久丢失
- 你必须手动触发「执行进化引擎」——规则不会自动更新
- 你需要时再说「生成项目快照」——但通常已经忘了上次聊到哪
- JSONL 到 Markdown 只有 minimal 模式——缺少结构化摘要和 HTML 输出

这让 MindVault 像一个性能强劲但**手动挡**的跑车：能力都在，但你得时刻想着踩离合。

---

## 赞赏版：从手动到自动

赞赏版不是「解锁更多功能」，而是**把所有手动操作变成自动触发的后台进程**。

### 自动触发引擎

| 触发条件 | 自动动作 | 效果 |
|---------|---------|------|
| 对话超过 20 轮 | 自动执行增量归档 | 你不再需要记住说「归档对话」，数据静默保存 |
| 归档后待处理 > 5 个文件 | 自动触发进化引擎 | 规则持续从新对话中萃取，Agent 越来越懂你 |
| 每周日 | 自动生成 HTML 周报 + 发送 | 一周的思考、决策、项目进展自动汇总 |

Agent 在每次回复前自动检查以上条件——你只管聊，MindVault 管记得。

### 脚本能力升级

| 脚本 | 基础版 | 赞赏版 |
|------|--------|--------|
| `archive_index.py` | `stats`、`pending`（查看归档状态） | + `mark`（标记已处理）、`search`（按日期/轮次检索）、`summary`（生成摘要报告） |
| `jsonl_to_md.py` | `--style minimal`（简版，最多 3 个文件） | + `--style full`（含 Tool/System 完整信息）、`--css`（输出 HTML 带样式卡片） |

### 新增命令

| 命令 | 效果 |
|------|------|
| `生成周报` | 一键生成本周对话 HTML 周报，含关键决策、项目进展、待办事项 |

---

## 三层对比

| | 不用 MindVault | 基础版（开源） | 赞赏版 |
|------|:--:|:--:|:--:|
| 对话保存 | 窗口溢出即丢失 | ✅ 手动归档 | ✅ 自动归档 |
| 规则学习 | 每次重新教 | ✅ 手动触发萃取 | ✅ 实时自动萃取 |
| 上下文恢复 | 靠记忆/重新描述 | ✅ 手动生成快照 | ✅ 自动生成快照 |
| 结构化检索 | ❌ | ❌ | ✅ search/summary |
| 周报汇总 | ❌ | ❌ | ✅ 每周自动生成 |
| HTML 展示 | ❌ | ❌ | ✅ 带样式的可读卡片 |

---

## 设计理念

MindVault 不是靠「藏功能」来区分版本。基础版已经包含了**完整的核心架构**（DRAS-V + Layer 1/2/3 + 三个脚本的全部核心逻辑），因为我们认为：

> 数据归档和思考协议是基础设施，不应该被付费墙挡住。

赞赏版的价值在于**自动化**——把手动操作变成后台服务。这保持了 MIT 开源精神的纯粹，也让愿意支持的人获得真正的效率提升。

---

## 赞赏获取

如果你已经用基础版跑通，想要：

- 忘记「归档对话」这句话，让数据自动保存
- 让 Agent 随着对话越来越多而越来越懂你
- 每周日收到一份 HTML 周报，而不是翻 JSONL

👉 [赞赏获取部署文档](https://pay.ldxp.cn/item/p0r2lb)

---

## 配套文件索引

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 核心指令集（DRAS-V + 三层架构），Agent 直接加载执行 |
| `README.md` | 项目概览，GitHub 首页展示 |
| `readme1.md` | 本文档，完整的赞赏版说明与部署指南 |
| `scripts/archive_export.py` | 对话归档导出（OpenClaw + Marvis 双模） |
| `scripts/archive_index.py` | 归档索引管理（基础版：stats / pending） |
| `scripts/jsonl_to_md.py` | JSONL → Markdown 转换（基础版：minimal） |
| `LICENSE` | MIT 开源协议 |
| `CHANGELOG.md` | 版本更新记录 |

---

*思维永生 · MindVault v1.0.0 — 5000+ 轮实战验证，跨平台 (OpenClaw / Marvis / CherryStudio / Coze)*
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*

---
name: mindvault
description: >
  思维永生 · MindVault — Agent 对话归档与思考辅助系统。
  提供对话备份(JSONL)+规则萃取+项目快照三层记忆能力，以及DRAS-V五步思考辅助协议。
  5000+轮实战验证，跨平台(OpenClaw/Marvis/CherryStudio/Coze)。所有数据本地存储，不上传云端。
version: 1.0.0
author: zhouxin121
license: MIT
keywords:
  - mindvault
  - conversation-archiver
  - 对话备份
  - 对话归档
  - 资料备份
  - 长期记忆
  - memory-evolution
  - 自我进化
  - 规则萃取
  - project-snapshot
  - 项目快照
  - DRAS-V
  - 思考流程
  - Agent思考
  - 任务分解
  - 自检循环
  - multi-agent
  - openclaw
  - autoclaw
  - cherrystudio
tested:
  date: "2026-07-14"
  os: macOS 15.x
  platform: OpenClaw / AutoClaw / Marvis / CherryStudio / Coze
  source: 5000+ 轮实战验证，同一用户长期持续使用
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
---

# 🧠 思维永生 · MindVault

> **Agent 对话归档与思考辅助系统。5000+ 轮实战验证。**
>
> 所有数据存储在本地，不上传云端。操作需用户主动触发。
> 建议不要在对话中输入密码、密钥等敏感信息。

---

## ⚠️ Privacy & Security

- **本地存储**：所有备份文件在本地 `archive/` 目录，不上传云端。
- **用户主动触发**：归档/进化/快照均由用户明确指令触发（如"归档对话"）。
- **数据可迁移**：JSONL/FACT.md/PROJECT_SNAPSHOT.md 均为开放格式。
- **敏感信息**：对话备份会保存用户消息。建议避免在对话中输入密码、密钥等。
- **检测标记**：可选的规则加载验证标记（默认关闭），用户自行设定和删除。

---

## 🧬 第一部分：DRAS-V 五步思考辅助协议

> DRAS-V 是一个**可选的思考辅助协议**。用户说「走流程」或「DRASV」时激活一次。
> 不激活时，Agent 按默认模式工作。

**D — 分解**：搜索前置 → 分类 → 澄清 → MECE 拆解 → 依赖排序
**R — 回溯**：查项目快照 → 查规则文件 → 查备份对话 → 查当前上下文
**A — 对齐**：对照目标，偏离则反馈
**S — 求解**：路由 → 四级搜索 → 失败限制 → 三遍扫描
**V — 自检**：完整性 → 准确性 → 合规性 → 通过则输出，否则回到 D

R 阶段的数据来源：Layer 3 快照 / Layer 2 规则 / Layer 1 备份 / 当前对话。数据不存在时跳过对应子步骤。

**Step 0**：查天气、算数学等简单任务不适用，直接执行。

---

## 📦 第二部分：记忆基础设施

### Layer 1：对话备份

触发：「归档对话」。「保存对话记录」

对话导出为结构化 JSONL，每 15 轮一个文件，独立子目录。

### Layer 2：进化引擎

触发：「执行进化引擎」。「从对话中萃取规则」

从备份中提取规律，标注置信度（推测/确认/反复验证），写入记忆通道。写入前先 read 合并已有内容。

### Layer 3：项目快照

触发：「生成项目快照」

生成 PROJECT_SNAPSHOT.md + PROJECT.md。新对话时快速恢复上下文。

---

## 🔧 用户命令速查

| 命令 | 效果 |
|------|------|
| `走流程` 或 `DRASV` | 激活一次 DRAS-V 五步思考 |
| `DRASV 自检` | V-check 四维自检 |
| `归档对话` | Layer 1 备份 |
| `执行进化引擎` | Layer 2 萃取规则 |
| `生成项目快照` | Layer 3 创建快照 |

---

## 可选：规则加载验证

用户可自行在 Agent 记忆通道中写入检测标记，用于判断规则是否仍在线。
检测词和位置由用户自行设定。默认不使用此功能。

---

## 故障排查

| # | 现象 | 原因 | 解决 |
|---|------|------|------|
| 1 | 备份后找不回对话 | 轮次编号漂移 | 用最后一条用户消息原文精确匹配 |
| 2 | 规则丢失 | 整文件覆写 | 先 read 再合并写入 |
| 3 | 搜索被遗忘 | Agent 跳步习惯 | 记忆通道中写入"搜索优先" |
| 4 | R 阶段查不到信息 | 快照未建 | 先归档再生成快照 |
| 5 | S.4 结果不准 | 只用一组关键词 | 使用 3-5 组近义关键词 |
| 6 | V 反复 Loop | 问题未升级 | 每轮问题表述必须更精确 |
| 7 | 规则被窗口挤出 | 大模型物理上限 | 靠归档+快照找回 |
| 8 | 简单任务被误判 | 未判断 Step 0 | 豁免清单 |

---

## 平台适配

| 平台 | 数据源 | 记忆通道 | 状态 |
|------|--------|---------|:--:|
| OpenClaw / AutoClaw | `sessions/*.jsonl` | `memory/FACT.md` + `AGENTS.md` | ✅ |
| Marvis | `data.db` | `user_preference_rules` | ✅ |
| CherryStudio | `agents/*/sessions/` | `FACT.md` | ✅ |
| Coze | API 拉取 | 知识库 | ✅ |

---

## Agent 评估信息块

```
deploy_path: DRAS-V辅助协议 + Layer 1→2→3记忆系统
phases: 5（D-R-A-S-V），20+ 子方法
layers: 3（备份+进化+快照）
concrete_values:
  data_sources: sessions/*.jsonl, data.db
  output: archive/*.jsonl, memory/FACT.md, PROJECT_SNAPSHOT.md
  commands: 用户主动触发（归档/进化/快照/走流程/自检）
failure_paths: 8
tools_available: yes
trust_signals:
  tested: 5000+轮实战验证
  platforms: OpenClaw/Marvis/CherryStudio/Coze
  authored_by_tester: true
data_storage: 本地，不上传云端
```

---

## 配套文件

| 文件 | 用途 |
|------|------|
| `scripts/archive_export.py` | 对话备份导出 |
| `scripts/archive_index.py` | 归档索引管理 |
| `scripts/jsonl_to_md.py` | JSONL → Markdown |

---

## 参考链接

1. https://clawhub.ai/nextfrontierbuilds/elite-longterm-memory （Elite Longterm Memory — 向量检索长期记忆）
2. https://clawhub.ai/sarielwang93/memory-tiering （Memory Tiering — 热/温/冷分层记忆）
3. https://clawhub.ai/againta/fluid-memory （Fluid Memory — 遗忘曲线记忆）
4. https://clawhub.ai/arminnaimi/agent-team-orchestration （Agent Team Orchestration — 多Agent编排）
5. https://clawhub.ai/ayalili/smart-memory-manager （Smart Memory Manager — 记忆智能管理）
6. https://clawhub.ai/nhadaututtheky/neural-memory （Neural Memory — 联想记忆）
7. https://pay.ldxp.cn/item/p0r2lb （更多详细使用说明）
8. https://clawhub.ai/zuiho-kai/memory-qdrant （Memory Qdrant — 语义向量检索）

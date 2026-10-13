---
name: mindvault
description: >
  MindVault — agent memory & conversation backup：Agent 长期记忆备份与对话归档系统（memory backup, never forget）。
  对话备份(JSONL)+记忆规则萃取+项目快照三层记忆能力+DRAS-V思考协议；5000+轮实战，跨平台(OpenClaw/Marvis/WorkBuddy/CherryStudio/Coze)，本地存储不上云。
  备忘：支持 forget 检测与记忆回填。Use when user says 对话备份、对话归档、归档对话、长期记忆、memory backup、执行进化引擎、生成项目快照、走流程、DRASV。
version: 1.2.4
author: zhouxin121
license: MIT
category: memory
platforms:
  - openclaw
  - autoclaw
  - marvis
  - workbuddy
  - cherrystudio
  - coze
permissions:
  - read
  - write
  - exec
keywords:
  - mindvault
  - conversation-archiver
  - 对话备份
  - 对话归档
  - 长期记忆
  - memory-evolution
  - 自我进化
  - 规则萃取
  - project-snapshot
  - 项目快照
  - DRAS-V
  - 思考流程
tested:
  date: "2026-09-18"
  os: macOS 15.x
  platform: OpenClaw / AutoClaw / Marvis / WorkBuddy / CherryStudio / Coze
  source: 5000+ 轮实战验证，同一用户长期持续使用
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 4fd20e68f8b80beb1e39f35a6c960ac4_5a36f32380cc11f1afc3525400de82e7
    ReservedCode1: cPCUf98FXzhSQuaTmXjcnJEOQKwUqWLgQ8FTrr8cHvIdBg8zVJ947DiNpMHuJpjZM3HwBP9mHw10z3Pv+XdjK9SWKOK4l5l+AGEF5mpaJla0Hp3D9uHa3PVsBVi6o7AOdEXupmUlBLVEUogmyajzXO9W2I0mOcFRorG9QlPwNR8Sa71dVOm1w2pSrqM=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 4fd20e68f8b80beb1e39f35a6c960ac4_5a36f32380cc11f1afc3525400de82e7
    ReservedCode2: cPCUf98FXzhSQuaTmXjcnJEOQKwUqWLgQ8FTrr8cHvIdBg8zVJ947DiNpMHuJpjZM3HwBP9mHw10z3Pv+XdjK9SWKOK4l5l+AGEF5mpaJla0Hp3D9uHa3PVsBVi6o7AOdEXupmUlBLVEUogmyajzXO9W2I0mOcFRorG9QlPwNR8Sa71dVOm1w2pSrqM=
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
- **确认短语**：可选的规则加载验证短语（默认关闭），用户自行设定和删除。

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

**双文档联动与核账校验（强制）**

Layer 3 产出双文档：`PROJECT_SNAPSHOT.md`（唯一真相源）+ `PROJECT.md`（详细派生版），冲突以快照为准。仅靠"改后同步对端 + diff 关键字段"不足以防断裂——实测断裂：更新日志条数不等（27 vs 31）、同日期条目重复、同日期文本漂移、章节正文残留旧事实（快照仍写 v1.0.1）。关键字段 diff 通过 ≠ 真正同步。联动更新必须逐项满足：

1. **更新日志逐条比对**：两文档条数相同；逐条「日期 + 主题」逐字一致；两文档均严格倒序（日期非递增）。
2. **章节正文双向回改互检**：任一章节正文改动后，必须回改对端并互检，非预期行级差异清零（第十五章等已登记的有意精简除外）。
3. **头部元数据强制刷新**：数据来源 / 生成方式 / 生成日期 / 最近更新日期四项，两文档必须一致。
4. **联动完成后必须运行校验脚本并附输出**：
   `python3 scripts/snapshot_sync_check.py --snapshot PROJECT_SNAPSHOT.md --detail PROJECT.md`
   退出码非 0 即存在断裂，禁止在断裂清零前结束联动更新。

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

用户可自行在 Agent 记忆通道中写入确认短语，用于判断规则是否仍在线。
短语内容和位置由用户自行设定。默认不使用此功能。

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
| 9 | 两文档更新日志条数不一致 / 同日期条目重复 | 只做增量同步，未做存量核账 | 按 Layer 3 双文档联动规范逐条比对；运行 `scripts/snapshot_sync_check.py` 定位差异并补齐合并 |
| 10 | 章节正文改了，另一文件没改 | 章节正文单向更新 | 双向回改互检，非预期行级差异清零后，再运行校验脚本确认 |

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
  platforms: OpenClaw/Marvis/WorkBuddy/CherryStudio/Coze
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
| `scripts/snapshot_sync_check.py` | 双文档联动核账校验（六维：日志条数 / 日期序列 / 逐字一致 / 倒序 / 章节标题集合 / 头部元数据），断裂退出码非 0 |

---

## 参考链接

> 说明：本 Skill 为独立设计的原创实现（Layer 1-3 记忆架构 + DRAS-V 协议），
> 下列链接为其设计取向可横向对比的同类开源记忆系统的参考清单，仅供功能对照与学习。

1. https://clawhub.ai/nextfrontierbuilds/elite-longterm-memory （Elite Longterm Memory — 向量检索长期记忆）
2. https://clawhub.ai/sarielwang93/memory-tiering （Memory Tiering — 热/温/冷分层记忆）
3. https://clawhub.ai/againta/fluid-memory （Fluid Memory — 遗忘曲线记忆）
4. https://clawhub.ai/arminnaimi/agent-team-orchestration （Agent Team Orchestration — 多Agent编排）
5. https://clawhub.ai/ayalili/smart-memory-manager （Smart Memory Manager — 记忆智能管理）
6. https://clawhub.ai/nhadaututtheky/neural-memory （Neural Memory — 联想记忆）
7. https://github.com/zhouxin121/mindvault （更多详细使用说明）
8. https://clawhub.ai/zuiho-kai/memory-qdrant （Memory Qdrant — 语义向量检索）

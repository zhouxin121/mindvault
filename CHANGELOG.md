## [修复记录] - 2026-09-11（基于 1.1.0 发布前评审，版本号维持 1.1.0 不变）

- **jsonl_to_md.py**（F1 修复）：`--style full` 下 Tool 消息改为读取 archive_export 实际导出的字段（args_summary / files / urls / errors），修复此前误读 error/summary/result_preview 导致 Tool 内容全丢的问题；同时保留旧字段兼容回退
- **jsonl_to_md.py**（F2 修复）：Agent 工具调用参数优先读取 tool_calls 元素内的 args，回退读取 Agent 条目顶层 key_params，修复参数读取层级错误
- **archive_index.py**（F3 修复）：`search --rounds` 改为解析 exporter 实际写入的 rounds 字符串（如 "16-30"），并新增 parse_rounds 兼容函数，修复按轮次检索失效
- **archive_index.py**（F4 修复）：stats / pending / summary 的消息数统计由不存在的 total_messages 字段改为 entries（JSONL 条数即消息数），修复统计恒 0 或 '?'
- **SKILL.md**：AIGC 块补齐为完整 7 字段（Label/ContentProducer/ProduceID/ReservedCode1/ContentPropagator/PropagateID/ReservedCode2，与 readme1.md 一致）；参考链接前补充原创性说明
- **文案统一软化**：README.md / readme1.md / SKILL.md 中"强制五步思考/每次任务自动执行"统一为"可选五步思考（用户说「走流程」/「DRASV」时激活）"，消除与 SKILL.md"可选协议"的矛盾；"永久归档/永久备份/30 秒恢复"等绝对化表述改为"长期归档/长期备份/快速恢复"；"数据主权完全属于用户"改为"掌握在用户手中"
- **readme1.md**：文末新增"购买与支持"小节，补充链动小铺链接 https://wzyp.cn/item/p0r2lb
- **SKILL.md**：隐私说明明确备份数据写入本地 archive/ 目录（每对话独立子目录，含 _index.json 索引）

## [1.1.0] - 2026-09-11
- 完整版改造：不再区分免费版/赞赏版，三脚本全部功能统一开放
- archive_index.py：解锁 mark/search/summary 完整实现；cmd_mark 加入 B9 if_version 乐观版本令牌 + B15 索引缺失即异常，写时 index_version 自增
- archive_export.py：修复 merge_index 7 参数调用/6 参数定义不匹配的历史 bug（此前 _index.json 只能手动生成）；merge_index 首次写入以实际新文件落盘；写索引携带 index_version，统一索引同步版本号（B9/B15 语义落地）
- jsonl_to_md.py：恢复 --style full 与 --css HTML 输出，支持全部角色渲染
- SKILL.md / readme1.md / _meta.json：版本统一至 1.1.0，去除付费墙文案

## [1.0.0] - 2026-07-14
- 初始发布：MindVault 思维永生系统
- 5000+ 轮实战验证

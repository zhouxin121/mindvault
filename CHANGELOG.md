## [1.1.0] - 2026-09-11
- 完整版改造：不再区分免费版/赞赏版，三脚本全部功能统一开放
- archive_index.py：解锁 mark/search/summary 完整实现；cmd_mark 加入 B9 if_version 乐观版本令牌 + B15 索引缺失即异常，写时 index_version 自增
- archive_export.py：修复 merge_index 7 参数调用/6 参数定义不匹配的历史 bug（此前 _index.json 只能手动生成）；merge_index 首次写入以实际新文件落盘；写索引携带 index_version，统一索引同步版本号（B9/B15 语义落地）
- jsonl_to_md.py：恢复 --style full 与 --css HTML 输出，支持全部角色渲染
- SKILL.md / readme1.md / _meta.json：版本统一至 1.1.0，去除付费墙文案

## [1.0.0] - 2026-07-14
- 初始发布：MindVault 思维永生系统
- 5000+ 轮实战验证

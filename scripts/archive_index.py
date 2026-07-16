#!/usr/bin/env python3
"""MindVault 基础版 — _index.json 管理工具

基础版命令：stats, pending
赞赏版命令：mark, search, summary → https://pay.ldxp.cn/item/p0r2lb


子命令：
  stats      — 统计：文件数 / 总条目 / 轮次 / processed 比例
  pending    — 列出 processed=false 的文件
  mark       — 将指定文件标记为 processed=true
  search     — 按日期/轮次范围搜索文件
  summary    — 输出 JSON 摘要（供 Agent 消费）

用法：
  python archive_index.py <archive_dir> stats
  python archive_index.py <archive_dir> pending
  python archive_index.py <archive_dir> mark "chat_20260703_rounds-16-30.jsonl"
  python archive_index.py <archive_dir> search 2026-07-03
  python archive_index.py <archive_dir> search --rounds 20-40
  python archive_index.py <archive_dir> summary
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def load_index(index_dir: str) -> dict:
    """从 index_dir 往上溯一层找 _index.json，找不到则返回空结构。"""
    # 支持传入子目录（如 archive_dir/conv_label）或 archive_dir 本身
    path = Path(index_dir)
    candidates = [path / "_index.json", path.parent / "_index.json"]
    for p in candidates:
        if p.exists():
            with open(p, "r") as f:
                return json.load(f)
    return {}


def save_index(index_dir: str, data: dict):
    path = Path(index_dir)
    if path.is_dir():
        out = path / "_index.json"
    else:
        out = path.parent / "_index.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cmd_stats(index_dir: str):
    idx = load_index(index_dir)
    files = idx.get("files", [])
    total_entries = sum(f.get("entries", 0) for f in files)
    total_rounds = sum(f.get("round_count", f.get("entries", 0)) for f in files)
    total_msgs = sum(f.get("total_messages", 0) or 0 for f in files)
    processed = sum(1 for f in files if f.get("processed", False))
    pending = len(files) - processed

    print(f"文件数:       {len(files)}")
    print(f"已处理:       {processed}")
    print(f"未处理:       {pending}")
    print(f"总条目数:     {total_entries}")
    print(f"总轮次数:     {total_rounds}")
    print(f"总消息数:     {total_msgs}")
    print(f"处理比例:     {processed/len(files)*100:.1f}%" if files else "0.0%")


def cmd_pending(index_dir: str):
    idx = load_index(index_dir)
    files = idx.get("files", [])
    pending = [f for f in files if not f.get("processed", False)]
    if not pending:
        print("没有未处理的归档文件。")
        return
    print(f"未处理文件数: {len(pending)}")
    if len(pending) >= 5:
        print("⚠️  积压严重，建议执行进化引擎。")
    for f in pending:
        print(f"  - {f.get('file', '?')}  (rounds: {f.get('round_count', f.get('entries', '?'))}, "
              f"messages: {f.get('total_messages', '?')}, "
              f"date: {f.get('date', '?')})")


def cmd_mark(index_dir: str, filename: str):
    idx = load_index(index_dir)
    files = idx.get("files", [])
    found = False
    for f in files:
        if f.get("file") == filename:
            f["processed"] = True
            f["processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            found = True
            break
    if not found:
        print(f"错误：未找到文件 '{filename}'")
        sys.exit(1)
    idx["files"] = files
    save_index(index_dir, idx)
    print(f"已标记: {filename}")


def cmd_search(index_dir: str, date_str: str = None, rounds_range: str = None):
    idx = load_index(index_dir)
    files = idx.get("files", [])
    results = files

    if date_str:
        results = [f for f in results if f.get("date", "") == date_str]

    if rounds_range:
        try:
            lo, hi = rounds_range.split("-")
            lo, hi = int(lo), int(hi)
        except ValueError:
            print("错误：rounds 范围格式应为 '20-40'")
            sys.exit(1)
        results = [
            f for f in results
            if lo <= f.get("round_start", 0) <= hi
            or lo <= f.get("round_end", 0) <= hi
        ]

    if not results:
        print("无匹配结果。")
        return
    for f in results:
        print(f"{f.get('file', '?')}  date={f.get('date','?')} "
              f"rounds=[{f.get('round_start','?')}-{f.get('round_end','?')}] "
              f"entries={f.get('entries','?')}  msgs={f.get('total_messages','?')} "
              f"processed={f.get('processed',False)}")


def cmd_summary(index_dir: str):
    idx = load_index(index_dir)
    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_count": len(idx.get("files", [])),
        "total_entries": sum(f.get("entries", 0) for f in idx.get("files", [])),
        "total_messages": sum(f.get("total_messages", 0) or 0 for f in idx.get("files", [])),
        "processed_count": sum(1 for f in idx.get("files", []) if f.get("processed", False)),
        "pending_count": sum(1 for f in idx.get("files", []) if not f.get("processed", False)),
        "date_range": {
            "earliest": min((f.get("date", "9999") for f in idx.get("files", []) if f.get("date")), default=None),
            "latest": max((f.get("date", "0000") for f in idx.get("files", []) if f.get("date")), default=None),
        },
        "pending_files": [
            f.get("file") for f in idx.get("files", []) if not f.get("processed", False)
        ],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    index_dir = sys.argv[1]
    cmd = sys.argv[2]
    args = sys.argv[3:]

    if cmd == "stats":
        cmd_stats(index_dir)
    elif cmd == "pending":
        cmd_pending(index_dir)
    elif cmd == "mark":
        if not args:
            print("用法: archive_index.py <dir> mark <filename>")
            sys.exit(1)
        print("🚫 赞赏版功能：mark。基础版支持 stats 和 pending。\n获取完整版：https://pay.ldxp.cn/item/p0r2lb")
        sys.exit(1)
    elif cmd == "search":
        date_str = args[0] if args else None
        rounds_range = None
        if len(args) >= 2 and args[0] == "--rounds":
            rounds_range = args[1]
        print("🚫 赞赏版功能：search。基础版支持 stats 和 pending。\n获取完整版：https://pay.ldxp.cn/item/p0r2lb")
        sys.exit(1)
    elif cmd == "summary":
        print("🚫 赞赏版功能：summary。基础版支持 stats 和 pending。\n获取完整版：https://pay.ldxp.cn/item/p0r2lb")
        sys.exit(1)
    else:
        print(f"未知子命令: {cmd}")
        sys.exit(1)

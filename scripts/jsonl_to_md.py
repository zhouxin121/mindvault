#!/usr/bin/env python3
"""MindVault 基础版 — JSONL → Markdown

基础版：仅 --style minimal，最多处理 3 文件
赞赏版：--style full + --css + 无限制 → https://pay.ldxp.cn/item/p0r2lb


用法：
  python jsonl_to_md.py <jsonl_file> [--style minimal|full] [--output <md_file>]
  python jsonl_to_md.py <jsonl_file> --css <css_template_file>

默认输出到 stdout，--output 写入文件。
--style minimal：仅用户+Agent 消息（默认）
--style full：全部角色（system/tool/scheduled）
--css：可选 HTML+CSS 输出模板（将 Markdown 嵌入 HTML 模板）
"""

import json
import sys
from datetime import datetime
from pathlib import Path


ROLE_ICONS = {
    "user": "👤",
    "agent": "🤖",
    "tool": "🔧",
    "system": "⚙️",
    "scheduled": "⏰",
}


def render_jsonl(filepath: str, style: str = "minimal") -> str:
    lines = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            role = entry.get("role", "?")
            if style == "minimal" and role not in ("user", "agent"):
                continue

            icon = ROLE_ICONS.get(role, "❓")
            ts = entry.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    ts_fmt = dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    ts_fmt = ts
            else:
                ts_fmt = ""

            lines.append(f"### {icon} {role.upper()}  {ts_fmt}\n")

            if role == "user":
                content = entry.get("content", "")
                attachments = entry.get("attachments", [])
                if attachments:
                    att_lines = ["**附件：**"]
                    for att in attachments:
                        att_lines.append(f"- [{att.get('type','file')}] `{att.get('path','?')}`")
                    lines.append("\n".join(att_lines) + "\n")
                if content:
                    lines.append(f"{content}\n")

            elif role == "agent":
                reasoning = entry.get("reasoning", "")
                if reasoning:
                    lines.append(f"> *推理思路：* {reasoning}\n")
                content = entry.get("content", "")
                if content:
                    trunc = entry.get("content_truncated", False)
                    if trunc:
                        content += "\n\n*（内容已截断）*"
                    lines.append(f"{content}\n")
                tools = entry.get("tool_calls", [])
                if tools:
                    lines.append("**工具调用：**\n")
                    for t in tools:
                        lines.append(f"- `{t.get('name','?')}`")
                        params = t.get("key_params", {})
                        if params:
                            lines.append(f"  - {json.dumps(params, ensure_ascii=False)}")
                    lines.append("")

            elif role == "tool":
                tool_name = entry.get("tool_name", "?")
                lines.append(f"**工具：** `{tool_name}`\n")
                error = entry.get("error")
                if error:
                    lines.append(f"⚠️ 错误：{error}\n")
                else:
                    summary = entry.get("summary", "")
                    if summary:
                        lines.append(f"{summary}\n")
                result = entry.get("result_preview", "")
                if result:
                    lines.append(f"```\n{result}\n```\n")

            elif role == "system":
                content = entry.get("content", "") or entry.get("origin", "")
                lines.append(f"```\n{content}\n```\n")

            elif role == "scheduled":
                summary = entry.get("summary", "")
                lines.append(f"{summary}\n")

            lines.append("---\n")

    return "\n".join(lines)


def main():
    print("📖 MindVault 基础版：仅 minimal 模式。完整功能见赞赏版。")

    import argparse
    parser = argparse.ArgumentParser(description="JSONL 归档 → Markdown 阅读器")
    parser.add_argument("jsonl_file", help="JSONL 归档文件路径")
    parser.add_argument("--style", choices=["minimal"], default="minimal",
                        help="渲染风格：minimal=仅用户+Agent，full=全部角色")
    parser.add_argument("--output", "-o", help="输出 Markdown 文件路径")
    # --css 为赞赏版功能
    args = parser.parse_args()

    md = render_jsonl(args.jsonl_file, style=args.style)

    if args.output:
        out_path = Path(args.output)
        if args.css:
            css_content = Path(args.css).read_text(encoding="utf-8")
            html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>对话归档 — {Path(args.jsonl_file).stem}</title>
<style>
{css_content}
</style>
</head>
<body>
<div class="conversation">
{md.replace(chr(10), chr(10)+"  ")}
</div>
</body>
</html>"""
            out_path.write_text(html, encoding="utf-8")
        else:
            out_path.write_text(md, encoding="utf-8")
        print(f"已写入: {out_path}")
    else:
        print(md)


if __name__ == "__main__":
    main()

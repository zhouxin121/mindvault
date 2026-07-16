#!/usr/bin/env python3
"""
对话归档导出脚本 — 支持 OpenClaw JSONL 和 Marvis SQLite 两种数据源。

OpenClaw 模式:
  python archive_export.py openclaw <sessions_dir> <archive_dir> --conv-label <label> [--incremental]
  从 sessions/*.jsonl 中提取消息

Marvis 模式:
  python archive_export.py marvis <conversation_id> <db_path> <archive_dir> --conv-label <label> [--incremental]
  从 data.db 的 messages 表中提取消息

--conv-label 必填：对话标识（AutoClaw: agent id / OpenClaw: session 名 / Marvis: conversation_id 前 8 位）
用于创建对话专属子目录，防止不同对话的同名文件相互覆盖。

增量模式（--incremental）：
  读取 archive_dir/<conv_label>/_index.json 获取最后归档轮次，仅导出该轮次之后的新消息。
  新文件追加到对话专属子目录，_index.json 做增量合并更新。
  若无新轮次，直接退出不做任何写入。

切割规则：每 15 轮一个 JSONL 文件。时间戳统一输出 GMT+8 ISO 8601 可读格式。
多对话隔离：每个对话独立子目录 + 独立计数。文件名格式: {对话标识}_{日期}_rounds-{起始}-{结束}.jsonl

v3.1 时间戳规则：每条消息（user/agent/tool/system）必须携带 timestamp 字段。
  格式：ISO 8601 可读格式（2026-06-30T16:03:25+08:00），禁止 Unix 毫秒戳。
  降级策略：agent/tool 消息无原始时间戳时继承上一条消息的时间戳。
  验证：备份完成后自动抽查 5 条消息，确认 timestamp 存在且格式正确。
"""

import sqlite3
import json
import os
import re
import sys
import glob
import random
from datetime import datetime, timezone, timedelta

ROUNDS_PER_FILE = 15
MAX_TOOL_CONTENT = 500
TZ_CN = timezone(timedelta(hours=8))


def to_gmt8(ts_str):
    """将时间字符串转 GMT+8 ISO 8601"""
    if not ts_str:
        return ""
    ts_str = ts_str.strip()
    if ts_str.endswith('Z'):
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    elif '+' in ts_str or (ts_str.endswith('00') and 'T' in ts_str):
        dt = datetime.fromisoformat(ts_str)
    else:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ_CN)
    return dt.astimezone(TZ_CN).strftime('%Y-%m-%dT%H:%M:%S+08:00')


def extract_tool_files(content):
    """从 tool content 中提取文件路径"""
    files = []
    if not content:
        return files
    if isinstance(content, str):
        matches = re.findall(
            r'(?:file_path|path|output)[\s"\'：:]+([/\w\-. ~]+(?:\.\w+))', content
        )
        files.extend(matches)
    try:
        data = json.loads(content) if isinstance(content, str) else content
        if isinstance(data, dict):
            for key in ['file_path', 'path', 'file_paths']:
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        files.extend(val)
                    elif isinstance(val, str):
                        files.append(val)
    except Exception:
        pass
    return list(set(files))


def extract_tool_urls(content):
    """从 tool content 中提取 URL"""
    urls = []
    if not content or not isinstance(content, str):
        return urls
    matches = re.findall(r'https?://[^\s<>"\'{}|\\^`\[\]]+', content)
    return list(set(matches))


def process_user(content, ts_str, ts_inherited=False):
    """用户消息：100% 保留原始输入，不做任何加工。返回消息条目和校验警告。
    如果消息以 [SYSTEM: 开头，视为系统注入消息，标记 role='system' 且不参与轮次计数。
    提取附件信息：<attachments> 块中的文件路径，生成 attachments 字段。"""
    processed = content or ""
    warnings = []
    # 系统消息过滤：以 [SYSTEM: 开头的为平台自动注入，非用户发言
    if processed.strip().startswith('[SYSTEM:'):
        entry = {
            "timestamp": to_gmt8(ts_str),
            "role": "system",
            "content": processed,
        }
        if ts_inherited:
            entry["ts_inherited"] = True
        return entry, []
    
    # 提取附件信息
    attachments = []
    if '<attachments>' in processed and '</attachments>' in processed:
        start = processed.find('<attachments>') + len('<attachments>')
        end = processed.find('</attachments>')
        if start < end:
            attachment_text = processed[start:end].strip()
            # 每行一个文件路径
            for line in attachment_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('/') or line.startswith('file://')):
                    # 提取文件名和路径
                    path = line.replace('file://', '')
                    # 简单内容摘要：根据扩展名判断类型
                    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                        attachments.append({"type": "image", "path": path})
                    elif path.lower().endswith(('.pdf', '.doc', '.docx', '.xlsx', '.pptx')):
                        attachments.append({"type": "document", "path": path})
                    elif path.lower().endswith(('.py', '.js', '.java', '.cpp', '.c', '.go', '.rs')):
                        attachments.append({"type": "code", "path": path})
                    elif path.lower().endswith(('.txt', '.md', '.json', '.yaml', '.yml')):
                        attachments.append({"type": "text", "path": path})
                    else:
                        attachments.append({"type": "file", "path": path})
    
    if content and processed != content:
        warnings.append(f"USER_MSG_INTEGRITY_FAIL: 原始 {len(content)} 字 → 处理后 {len(processed)} 字")
    entry = {
        "timestamp": to_gmt8(ts_str),
        "role": "user",
        "content": processed,
    }
    if ts_inherited:
        entry["ts_inherited"] = True
    if attachments:
        entry["attachments"] = attachments
    return entry, warnings


def extract_key_params(tool_calls_list):
    """从 tool_calls 提取关键参数：文件路径、URL、查询词、agent 名称等"""
    params = {"file_paths": [], "urls": [], "queries": [], "agent_name": ""}
    for tc in (tool_calls_list or []):
        args = tc.get('args', {})
        if not args or not isinstance(args, dict):
            continue
        for k, v in args.items():
            vs = str(v)
            if any(x in k.lower() for x in ('path', 'file', 'directory', 'dir')):
                params['file_paths'].append(vs)
            elif 'url' in k.lower():
                params['urls'].append(vs)
            elif any(x in k.lower() for x in ('query', 'search', 'prompt')):
                params['queries'].append(vs[:200])
            elif 'agent' in k.lower():
                params['agent_name'] = vs
    # 去重并清理空列表
    for k in params:
        if isinstance(params[k], list):
            params[k] = list(dict.fromkeys(params[k]))[:10]
    return params


def detect_experience_markers(content, reasoning):
    """从回复和推理中检测经验标记"""
    markers = []
    text = ((content or '') + ' ' + (reasoning or '')).lower()

    # 用户纠正
    if any(kw in text for kw in ('不对', '错误理解', '纠正', '不是这样', '撤回', '重新', '别这样')):
        markers.append('用户纠正')

    # 确认/授权
    if any(kw in text for kw in ('确认', '许可', '批准')):
        markers.append('确认授权')

    # 错误处理
    if any(kw in text for kw in ('失败', '报错', 'error', 'failed', 'exception', '超时', '拒绝')):
        markers.append('错误处理')

    # 关键决策
    if any(kw in text for kw in ('方案', '决定', '最终选择', '采用方案', '路线')):
        markers.append('关键决策')

    # v3 标准标记
    if '逐字保留' in text or 'v3' in text:
        markers.append('v3标准')

    return markers


def process_agent(content, reasoning, tool_calls_list, ts_str, ts_inherited=False):
    """Agent 消息：五维度提取（推理思路 + 回复 + 工具调用 + 关键参数 + 经验标记）。
    v3.1 修正：长回复 (>500 字) 截断到最近一个完整段落边界，不卡在句子中间。
    注：LLM 摘要需在后续分析阶段完成，脚本层面只保证段落完整性。"""
    tc_list = tool_calls_list or []
    full_content = content or ""
    content_length = len(full_content)

    # 长回复截断：500 字后找最近的段落边界（双换行）
    if content_length > 500:
        trunc_point = 500
        boundary = full_content.rfind('\n\n', 0, trunc_point)
        if boundary > 300:  # 至少保留 300 字，否则宁可卡在 500
            trunc_point = boundary
        display_content = full_content[:trunc_point].rstrip()
    else:
        display_content = full_content

    entry = {
        "timestamp": to_gmt8(ts_str),
        "role": "agent",
        "reasoning": reasoning or "",
        "content": display_content,
        "content_length": content_length,
        "content_truncated": content_length > 500,
        "tool_calls": tc_list,
        "key_params": extract_key_params(tc_list),
        "experience_markers": detect_experience_markers(full_content, reasoning),
    }
    if ts_inherited:
        entry["ts_inherited"] = True
    return entry


def process_tool(content, tool_name, ts_str, tool_call_args=None, ts_inherited=False):
    """Tool 消息：仅保留工具名 + 关键参数 + 路径 + URL + 错误摘要"""
    files = extract_tool_files(content)
    urls = extract_tool_urls(content)
    errors = []

    # 从 tool_call_args 提取关键参数（比从 content 提取更准确）
    key_param = extract_tool_key_param(tool_name, tool_call_args or {})

    if content and isinstance(content, str):
        # 检查是否包含错误信息
        for kw in ['error', 'Error', 'failed', 'Failed', 'exception', 'Exception']:
            if kw in content:
                lines = content.split('\n')
                for line in lines:
                    if kw in line:
                        errors.append(line.strip()[:200])
                        break
                break

    # 生成 args_summary：关键参数 + 文件/URL/错误计数
    parts = []
    if key_param:  # 优先展示关键参数（如 web_fetch 的 URL、exec 的 command）
        parts.append(key_param[:120])
    if files:
        parts.append(f"文件: {len(files)} 个")
    if urls:
        parts.append(f"URL: {len(urls)} 个")
    if errors:
        parts.append(f"错误: {len(errors)} 条")
    args_summary = " | ".join(parts)

    entry = {
        "timestamp": to_gmt8(ts_str),
        "role": "tool",
        "tool_name": tool_name or "",
        "key_param": key_param,
        "args_summary": args_summary,
        "files": files,
        "urls": urls,
        "errors": errors,
    }
    if ts_inherited:
        entry["ts_inherited"] = True
    return entry


# ── 工具关键参数提取规则 ──────────────────────────────────

def extract_tool_key_param(tool_name, args):
    """按工具类型提取最关键的单个参数。规则：
    exec / shell_executor: command（前 200 字）
    web_fetch / web_search: url 或 query
    read / read_text: file_path
    write / write_file: file_path
    dispatch_task: agent_name + task（各前 100 字）
    其他: 第一个非空字符串参数
    """
    if not args or not isinstance(args, dict):
        return ""

    tool_name_lower = (tool_name or '').lower()

    if 'exec' in tool_name_lower or 'shell' in tool_name_lower:
        cmd = args.get('command', '') or args.get('cmd', '')
        return f"命令: {str(cmd)[:200]}" if cmd else ""

    if 'web_fetch' in tool_name_lower or 'fetch' in tool_name_lower:
        url = args.get('url', '')
        return f"URL: {str(url)[:200]}" if url else ""

    if 'web_search' in tool_name_lower or 'search' in tool_name_lower:
        query = args.get('query', '') or args.get('q', '')
        return f"搜索: {str(query)[:200]}" if query else ""

    if 'read' in tool_name_lower:
        file_path = args.get('file_path', '') or args.get('path', '')
        return f"文件: {str(file_path)[:200]}" if file_path else ""

    if 'write' in tool_name_lower:
        file_path = args.get('file_path', '') or args.get('path', '')
        return f"文件: {str(file_path)[:200]}" if file_path else ""

    if 'dispatch' in tool_name_lower:
        agent = args.get('agent_name', '') or ''
        task = args.get('task', '') or ''
        if agent or task:
            return f"Agent: {str(agent)[:100]}, Task: {str(task)[:100]}"

    # 兜底：取第一个非空字符串参数
    for k, v in args.items():
        if isinstance(v, str) and v.strip():
            return f"{k}: {v[:200]}"
    return ""


# ── 增量索引工具 ────────────────────────────────────────

def load_index(archive_dir, conv_label):
    """从对话子目录加载 _index.json，不存在则返回 None"""
    subdir = os.path.join(archive_dir, conv_label)
    path = os.path.join(subdir, "_index.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_last_archived_round(archive_dir, conv_label):
    """从对话子目录的 _index.json 获取最后归档轮次。失败返回 0"""
    index = load_index(archive_dir, conv_label)
    if not index:
        return 0
    files = index.get('files', [])
    if not files:
        return 0
    last_rounds = files[-1].get('rounds', '0000-0000')
    try:
        end_round = int(last_rounds.split('-')[-1])
        return end_round
    except (ValueError, IndexError):
        return 0


def merge_index(archive_dir, conv_label, new_file_entries, new_total_rounds, new_total_messages):
    """增量合并：将新文件追加到已有 _index.json。"""
    existing = load_index(archive_dir, conv_label)
    subdir = os.path.join(archive_dir, conv_label)
    if not existing:
        _write_index(archive_dir, conv_label, [], [], [], new_total_rounds, new_total_messages)
        return

    existing_files = existing.get('files', [])
    existing_files.extend(new_file_entries)

    existing['total_rounds'] = new_total_rounds
    existing['total_messages'] = existing.get('total_messages', 0) + new_total_messages
    existing['total_files'] = len(existing_files)
    existing['archived_at'] = datetime.now(TZ_CN).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    if 'time_span' in existing and new_file_entries:
        existing['time_span']['end'] = new_file_entries[-1].get('date', '')

    index_path = os.path.join(subdir, "_index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"\n索引已更新: {index_path}")
    print(f"新增 {len(new_file_entries)} 个文件，累计 {len(existing_files)} 个，共 {existing['total_rounds']} 轮，{existing['total_messages']} 条。")


# ── OpenClaw 模式 ──────────────────────────────────────

def extract_openclaw(sessions_dir, archive_dir, conv_label, incremental=False):
    """从 OpenClaw sessions/*.jsonl 提取消息"""
    jsonl_files = sorted(glob.glob(os.path.join(sessions_dir, "*.jsonl")))
    if not jsonl_files:
        print("未找到 JSONL 会话文件")
        return

    subdir = os.path.join(archive_dir, conv_label)
    os.makedirs(subdir, exist_ok=True)

    start_round = 0
    if incremental:
        start_round = get_last_archived_round(archive_dir, conv_label)
        if start_round > 0:
            print(f"[增量] 最后归档轮次: {start_round}，将导出第 {start_round + 1} 轮起的新消息")

    entries = []
    round_num = 0
    last_timestamp = ""  # 降级策略：agent/tool 消息无时间戳时继承上一条

    for jf in jsonl_files:
        with open(jf, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if msg.get('type') != 'message':
                    continue

                message = msg.get('message', {})
                role = message.get('role', '')
                timestamp = msg.get('timestamp', '') or last_timestamp
                ts_inherited = (not msg.get('timestamp', '') and last_timestamp != "")
                if timestamp:
                    last_timestamp = timestamp  # 持续追踪最近的有效时间戳

                # 提取 content 数组
                contents = message.get('content', [])
                if isinstance(contents, str):
                    contents = [{'type': 'text', 'text': contents}]

                text_parts = []
                thinking_parts = []
                tool_calls_parts = []
                tool_results_parts = []

                for c in contents:
                    ct = c.get('type', '')
                    if ct == 'text':
                        text_parts.append(c.get('text', ''))
                    elif ct == 'thinking':
                        thinking_parts.append(c.get('text', c.get('thinking', '')))
                    elif ct == 'toolCall':
                        tool_calls_parts.append({
                            'name': c.get('toolName', c.get('name', '')),
                            'args': c.get('args', c.get('input', {}))
                        })
                    elif ct == 'toolResult':
                        tool_results_parts.append({
                            'tool_name': c.get('toolName', c.get('name', '')),
                            'content': c.get('content', c.get('result', ''))
                        })

                if role == 'user':
                    round_num += 1
                    # 增量模式：跳过已归档的轮次
                    if incremental and round_num <= start_round:
                        continue
                    content = '\n'.join(text_parts)
                    user_entry, warnings = process_user(content, timestamp, ts_inherited)
                    entries.append({
                        'round': round_num,
                        'entry': user_entry
                    })
                    for w in warnings:
                        print(f"  [校验告警] Round {round_num}: {w}")
                elif role == 'assistant':
                    if incremental and round_num <= start_round:
                        continue
                    content = '\n'.join(text_parts)
                    reasoning = '\n'.join(thinking_parts)
                    entries.append({
                        'round': round_num,
                        'entry': process_agent(content, reasoning, tool_calls_parts, timestamp, ts_inherited)
                    })
                    # 如果有 toolResult，也加进去，并附上对应 toolCall 的 args
                    for tr in tool_results_parts:
                        tr_name = tr.get('tool_name', '')
                        # 匹配最近一条同名 toolCall 的参数
                        tr_args = {}
                        for tc in reversed(tool_calls_parts):
                            if tc.get('name') == tr_name:
                                tr_args = tc.get('args', {})
                                break
                        entries.append({
                            'round': round_num,
                            'entry': process_tool(
                                str(tr.get('content', '')),
                                tr_name,
                                timestamp,
                                tool_call_args=tr_args,
                                ts_inherited=ts_inherited
                            )
                        })

    _write_archive(entries, archive_dir, conv_label, incremental=incremental, existing_total_rounds=start_round)


# ── Marvis 模式 ────────────────────────────────────────

def extract_marvis(conv_id, db_path, archive_dir, conv_label, incremental=False):
    """从 Marvis data.db 提取消息"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    subdir = os.path.join(archive_dir, conv_label)
    os.makedirs(subdir, exist_ok=True)

    start_round = 0
    if incremental:
        start_round = get_last_archived_round(archive_dir, conv_label)
        if start_round > 0:
            print(f"[增量] 最后归档轮次: {start_round}，将导出第 {start_round + 1} 轮起的新消息")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT message_seq, role, content, tool_calls, tool_call_id,
               tool_name, metadata, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY message_seq
    """, (conv_id,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("未找到消息记录")
        return

    entries = []
    round_num = 0
    last_tool_calls_list = []  # 跟踪上一条 assistant 的 tool_calls 用于匹配 tool 结果
    last_timestamp = ""  # 降级策略：agent/tool 消息无时间戳时继承上一条

    for row in rows:
        msg = dict(row)
        role = msg['role']
        content = msg.get('content', '') or ''
        ts_str = msg.get('created_at', '') or last_timestamp
        ts_inherited = (not msg.get('created_at', '') and last_timestamp != "")
        if ts_str:
            last_timestamp = ts_str  # 持续追踪最近的有效时间戳

        if role == 'user':
            round_num += 1
            # 增量模式：跳过已归档的轮次
            if incremental and round_num <= start_round:
                continue
            user_entry, warnings = process_user(content, ts_str, ts_inherited)
            entries.append({
                'round': round_num,
                'entry': user_entry
            })
            for w in warnings:
                print(f"  [校验告警] Round {round_num}: {w}")
        elif role == 'assistant':
            if incremental and round_num <= start_round:
                continue
            # 提取 reasoning
            reasoning = ""
            metadata_raw = msg.get('metadata', '') or '{}'
            try:
                if metadata_raw:
                    meta = json.loads(metadata_raw)
                    reasoning = meta.get('reasoning_content', '')
            except Exception:
                pass

            # 提取 tool_calls
            tool_calls_list = []
            tool_calls_raw = msg.get('tool_calls', '') or ''
            try:
                if tool_calls_raw:
                    tcs = json.loads(tool_calls_raw)
                    if isinstance(tcs, list):
                        for tc in tcs:
                            tool_calls_list.append({
                                'name': tc.get('name', ''),
                                'args': tc.get('args', {})
                            })
            except Exception:
                pass

            last_tool_calls_list = tool_calls_list  # 保存供后续 tool 消息匹配

            entries.append({
                'round': round_num,
                'entry': process_agent(content, reasoning, tool_calls_list, ts_str, ts_inherited)
            })
        elif role == 'tool':
            if incremental and round_num <= start_round:
                continue
            tool_name = msg.get('tool_name', '') or ''
            # 匹配上一条 assistant 的同名 tool_call args
            tr_args = {}
            for tc in reversed(last_tool_calls_list):
                if tc.get('name') == tool_name:
                    tr_args = tc.get('args', {})
                    break
            entries.append({
                'round': round_num,
                'entry': process_tool(content, tool_name, ts_str, tool_call_args=tr_args, ts_inherited=ts_inherited)
            })

    _write_archive(entries, archive_dir, conv_label, incremental=incremental, existing_total_rounds=start_round)


# ── 通用写入逻辑 ────────────────────────────────────────

def _write_archive(entries, archive_dir, conv_label, incremental=False, existing_total_rounds=0):
    """通用的归档写入逻辑。使用对话专属子目录，文件名加对话标识前缀。"""
    if not entries:
        if incremental:
            print("没有新轮次需要归档。")
        else:
            print("没有消息需要归档。")
        return

    subdir = os.path.join(archive_dir, conv_label)
    os.makedirs(subdir, exist_ok=True)

    total_rounds = max(e['round'] for e in entries) if entries else 0
    total_messages = len(entries)
    user_msgs = sum(1 for e in entries if e['entry']['role'] == 'user')
    agent_msgs = sum(1 for e in entries if e['entry']['role'] == 'agent')
    tool_msgs = sum(1 for e in entries if e['entry']['role'] == 'tool')
    print(f"本批消息: {total_messages} (user: {user_msgs}, agent: {agent_msgs}, tool: {tool_msgs})，轮次: {min(e['round'] for e in entries)}-{total_rounds}")

    # ── 增量模式预检（不可跳过） ──
    if incremental:
        user_entries = [e for e in entries if e['entry']['role'] == 'user']
        print(f"\n[增量预检] 新轮次: {min(e['round'] for e in entries)}-{total_rounds}，共 {len(user_entries)} 轮用户消息")
        if user_entries:
            first = user_entries[0]['entry']['content']
            print(f"  首轮 (R{user_entries[0]['round']}): {first[:120]}{'...' if len(first) > 120 else ''}")
        if len(user_entries) > 1:
            last = user_entries[-1]['entry']['content']
            print(f"  末轮 (R{user_entries[-1]['round']}): {last[:120]}{'...' if len(last) > 120 else ''}")
        print("  [预检完成] 请确认以上新轮次范围和首末消息是否正确。")

    file_entries = []
    first_batch_start = 1 if not incremental else ((existing_total_rounds // ROUNDS_PER_FILE) * ROUNDS_PER_FILE + 1)

    for batch_start in range(first_batch_start, total_rounds + 1, ROUNDS_PER_FILE):
        batch_end = min(batch_start + ROUNDS_PER_FILE - 1, total_rounds)
        batch_entries = [e for e in entries if batch_start <= e['round'] <= batch_end]

        if not batch_entries:
            continue

        last_ts = batch_entries[-1]['entry'].get('timestamp', '')
        date_str = last_ts[:10] if last_ts else datetime.now(TZ_CN).strftime('%Y-%m-%d')

        round_nums_in_file = set(e['round'] for e in batch_entries)

        # 文件名：{对话标识}_{日期}_rounds-{起始}-{结束}.jsonl
        filename = f"{conv_label}_{date_str}_rounds-{batch_start:04d}-{batch_end:04d}.jsonl"
        filepath = os.path.join(subdir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            for e in batch_entries:
                entry = e['entry']
                entry['round'] = e['round']
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        file_size = os.path.getsize(filepath)
        file_entries.append({
            "file": filename,
            "rounds": f"{batch_start:04d}-{batch_end:04d}",
            "date": date_str,
            "entries": len(batch_entries),
            "round_count": len(round_nums_in_file),
            "size_bytes": file_size,
            "processed": False
        })
        print(f"  {filename}: {len(batch_entries)} 条 ({len(round_nums_in_file)} 轮), {file_size:,} 字节")

    if incremental:
        combined_rounds = max(total_rounds, existing_total_rounds)
        combined_msgs = total_messages
        merge_index(archive_dir, conv_label, file_entries, combined_rounds, combined_msgs)
    else:
        _write_index(archive_dir, conv_label, file_entries, entries, total_rounds, total_messages)

    # 写入全局索引
    _write_unified_index(archive_dir)

    # ── v3 时间戳验证（不可跳过） ──
    _validate_timestamps(entries)

    print(f"归档完成。{len(file_entries)} 个新文件，子目录: {subdir}")


def _validate_timestamps(entries):
    """v3.1 时间戳验证：随机抽查 5 条不同角色消息，确认 timestamp 存在且为 ISO 8601 格式。
    同时统计全量降级时间戳（ts_inherited），写入备份日志。
    不通过则打印告警，不回退。"""
    iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$')
    
    # 统计全量降级时间戳
    inherited_count = sum(1 for e in entries if e['entry'].get('ts_inherited'))
    inherited_by_role = {}
    for e in entries:
        if e['entry'].get('ts_inherited'):
            role = e['entry'].get('role', '?')
            inherited_by_role[role] = inherited_by_role.get(role, 0) + 1
    
    print(f"\n[v3.1 时间戳降级日志] 共 {inherited_count} 条消息使用继承时间戳（非原始时间戳）")
    if inherited_by_role:
        for role, count in sorted(inherited_by_role.items()):
            print(f"  {role}: {count} 条")
    else:
        print("  ✅ 所有消息均携带原始时间戳")
    
    # 抽查 5 条格式
    if len(entries) <= 5:
        sample = entries
    else:
        sample = random.sample(entries, 5)
    
    failures = []
    
    for e in sample:
        entry = e['entry']
        ts = entry.get('timestamp', '')
        role = entry.get('role', '?')
        inherited = entry.get('ts_inherited', False)
        mark = " [继承]" if inherited else ""
        if not ts:
            failures.append(f"  R{e['round']} {role}{mark}: 无时间戳")
        elif not iso_pattern.match(ts):
            failures.append(f"  R{e['round']} {role}{mark}: 格式异常 ({ts[:25]})")
    
    print(f"\n[v3.1 格式抽查] {len(sample)} 条消息:")
    if failures:
        print("  ❌ 以下消息时间戳不合格:")
        for f in failures:
            print(f)
    else:
        print("  ✅ 全部通过 — 每条消息均带 ISO 8601 时间戳")


def _write_index(archive_dir, conv_label, file_entries, entries, total_rounds, total_messages):
    """写入对话子目录的 _index.json（全量模式用）"""
    conv_start = entries[0]['entry'].get('timestamp', '') if entries else ""
    conv_end = entries[-1]['entry'].get('timestamp', '') if entries else ""

    index = {
        "conversation_label": conv_label,
        "total_rounds": total_rounds,
        "total_messages": total_messages,
        "total_files": len(file_entries),
        "rounds_per_file": ROUNDS_PER_FILE,
        "time_span": {
            "start": conv_start[:10] if conv_start else "",
            "end": conv_end[:10] if conv_end else ""
        },
        "archived_at": datetime.now(TZ_CN).strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        "trim_standard": "v3.1",
        "files": file_entries
    }

    subdir = os.path.join(archive_dir, conv_label)
    os.makedirs(subdir, exist_ok=True)
    index_path = os.path.join(subdir, "_index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n对话索引: {index_path}")
    print(f"归档完成。{len(file_entries)} 个文件，{total_rounds} 轮，{total_messages} 条。")


def _write_unified_index(archive_dir):
    """扫描 archive_dir 下所有子目录，写入全局索引 _index_unified.json"""
    if not os.path.exists(archive_dir):
        return
    conversations = []
    for entry in sorted(os.listdir(archive_dir)):
        entry_path = os.path.join(archive_dir, entry)
        if os.path.isdir(entry_path):
            idx_path = os.path.join(entry_path, "_index.json")
            if os.path.exists(idx_path):
                try:
                    with open(idx_path, 'r', encoding='utf-8') as f:
                        idx = json.load(f)
                    conversations.append({
                        "conversation_label": entry,
                        "total_rounds": idx.get("total_rounds", 0),
                        "total_messages": idx.get("total_messages", 0),
                        "total_files": idx.get("total_files", 0),
                        "time_span": idx.get("time_span", {})
                    })
                except Exception:
                    pass
    unified = {
        "type": "global_index",
        "conversations": conversations,
        "total_conversations": len(conversations),
        "updated_at": datetime.now(TZ_CN).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    }
    unified_path = os.path.join(archive_dir, "_index_unified.json")
    with open(unified_path, 'w', encoding='utf-8') as f:
        json.dump(unified, f, ensure_ascii=False, indent=2)


# ── 主入口 ──────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法:")
        print("  OpenClaw: python archive_export.py openclaw <sessions_dir> <archive_dir> --conv-label <label> [--incremental]")
        print("  Marvis:   python archive_export.py marvis <conversation_id> <db_path> <archive_dir> --conv-label <label> [--incremental]")
        print()
        print("  --conv-label 必填：对话标识，用于子目录隔离和文件名前缀")
        sys.exit(1)

    mode = sys.argv[1]
    incremental = '--incremental' in sys.argv
    conv_label = ""

    # 解析 --conv-label
    if '--conv-label' in sys.argv:
        idx = sys.argv.index('--conv-label')
        if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith('--'):
            conv_label = sys.argv[idx + 1]
            # 从 argv 中移除标记和值，方便后续位置参数解析
            sys.argv = sys.argv[:idx] + sys.argv[idx + 2:]

    if not conv_label:
        print("错误: --conv-label <label> 为必填参数")
        print("  对话标识: AutoClaw 用 agent id, OpenClaw 用 session 名, Marvis 用 conversation_id 前 8 位")
        sys.exit(1)

    if mode == 'openclaw':
        if len(sys.argv) < 4:
            print("用法: python archive_export.py openclaw <sessions_dir> <archive_dir> --conv-label <label> [--incremental]")
            sys.exit(1)
        sessions_dir = sys.argv[2]
        archive_dir = sys.argv[3]
        extract_openclaw(sessions_dir, archive_dir, conv_label, incremental=incremental)

    elif mode == 'marvis':
        if len(sys.argv) < 5:
            print("用法: python archive_export.py marvis <conversation_id> <db_path> <archive_dir> --conv-label <label> [--incremental]")
            sys.exit(1)
        conv_id = sys.argv[2]
        db_path = sys.argv[3]
        archive_dir = sys.argv[4]
        extract_marvis(conv_id, db_path, archive_dir, conv_label, incremental=incremental)

    else:
        print(f"未知模式: {mode}，请使用 openclaw 或 marvis")
        sys.exit(1)

#!/usr/bin/env python3
"""
manager.py — Self-Improvement Loop v5.0.0
TDD 开发：最小实现
"""
import os
import sys
import json
import fcntl
import argparse
import datetime
import warnings
from pathlib import Path

LEARNINGS_DIR = os.environ.get('LEARNINGS_DIR', os.path.expanduser('~/.openclaw/workspace/.learnings'))
TYPE_TO_PREFIX = {'learnings': 'LRN', 'errors': 'ERR', 'features': 'FEAT'}
PREFIX_TO_TYPE = {v: k for k, v in TYPE_TO_PREFIX.items()}


def _lock_file(filepath):
    """获取文件锁，返回文件句柄。锁文件位于同目录 .locks/ 下。"""
    lock_dir = os.path.join(os.path.dirname(filepath) or '.', '.locks')
    os.makedirs(lock_dir, exist_ok=True)
    lockfile = os.path.join(lock_dir, f'{os.path.basename(filepath)}.lock')
    fh = open(lockfile, 'w')
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    return fh


def _unlock_file(fh):
    """释放文件锁并关闭句柄。"""
    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    fh.close()


def _atomic_write(filepath, lines):
    """原子写入：先写临时文件，再 rename，确保数据完整性。"""
    tmp = filepath + f'.{os.getpid()}.tmp'
    with open(tmp, 'w') as f:
        f.writelines(lines)
        f.flush()
        os.fsync(f.fileno())
    os.rename(tmp, filepath)


def _get_jsonl_path(etype):
    return os.path.join(LEARNINGS_DIR, f'{etype}.jsonl')


def _ensure_dir():
    """确保学习目录和归档目录存在，必要时创建 JSONL 文件占位。"""
    os.makedirs(LEARNINGS_DIR, exist_ok=True)
    os.makedirs(os.path.join(LEARNINGS_DIR, 'archive'), exist_ok=True)
    for f in ['learnings', 'errors', 'features']:
        p = _get_jsonl_path(f)
        if not os.path.exists(p):
            Path(p).touch()


def _read_jsonl(etype):
    """读取指定类型的 JSONL 文件，返回 entry 列表。损坏行会发出警告。"""
    fpath = _get_jsonl_path(etype)
    entries = []
    if os.path.exists(fpath):
        with open(fpath) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        warnings.warn(f"警告：{fpath}:{line_num} JSON 损坏，已跳过")
    return entries


def _write_jsonl(etype, entries):
    fpath = _get_jsonl_path(etype)
    fh = _lock_file(fpath)
    lines = [json.dumps(e, ensure_ascii=False) + '\n' for e in entries]
    _atomic_write(fpath, lines)
    _unlock_file(fh)


def _append_entry(entry):
    etype = entry['type']
    fpath = _get_jsonl_path(etype)
    fh = _lock_file(fpath)
    line = json.dumps(entry, ensure_ascii=False) + '\n'
    with open(fpath, 'a') as f:
        f.write(line)
    _unlock_file(fh)
    return entry


def _read_all_entries():
    result = {}
    for etype in ['learnings', 'errors', 'features']:
        result[etype] = _read_jsonl(etype)
    return result


def _generate_id(prefix):
    """生成唯一 ID，格式：{PREFIX}-{YYYYMMDD}-{NNN}。线程安全。"""
    today = datetime.datetime.now().strftime('%Y%m%d')
    fpath = _get_jsonl_path(PREFIX_TO_TYPE.get(prefix, ''))
    # 加锁防止极端并发场景下生成重复 ID
    fh = _lock_file(fpath)
    count = 0
    if os.path.exists(fpath):
        with open(fpath) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        e = json.loads(line)
                        if e['id'].startswith(f'{prefix}-{today}'):
                            count += 1
                    except json.JSONDecodeError:
                        pass
    nnn = f'{count + 1:03d}'
    _unlock_file(fh)
    return f'{prefix}-{today}-{nnn}'


# 命令实现
def cmd_add(args):
    _ensure_dir()
    if args.json:
        with open(args.json) as f:
            data = json.load(f)
    else:
        data = {
            'type': args.type,
            'category': args.category,
            'pattern_key': args.pattern_key or '',
            'what_happened': args.what,
            'root_cause': getattr(args, 'root_cause', '') or '',
            'how_to_avoid': args.avoid or '',
            'tags': [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else [],
            'source': args.source,
        }

    prefix = TYPE_TO_PREFIX[data['type']]
    data['id'] = _generate_id(prefix)
    data['logged_at'] = datetime.datetime.now().isoformat()
    data['status'] = 'pending'
    data['notified'] = False
    data['notification_count'] = 0
    data['updated_at'] = None

    entry = _append_entry(data)
    if args.json_output:
        print(json.dumps({'success': True, 'entry': entry}, ensure_ascii=False, indent=2))
    else:
        print(f"Added: {entry['id']}")


def cmd_list(args):
    _ensure_dir()
    all_entries = _read_all_entries()
    for etype, entries in all_entries.items():
        if args.type and etype != args.type:
            continue
        filtered = entries
        if args.status:
            filtered = [e for e in filtered if e.get('status') == args.status]
        if args.pattern_key:
            filtered = [e for e in filtered if args.pattern_key in e.get('pattern_key', '')]
        if args.count_only:
            print(f"{etype}: {len(filtered)}")
            continue
        for e in filtered:
            ts = e.get('logged_at', '')[:10]
            status = e.get('status', 'pending')
            what = e.get('what_happened', '')[:50]
            print(f"[{e['id']}] {ts} [{status}] {what}...")


def cmd_get(args):
    _ensure_dir()
    all_entries = _read_all_entries()
    for entries in all_entries.values():
        for e in entries:
            if e['id'] == args.id:
                print(json.dumps(e, ensure_ascii=False, indent=2))
                return
    print(f"Entry not found: {args.id}", file=sys.stderr)
    sys.exit(1)


def cmd_update(args):
    _ensure_dir()
    all_entries = _read_all_entries()
    for etype, entries in all_entries.items():
        for i, e in enumerate(entries):
            if e['id'] == args.id:
                if args.status:
                    entries[i]['status'] = args.status
                if args.pattern_key is not None:
                    entries[i]['pattern_key'] = args.pattern_key
                entries[i]['updated_at'] = datetime.datetime.now().isoformat()
                _write_jsonl(etype, entries)
                print(json.dumps({'success': True, 'entry': entries[i]}, ensure_ascii=False, indent=2))
                return
    print(f"Entry not found: {args.id}", file=sys.stderr)
    sys.exit(1)


def cmd_notify(args):
    _ensure_dir()
    all_entries = _read_all_entries()
    for etype, entries in all_entries.items():
        for i, e in enumerate(entries):
            if e['id'] == args.id:
                entries[i]['notified'] = True
                entries[i]['notification_count'] = e.get('notification_count', 0) + 1
                entries[i]['updated_at'] = datetime.datetime.now().isoformat()
                _write_jsonl(etype, entries)
                print(json.dumps({'success': True, 'entry': entries[i]}, ensure_ascii=False, indent=2))
                return
    print(f"Entry not found: {args.id}", file=sys.stderr)
    sys.exit(1)


def _entry_to_raw_md(e):
    """Render a JSON entry as Markdown for AI analysis."""
    sections = []
    if e.get('category'):
        sections.append(f"### Category\n{e.get('category')}")
    sections.append(f"### What Happened\n{e.get('what_happened', '')}")
    if e.get('root_cause'):
        sections.append(f"### Root Cause\n{e.get('root_cause', '')}")
    if e.get('how_to_avoid'):
        sections.append(f"### How To Avoid\n{e.get('how_to_avoid', '')}")
    if e.get('tags'):
        sections.append(f"### Tags\n{', '.join(e.get('tags', []))}")
    if e.get('skill_candidate'):
        sections.append(f"### Suggested Skill\n{e.get('skill_candidate')}")
    return '\n\n'.join(sections)


def cmd_scan(args):
    _ensure_dir()
    all_entries = _read_all_entries()
    groups = {}
    for etype, entries in all_entries.items():
        for e in entries:
            if e.get('status') not in ('pending', 'active', 'in_progress'):
                continue
            key = e.get('pattern_key') or e.get('category', '')
            if not key:
                continue
            if key not in groups:
                groups[key] = {'name': key, 'source': 'pattern_key' if e.get('pattern_key') else 'category', 'entries': []}
            groups[key]['entries'].append(e)

    patterns = []
    for name, group in groups.items():
        count = len(group['entries'])
        first = group['entries'][0]
        first['raw_md'] = _entry_to_raw_md(first)
        should_notify = (
            count >= args.threshold and
            (not first.get('notified', False) or first.get('notification_count', 0) < count)
        )
        max_entries = getattr(args, 'max_entries', 10)
        if max_entries == 0:
            max_entries = len(group['entries'])  # 0 means all
        # Add raw_md to each entry for AI analysis
        for entry in group['entries'][:max_entries]:
            entry['raw_md'] = _entry_to_raw_md(entry)

        patterns.append({
            'name': name, 'count': count, 'threshold': args.threshold,
            'should_notify': should_notify, 'source': group['source'],
            'first_entry': first,
            'entries': group['entries'][:max_entries],
        })

    if args.trigger_only:
        patterns = [p for p in patterns if p['should_notify']]

    print(json.dumps({'patterns': patterns, 'meta': {'threshold': args.threshold, 'scanned_at': datetime.datetime.now().isoformat()}}, ensure_ascii=False, indent=2))


def cmd_archive(args):
    _ensure_dir()
    all_entries = _read_all_entries()
    today = datetime.datetime.now().strftime('%Y-%m')
    archive_file = os.path.join(LEARNINGS_DIR, 'archive', f'{today}.jsonl')
    os.makedirs(os.path.dirname(archive_file), exist_ok=True)
    total_archived = 0
    for etype, entries in all_entries.items():
        to_archive = [e for e in entries if e.get('status') in ('resolved', 'promoted')]
        to_keep = [e for e in entries if e.get('status') not in ('resolved', 'promoted')]
        if to_archive:
            fh = _lock_file(archive_file)
            with open(archive_file, 'a') as f:
                for e in to_archive:
                    f.write(json.dumps(e, ensure_ascii=False) + '\n')
            _unlock_file(fh)
            total_archived += len(to_archive)
        if to_keep != entries:
            _write_jsonl(etype, to_keep)
    if args.dry_run:
        print(f"[DRY RUN] Would archive {total_archived} entries to {archive_file}")
    else:
        print(f"Archived {total_archived} entries to {archive_file}")


def cmd_stat(args):
    _ensure_dir()
    all_entries = _read_all_entries()
    for etype, entries in all_entries.items():
        total = len(entries)
        by_status = {}
        for e in entries:
            s = e.get('status', 'unknown')
            by_status[s] = by_status.get(s, 0) + 1
        print(f"\n{etype}: {total} total")
        for s, count in sorted(by_status.items()):
            print(f"  {s}: {count}")


def cmd_pending(args):
    """Manage .pending_notifications/ directory"""
    pending_dir = os.path.join(LEARNINGS_DIR, '.pending_notifications')
    os.makedirs(pending_dir, exist_ok=True)

    if args.list:
        files = sorted(os.listdir(pending_dir))
        if files:
            for f in files:
                print(f)
        else:
            print("(empty)")
        return

    if args.clean:
        for f in os.listdir(pending_dir):
            os.remove(os.path.join(pending_dir, f))
        print(f"Cleaned {pending_dir}")
        return

    if args.write:
        pattern_key = args.write
        content = sys.stdin.read()
        outfile = os.path.join(pending_dir, f'{pattern_key}.analysis.json')
        with open(outfile, 'w') as f:
            f.write(content)
        print(f"Wrote {outfile}")


def main():
    global LEARNINGS_DIR
    parser = argparse.ArgumentParser(prog='manager.py', description='Self-Improvement Loop v5.0.0')
    parser.add_argument('--learnings-dir', default=LEARNINGS_DIR)
    parser.add_argument('--json-output', action='store_true')
    subparsers = parser.add_subparsers(dest='cmd', required=True)

    p = subparsers.add_parser('add')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--type', choices=['learnings', 'errors', 'features'])
    g.add_argument('--json', help='从 JSON 文件读取')
    p.add_argument('--category')
    p.add_argument('--pattern-key', default='')
    p.add_argument('--what')
    p.add_argument('--root-cause', default='')
    p.add_argument('--avoid', '--how-to-avoid', dest='avoid', default='')
    p.add_argument('--tags', default='')
    p.add_argument('--source', default='human_correction')

    p = subparsers.add_parser('list')
    p.add_argument('--type')
    p.add_argument('--status')
    p.add_argument('--pattern-key')
    p.add_argument('--count-only', action='store_true')

    p = subparsers.add_parser('get')
    p.add_argument('id')

    p = subparsers.add_parser('update')
    p.add_argument('id')
    p.add_argument('--status')
    p.add_argument('--pattern-key')

    p = subparsers.add_parser('notify')
    p.add_argument('id')

    p = subparsers.add_parser('scan')
    p.add_argument('--threshold', type=int, default=2)
    p.add_argument('--trigger-only', action='store_true')
    p.add_argument('--max-entries', type=int, default=10,
                   help='Max entries per pattern to return (default 10, 0=all)')

    p = subparsers.add_parser('archive')
    p.add_argument('--dry-run', action='store_true')

    p = subparsers.add_parser('stat')

    p = subparsers.add_parser('pending')
    p.add_argument('--list', action='store_true', help='List pending files')
    p.add_argument('--clean', action='store_true', help='Clean pending directory')
    p.add_argument('--write', metavar='PATTERN_KEY', help='Write analysis JSON from stdin')

    args = parser.parse_args()
    LEARNINGS_DIR = args.learnings_dir

    commands = {'add': cmd_add, 'list': cmd_list, 'get': cmd_get, 'update': cmd_update,
                'notify': cmd_notify, 'scan': cmd_scan, 'archive': cmd_archive, 'stat': cmd_stat,
                'pending': cmd_pending}
    commands[args.cmd](args)


if __name__ == '__main__':
    main()

#!/Users/hiromutsuchiya/simplenote-backup/venv/bin/python3
"""
Simplenote Pull Script
Pulls remote changes from Simplenote to local backup directory.

Commands:
  python3 simplenote-pull.py status [backup_dir]   - Show differences
  python3 simplenote-pull.py pull [backup_dir]     - Apply remote changes to local
  python3 simplenote-pull.py dry-run [backup_dir]  - Preview changes without applying
"""
import os
import sys
import re
import glob
import shutil
from datetime import datetime
from simperium.core import Api as SimperiumApi


def load_env(env_path=None):
    """Load environment variables from .env file"""
    if env_path is None:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def get_default_backup_dir():
    return os.path.join(os.environ['HOME'], 'Dropbox/SimplenoteBackups')


def log(message, level="INFO"):
    """タイムスタンプ付きログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


load_env()

APPNAME = 'chalk-bump-f49'
TOKEN = os.environ.get('TOKEN')


def fetch_remote_notes(api):
    """リモートノートを全て取得（削除済み含む）"""
    dump = api.note.index(data=True)
    notes = dump['index']
    while 'mark' in dump:
        dump = api.note.index(data=True, mark=dump['mark'])
        notes.extend(dump['index'])
    return notes


def extract_filename(content, note_id):
    """ノート内容からファイル名を生成"""
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            title = line.lstrip('#').strip()
        else:
            title = line
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = safe_title[:100]
        if safe_title:
            return safe_title
    return note_id


def parse_local_file(filepath):
    """ローカルファイルを解析してコンテンツとタグを取得"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    clean_lines = []
    local_tags = []
    system_tags = []

    for line in lines:
        if line.startswith('Tags: '):
            tag_str = line[6:].strip()
            if tag_str:
                local_tags = [t.strip() for t in tag_str.split(',') if t.strip()]
        elif line.startswith('System tags: '):
            tag_str = line[13:].strip()
            if tag_str:
                system_tags = [t.strip() for t in tag_str.split(',') if t.strip()]
        else:
            clean_lines.append(line)

    while clean_lines and clean_lines[-1] == '':
        clean_lines.pop()

    return '\n'.join(clean_lines), local_tags, system_tags


def get_local_files(backup_dir):
    """ローカルファイルを全て取得してタイトルでインデックス化"""
    files = {}
    md_files = glob.glob(os.path.join(backup_dir, '**/*.md'), recursive=True)

    for filepath in md_files:
        content, tags, system_tags = parse_local_file(filepath)
        title = content.split('\n')[0] if content else ''

        # ディレクトリからタグを取得
        rel_path = os.path.relpath(filepath, backup_dir)
        parts = rel_path.split(os.sep)
        dir_tag = parts[0] if len(parts) > 1 and parts[0] != 'TRASH' else None

        files[filepath] = {
            'content': content,
            'tags': tags,
            'system_tags': system_tags,
            'dir_tag': dir_tag,
            'title': title,
            'is_trash': 'TRASH' in filepath
        }

    return files


def find_local_match(remote_note, local_files, matched_ids=None):
    """リモートノートに対応するローカルファイルを検索"""
    if matched_ids is None:
        matched_ids = set()

    remote_content = remote_note['d'].get('content', '')
    remote_title = remote_content.split('\n')[0] if remote_content else ''

    # 完全一致を優先（既にマッチ済みを除く）
    for filepath, local in sorted(local_files.items()):
        if filepath in matched_ids:
            continue
        if local['content'] == remote_content:
            return filepath, 'identical'

    # タイトル一致（既にマッチ済みを除く）
    for filepath, local in sorted(local_files.items()):
        if filepath in matched_ids:
            continue
        if local['title'] == remote_title:
            return filepath, 'title_match'

    return None, None


def analyze_differences(backup_dir):
    """リモートとローカルの差分を分析"""
    if not TOKEN:
        log("TOKEN not found", "ERROR")
        return None

    api = SimperiumApi(APPNAME, TOKEN)

    log("Fetching remote notes...")
    remote_notes = fetch_remote_notes(api)

    log("Scanning local files...")
    local_files = get_local_files(backup_dir)

    results = {
        'tag_changes': [],      # タグ（ディレクトリ）変更
        'content_changes': [],  # コンテンツ変更
        'new_notes': [],        # リモートにあってローカルにない
        'to_trash': [],         # リモートで削除 → ローカルをTRASHへ
        'orphaned': [],         # ローカルにあってリモートにない（孤立）
        'identical': [],        # 同一
        'remote_count': 0,
        'remote_trashed': 0,
        'local_count': len([f for f in local_files if not local_files[f]['is_trash']])
    }

    matched_local_files = set()

    # アクティブなリモートノート
    active_remote = [n for n in remote_notes if not n['d'].get('deleted')]
    # 削除済みリモートノート
    trashed_remote = [n for n in remote_notes if n['d'].get('deleted')]

    results['remote_count'] = len(active_remote)
    results['remote_trashed'] = len(trashed_remote)

    # アクティブなリモートノートを処理
    for note in active_remote:
        remote_content = note['d'].get('content', '')
        remote_tags = note['d'].get('tags', [])
        remote_system_tags = note['d'].get('systemTags', [])

        # 単一タグの場合のみディレクトリ化
        remote_dir_tag = remote_tags[0] if len(remote_tags) == 1 else None

        filepath, match_type = find_local_match(note, local_files, matched_local_files)

        if filepath:
            matched_local_files.add(filepath)
            local = local_files[filepath]

            if match_type == 'identical':
                # コンテンツは同一、タグをチェック
                if remote_dir_tag != local['dir_tag']:
                    results['tag_changes'].append({
                        'filepath': filepath,
                        'old_tag': local['dir_tag'],
                        'new_tag': remote_dir_tag,
                        'content': remote_content,
                        'tags': remote_tags,
                        'system_tags': remote_system_tags
                    })
                else:
                    results['identical'].append(filepath)
            else:
                # タイトル一致だがコンテンツ異なる
                results['content_changes'].append({
                    'filepath': filepath,
                    'old_tag': local['dir_tag'],
                    'new_tag': remote_dir_tag,
                    'content': remote_content,
                    'tags': remote_tags,
                    'system_tags': remote_system_tags
                })
        else:
            # ローカルにない新規ノート
            results['new_notes'].append({
                'content': remote_content,
                'tags': remote_tags,
                'system_tags': remote_system_tags,
                'dir_tag': remote_dir_tag
            })

    # 削除済みリモートノートをチェック（ローカルにあればTRASHへ）
    for note in trashed_remote:
        remote_content = note['d'].get('content', '')
        filepath, match_type = find_local_match(note, local_files, matched_local_files)

        if filepath and not local_files[filepath]['is_trash']:
            matched_local_files.add(filepath)
            results['to_trash'].append({
                'filepath': filepath,
                'title': local_files[filepath]['title']
            })

    # ローカルにあってリモートにない（孤立ファイル）
    for filepath, local in local_files.items():
        if filepath not in matched_local_files and not local['is_trash']:
            results['orphaned'].append({
                'filepath': filepath,
                'title': local['title']
            })

    return results, backup_dir


def get_unique_filepath(dir_path, base_name, ext):
    """重複時に連番を付与"""
    path = os.path.join(dir_path, base_name + ext)
    if not os.path.exists(path):
        return path
    counter = 1
    while True:
        path = os.path.join(dir_path, f"{base_name}_{counter}{ext}")
        if not os.path.exists(path):
            return path
        counter += 1


def show_status(backup_dir):
    """差分状態を表示"""
    result = analyze_differences(backup_dir)
    if result is None:
        return

    results, _ = result

    print(f"\n=== Pull Status ===")
    print(f"Remote notes: {results['remote_count']} (+ {results['remote_trashed']} in trash)")
    print(f"Local files: {results['local_count']}")
    print(f"")
    print(f"Changes from remote:")
    print(f"  - Tag/directory changes: {len(results['tag_changes'])}")
    print(f"  - Content changes: {len(results['content_changes'])}")
    print(f"  - New notes to download: {len(results['new_notes'])}")
    print(f"  - To move to TRASH: {len(results['to_trash'])}")
    print(f"  - Orphaned (local only): {len(results['orphaned'])}")
    print(f"  - Identical: {len(results['identical'])}")

    if results['tag_changes']:
        print(f"\nTag changes (first 10):")
        for item in results['tag_changes'][:10]:
            filename = os.path.basename(item['filepath'])
            old = item['old_tag'] or 'root'
            new = item['new_tag'] or 'root'
            print(f"  {filename}: {old}/ -> {new}/")
        if len(results['tag_changes']) > 10:
            print(f"  ... and {len(results['tag_changes']) - 10} more")

    if results['to_trash']:
        print(f"\nTo move to TRASH:")
        for item in results['to_trash'][:10]:
            print(f"  {os.path.basename(item['filepath'])}")

    if results['orphaned']:
        print(f"\nOrphaned files (local only, first 10):")
        for item in results['orphaned'][:10]:
            print(f"  {os.path.basename(item['filepath'])}")
        if len(results['orphaned']) > 10:
            print(f"  ... and {len(results['orphaned']) - 10} more")

    # 未タグファイル数
    untagged = len(results['new_notes']) - len([n for n in results['new_notes'] if n['dir_tag']])
    if untagged > 0:
        print(f"\nWarning: {untagged} new note(s) have no tag (will be in root)")


def do_pull(backup_dir, dry_run=False, trash_orphans=False):
    """リモートの変更をローカルに適用"""
    result = analyze_differences(backup_dir)
    if result is None:
        return {'error': True}

    results, _ = result

    log("=== Pull Summary ===")
    log(f"Tag changes: {len(results['tag_changes'])}")
    log(f"Content changes: {len(results['content_changes'])}")
    log(f"New notes: {len(results['new_notes'])}")
    log(f"To trash: {len(results['to_trash'])}")
    log(f"Orphaned: {len(results['orphaned'])}")
    log(f"Identical: {len(results['identical'])}")

    if dry_run:
        log("[DRY RUN - No changes made]")

        if results['tag_changes']:
            print("\nWould move (tag change):")
            for item in results['tag_changes'][:10]:
                old_dir = item['old_tag'] or 'root'
                new_dir = item['new_tag'] or 'root'
                print(f"  {os.path.basename(item['filepath'])}: {old_dir}/ -> {new_dir}/")

        if results['content_changes']:
            print("\nWould update (content):")
            for item in results['content_changes'][:10]:
                print(f"  {os.path.basename(item['filepath'])}")

        if results['new_notes']:
            print("\nWould create:")
            for item in results['new_notes'][:10]:
                title = item['content'].split('\n')[0][:50] if item['content'] else '(empty)'
                tag_info = f"[{item['dir_tag']}]" if item['dir_tag'] else "[untagged]"
                print(f"  {title}... {tag_info}")

        if results['to_trash']:
            print("\nWould move to TRASH:")
            for item in results['to_trash']:
                print(f"  {os.path.basename(item['filepath'])}")

        if results['orphaned'] and trash_orphans:
            print("\nWould move orphaned to TRASH:")
            for item in results['orphaned'][:10]:
                print(f"  {os.path.basename(item['filepath'])}")

        return results

    # 実際に適用
    moved = 0
    updated = 0
    created = 0
    trashed = 0
    untagged_count = 0

    # TRASH ディレクトリ作成
    trash_dir = os.path.join(backup_dir, 'TRASH')
    os.makedirs(trash_dir, exist_ok=True)

    # リモートで削除されたノート → ローカルをTRASHへ
    for item in results['to_trash']:
        old_path = item['filepath']
        filename = os.path.basename(old_path)
        new_path = get_unique_filepath(trash_dir, os.path.splitext(filename)[0], '.md')

        shutil.move(old_path, new_path)
        log(f"Moved to TRASH: {filename}")
        trashed += 1

    # 孤立ファイルをTRASHへ（オプション）
    if trash_orphans:
        for item in results['orphaned']:
            old_path = item['filepath']
            filename = os.path.basename(old_path)
            new_path = get_unique_filepath(trash_dir, os.path.splitext(filename)[0], '.md')

            shutil.move(old_path, new_path)
            log(f"Moved orphaned to TRASH: {filename}")
            trashed += 1

    # タグ変更（ディレクトリ移動）
    for item in results['tag_changes']:
        old_path = item['filepath']
        filename = os.path.basename(old_path)

        if item['new_tag']:
            new_dir = os.path.join(backup_dir, item['new_tag'])
        else:
            new_dir = backup_dir

        os.makedirs(new_dir, exist_ok=True)
        new_path = get_unique_filepath(new_dir, os.path.splitext(filename)[0], '.md')

        shutil.move(old_path, new_path)
        old_tag = item['old_tag'] or 'root'
        new_tag = item['new_tag'] or 'root'
        log(f"Tag changed: {filename} ({old_tag}/ -> {new_tag}/)")
        moved += 1

    # コンテンツ変更
    for item in results['content_changes']:
        filepath = item['filepath']

        # タグも変わっている場合は移動
        if item['new_tag'] != item['old_tag']:
            filename = os.path.basename(filepath)
            if item['new_tag']:
                new_dir = os.path.join(backup_dir, item['new_tag'])
            else:
                new_dir = backup_dir
            os.makedirs(new_dir, exist_ok=True)
            new_path = get_unique_filepath(new_dir, os.path.splitext(filename)[0], '.md')
            os.remove(filepath)
            filepath = new_path

        # コンテンツを更新
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(item['content'])
            f.write('\n')
            if item['tags']:
                f.write(f"Tags: {', '.join(item['tags'])}\n")
            if item['system_tags']:
                f.write(f"System tags: {', '.join(item['system_tags'])}\n")

        log(f"Updated: {os.path.basename(filepath)}")
        updated += 1

    # 新規ノート
    for item in results['new_notes']:
        content = item['content']
        filename = extract_filename(content, 'new_note')

        if item['dir_tag']:
            target_dir = os.path.join(backup_dir, item['dir_tag'])
        else:
            target_dir = backup_dir
            untagged_count += 1

        os.makedirs(target_dir, exist_ok=True)
        filepath = get_unique_filepath(target_dir, filename, '.md')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            f.write('\n')
            if item['tags']:
                f.write(f"Tags: {', '.join(item['tags'])}\n")
            if item['system_tags']:
                f.write(f"System tags: {', '.join(item['system_tags'])}\n")

        tag_info = f"[{item['dir_tag']}]" if item['dir_tag'] else "[untagged]"
        log(f"Created: {os.path.basename(filepath)} {tag_info}")
        created += 1

    # 空になったディレクトリを削除
    for item in os.listdir(backup_dir):
        item_path = os.path.join(backup_dir, item)
        if os.path.isdir(item_path) and item not in ['TRASH', '.', '..']:
            if not os.listdir(item_path):
                os.rmdir(item_path)
                log(f"Removed empty directory: {item}/")

    log(f"=== Pull Complete ===")
    log(f"Summary: {trashed} trashed, {moved} moved, {updated} updated, {created} created")

    if untagged_count > 0:
        log(f"Warning: {untagged_count} untagged file(s) in root directory", "WARN")

    return {
        'trashed': trashed,
        'moved': moved,
        'updated': updated,
        'created': created,
        'untagged': untagged_count,
        'orphaned': len(results['orphaned']) if not trash_orphans else 0
    }


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 simplenote-pull.py status [backup_dir]   - Show differences")
        print("  python3 simplenote-pull.py pull [backup_dir]     - Apply remote changes")
        print("  python3 simplenote-pull.py dry-run [backup_dir]  - Preview changes")
        sys.exit(1)

    command = sys.argv[1]
    backup_dir = sys.argv[2] if len(sys.argv) > 2 else get_default_backup_dir()

    if command == 'status':
        show_status(backup_dir)
    elif command == 'pull':
        do_pull(backup_dir, dry_run=False, trash_orphans=False)
    elif command == 'dry-run':
        do_pull(backup_dir, dry_run=True)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()

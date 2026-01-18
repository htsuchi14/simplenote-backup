#!/Users/hiromutsuchiya/simplenote-backup/venv/bin/python3
"""
Simplenote Import Script
Imports local .md files to Simplenote via Simperium API.

Commands:
  python3 simplenote-import.py status [backup_dir]   - Show sync status
  python3 simplenote-import.py sync [backup_dir]     - Sync all changes
  python3 simplenote-import.py dry-run [backup_dir]  - Preview changes
  python3 simplenote-import.py json [backup_dir]     - JSON output for Claude
"""
import os
import sys
import glob
import json
import uuid
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


load_env()

APPNAME = 'chalk-bump-f49'  # Simplenote
TOKEN = os.environ.get('TOKEN')


def fetch_existing_notes(api):
    """既存ノートを全て取得"""
    dump = api.note.index(data=True)
    notes = dump['index']
    while 'mark' in dump:
        dump = api.note.index(data=True, mark=dump['mark'])
        notes.extend(dump['index'])
    return notes


def parse_local_file(filepath):
    """ローカルファイルを解析してコンテンツとタグを取得"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    clean_lines = []
    local_tags = []

    for line in lines:
        if line.startswith('Tags: '):
            tag_str = line[6:].strip()
            if tag_str:
                local_tags = [t.strip() for t in tag_str.split(',') if t.strip()]
        elif line.startswith('System tags: '):
            continue
        else:
            clean_lines.append(line)

    # 末尾の空行を除去
    while clean_lines and clean_lines[-1] == '':
        clean_lines.pop()

    return '\n'.join(clean_lines), local_tags


def find_existing_note(content, existing, matched_ids=None):
    """既存ノートと比較して、同一または類似を判定

    matched_ids: 既にマッチ済みのノートIDのセット（重複タイトル対策）
    """
    if matched_ids is None:
        matched_ids = set()

    # IDでソートして処理順序を安定化
    for note in sorted(existing, key=lambda n: n['id']):
        if note['d'].get('deleted'):
            continue
        # 既にマッチ済みのノートはスキップ
        if note['id'] in matched_ids:
            continue

        existing_content = note['d'].get('content', '')
        existing_tags = note['d'].get('tags', [])

        if existing_content == content:
            return ('identical', note['id'], existing_tags)
        # 先頭行（タイトル）が同じなら更新候補
        if existing_content.split('\n')[0] == content.split('\n')[0]:
            return ('update', note['id'], existing_tags)
    return ('create', None, [])


def get_tag_from_path(filepath, import_dir):
    """ファイルパスからタグを取得（ディレクトリ名）"""
    parent_dir = os.path.basename(os.path.dirname(filepath))
    base_import_dir = os.path.basename(import_dir.rstrip('/'))
    if parent_dir and parent_dir not in [base_import_dir, 'TRASH']:
        return parent_dir
    return None


def analyze_sync_status(import_dir):
    """同期状態を分析"""
    if not TOKEN:
        print("Error: TOKEN not found. Set TOKEN in .env file or environment variable.")
        return None

    api = SimperiumApi(APPNAME, TOKEN)

    print("Fetching existing notes from Simplenote...", file=sys.stderr)
    existing_notes = fetch_existing_notes(api)

    # .mdファイルを検索（TRASHディレクトリを除外）、ソートして処理順序を安定化
    md_files = sorted([f for f in glob.glob(os.path.join(import_dir, '**/*.md'), recursive=True)
                if '/TRASH/' not in f])

    results = {
        'to_create': [],
        'to_update': [],
        'tag_changes': [],
        'identical': [],
        'local_count': len(md_files),
        'remote_count': len([n for n in existing_notes if not n['d'].get('deleted')])
    }

    # 既にマッチしたノートIDを追跡（重複タイトル対策）
    matched_ids = set()

    for filepath in md_files:
        content, local_tags = parse_local_file(filepath)
        dir_tag = get_tag_from_path(filepath, import_dir)

        # ディレクトリからのタグを優先
        effective_tags = [dir_tag] if dir_tag else local_tags

        action, note_id, remote_tags = find_existing_note(content, existing_notes, matched_ids)

        if action == 'create':
            results['to_create'].append({
                'filepath': filepath,
                'tags': effective_tags
            })
        elif action == 'update':
            # マッチしたノートIDを記録
            matched_ids.add(note_id)
            results['to_update'].append({
                'filepath': filepath,
                'note_id': note_id,
                'tags': effective_tags
            })
        else:  # identical
            # マッチしたノートIDを記録
            matched_ids.add(note_id)
            # タグが変わっているかチェック
            if set(effective_tags) != set(remote_tags):
                results['tag_changes'].append({
                    'filepath': filepath,
                    'note_id': note_id,
                    'old_tags': remote_tags,
                    'new_tags': effective_tags
                })
            else:
                results['identical'].append(filepath)

    return results, api, existing_notes


def do_sync(import_dir, dry_run=False, batch_size=50):
    """同期を実行 (bulk_post APIを使用)"""
    import time

    result = analyze_sync_status(import_dir)
    if result is None:
        return

    results, api, existing_notes = result

    print(f"\n=== Sync Summary ===")
    print(f"Local files: {results['local_count']}")
    print(f"Remote notes: {results['remote_count']}")
    print(f"To create: {len(results['to_create'])}")
    print(f"To update (content): {len(results['to_update'])}")
    print(f"To update (tags only): {len(results['tag_changes'])}")
    print(f"Identical: {len(results['identical'])}")

    if dry_run:
        print("\n[DRY RUN - No changes made]")
        if results['to_create']:
            print("\nWould create:")
            for item in results['to_create'][:10]:
                print(f"  + {os.path.basename(item['filepath'])} [tags: {item['tags']}]")
            if len(results['to_create']) > 10:
                print(f"  ... and {len(results['to_create']) - 10} more")

        if results['to_update']:
            print("\nWould update (content):")
            for item in results['to_update'][:10]:
                print(f"  ~ {os.path.basename(item['filepath'])} [tags: {item['tags']}]")

        if results['tag_changes']:
            print("\nWould update (tags only):")
            for item in results['tag_changes'][:10]:
                print(f"  # {os.path.basename(item['filepath'])}: {item['old_tags']} -> {item['new_tags']}")
        return

    # 実際に同期を実行
    created = 0
    updated = 0
    tag_updated = 0
    errors = 0

    def process_batch(batch_data, action_name):
        """バッチをbulk_postで送信"""
        nonlocal errors
        if not batch_data:
            return 0
        try:
            results = api.note.bulk_post(batch_data, wait=True)
            success = 0
            for r in results:
                if 'error' in r:
                    print(f"  Error ({action_name}): {r}")
                    errors += 1
                else:
                    success += 1
            return success
        except Exception as e:
            print(f"  Batch error ({action_name}): {e}")
            errors += len(batch_data)
            return 0

    # 新規作成（バッチ処理）
    if results['to_create']:
        print(f"\nCreating {len(results['to_create'])} notes...")
        batch = {}
        for i, item in enumerate(results['to_create']):
            content, _ = parse_local_file(item['filepath'])
            current_time = time.time()
            new_id = str(uuid.uuid4()).replace('-', '')
            batch[new_id] = {
                'content': content,
                'tags': item['tags'],
                'deleted': False,
                'shareURL': '',
                'publishURL': '',
                'systemTags': [],
                'modificationDate': current_time,
                'creationDate': current_time
            }

            if len(batch) >= batch_size:
                count = process_batch(batch, "create")
                created += count
                print(f"  Progress: {created}/{len(results['to_create'])} created")
                batch = {}

        # 残りを処理
        if batch:
            count = process_batch(batch, "create")
            created += count
            print(f"  Progress: {created}/{len(results['to_create'])} created")

    # コンテンツ更新（バッチ処理）
    if results['to_update']:
        print(f"\nUpdating {len(results['to_update'])} notes (content)...")
        batch = {}
        for i, item in enumerate(results['to_update']):
            content, _ = parse_local_file(item['filepath'])
            current_time = time.time()
            batch[item['note_id']] = {
                'content': content,
                'tags': item['tags'],
                'deleted': False,
                'modificationDate': current_time
            }

            if len(batch) >= batch_size:
                count = process_batch(batch, "update")
                updated += count
                print(f"  Progress: {updated}/{len(results['to_update'])} updated")
                batch = {}

        if batch:
            count = process_batch(batch, "update")
            updated += count
            print(f"  Progress: {updated}/{len(results['to_update'])} updated")

    # タグのみ更新（バッチ処理）
    if results['tag_changes']:
        print(f"\nUpdating {len(results['tag_changes'])} notes (tags only)...")
        batch = {}
        for i, item in enumerate(results['tag_changes']):
            content, _ = parse_local_file(item['filepath'])
            current_time = time.time()
            batch[item['note_id']] = {
                'content': content,
                'tags': item['new_tags'],
                'deleted': False,
                'modificationDate': current_time
            }

            if len(batch) >= batch_size:
                count = process_batch(batch, "tag update")
                tag_updated += count
                print(f"  Progress: {tag_updated}/{len(results['tag_changes'])} tag updates")
                batch = {}

        if batch:
            count = process_batch(batch, "tag update")
            tag_updated += count
            print(f"  Progress: {tag_updated}/{len(results['tag_changes'])} tag updates")

    print(f"\nDone: {created} created, {updated} updated, {tag_updated} tags updated, {len(results['identical'])} unchanged.")
    if errors > 0:
        print(f"Errors: {errors}")


def show_status(import_dir):
    """同期状態を表示"""
    result = analyze_sync_status(import_dir)
    if result is None:
        return

    results, _, _ = result

    print(f"=== Sync Status ===")
    print(f"Local files: {results['local_count']}")
    print(f"Remote notes: {results['remote_count']}")
    print(f"")
    print(f"Pending changes:")
    print(f"  - New files to create: {len(results['to_create'])}")
    print(f"  - Files to update (content): {len(results['to_update'])}")
    print(f"  - Files to update (tags only): {len(results['tag_changes'])}")
    print(f"  - Already synced: {len(results['identical'])}")

    if results['tag_changes']:
        print(f"\nTag changes pending:")
        for item in results['tag_changes'][:5]:
            print(f"  {os.path.basename(item['filepath'])}: {item['old_tags']} -> {item['new_tags']}")
        if len(results['tag_changes']) > 5:
            print(f"  ... and {len(results['tag_changes']) - 5} more")


def show_json(import_dir):
    """JSON形式で状態を出力"""
    result = analyze_sync_status(import_dir)
    if result is None:
        return

    results, _, _ = result

    output = {
        'local_count': results['local_count'],
        'remote_count': results['remote_count'],
        'to_create_count': len(results['to_create']),
        'to_update_count': len(results['to_update']),
        'tag_changes_count': len(results['tag_changes']),
        'identical_count': len(results['identical']),
        'tag_changes': [
            {
                'filename': os.path.basename(item['filepath']),
                'old_tags': item['old_tags'],
                'new_tags': item['new_tags']
            }
            for item in results['tag_changes'][:20]
        ]
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 simplenote-import.py status [backup_dir]   - Show sync status")
        print("  python3 simplenote-import.py sync [backup_dir]     - Sync all changes")
        print("  python3 simplenote-import.py dry-run [backup_dir]  - Preview changes")
        print("  python3 simplenote-import.py json [backup_dir]     - JSON output for Claude")
        sys.exit(1)

    command = sys.argv[1]
    import_dir = sys.argv[2] if len(sys.argv) > 2 else get_default_backup_dir()

    if command == 'status':
        show_status(import_dir)
    elif command == 'sync':
        do_sync(import_dir, dry_run=False)
    elif command == 'dry-run':
        do_sync(import_dir, dry_run=True)
    elif command == 'json':
        show_json(import_dir)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()

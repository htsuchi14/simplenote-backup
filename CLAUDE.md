# Simplenote Backup プロジェクトガイドライン

## プロジェクト概要

SimplenoteとローカルMarkdownファイルの双方向同期ツール。
Simperium APIを使用してSimplenoteと通信する。

## アーキテクチャ

### ディレクトリ = タグ

```
simplenote-backup-data/
├── 仕事/           # tags: ['仕事']
│   └── meeting.md
├── プログラミング/  # tags: ['プログラミング']
│   └── react.md
├── TRASH/          # 削除されたノート
└── memo.md         # tags: [] (ルート = タグなし)
```

### 同期の仕組み

- **IDベース同期**: ファイル先頭のIDコメントで正確にマッチング
- **マッチング優先順位**: ID一致 → コンテンツ一致 → タイトル一致
- **双方向**: Pull（リモート→ローカル）+ Push（ローカル→リモート）
- **自動分類**: キーワードベースの自動タグ付け

### ファイル形式

```markdown
<!-- simplenote-id: 9f8a7c6b5e4d3c2b1a0f9e8d7c6b5a4f -->
# タイトル

本文...

Tags: タグ名
```

IDコメントは自動付与され、タイトル変更時も正確に同期される。

## 主要スクリプト

| ファイル | 役割 |
|---------|------|
| `simplenote-sync.sh` | 双方向同期のメインスクリプト |
| `simplenote-backup.py` | フルバックアップ |
| `simplenote-pull.py` | リモート→ローカル同期 |
| `simplenote-import.py` | ローカル→リモート同期 |
| `simplenote-classify.py` | ノート分類（auto/AI） |
| `simplenote_metadata.py` | ID管理ユーティリティ |

## 安全に関する注意事項

### trash_orphans はデフォルトFalse

`simplenote-pull.py` の孤立ファイル検出は、誤って大量のファイルをTRASHに移動するリスクがある。
デフォルトでは `trash_orphans=False` とし、明示的に指定した場合のみ有効にする。

```python
# 安全なデフォルト
do_pull(backup_dir, dry_run=False, trash_orphans=False)
```

### 破壊的操作の前にdry-run

```bash
# 必ずプレビューしてから実行
./venv/bin/python3 simplenote-pull.py dry-run
./venv/bin/python3 simplenote-import.py dry-run
python3 simplenote-classify.py auto --dry-run
```

### バックアップからの復元

問題が発生した場合:
```bash
# フルバックアップで復元
./venv/bin/python3 simplenote-backup.py /path/to/backup-data
```

## 開発時の注意

### 環境設定

```bash
# venvを使用
./venv/bin/python3 script.py

# .envにTOKENが必要
cp .env.example .env
```

### テスト方法

```bash
# 状態確認
./venv/bin/python3 simplenote-pull.py status
./venv/bin/python3 simplenote-import.py status
python3 simplenote-classify.py status

# dry-runで動作確認
./venv/bin/python3 simplenote-pull.py dry-run
```

### よくある問題

1. **重複ファイル作成**: マッチに失敗すると `_1`, `_2` サフィックスが付く
   - 対処: フルバックアップで再同期（IDが付与される）
   ```bash
   rm -rf ~/Dropbox/SimplenoteBackups/*
   ./simplenote-sync.sh
   ```

2. **孤立ファイル大量検出**: 初回同期時やAPIエラー時に発生
   - 対処: `trash_orphans=False` を維持

3. **IDがないファイル**: 旧形式のファイルにはIDコメントがない
   - 対処: フルバックアップで全ファイルにIDを付与

## コマンドリファレンス

```bash
# 推奨: 双方向同期
./simplenote-sync.sh
make sync

# 個別操作
make run              # フルバックアップ
./venv/bin/python3 simplenote-pull.py pull    # Pull
./venv/bin/python3 simplenote-import.py sync  # Push
python3 simplenote-classify.py auto           # 自動分類

# launchd
./install-launchd.sh    # インストール
./uninstall-launchd.sh  # アンインストール
tail -f /tmp/simplenote-sync.log  # ログ確認
```

## 自動分類ルール

`simplenote-classify.py` の `AUTO_CLASSIFY_RULES` でキーワードを定義:

```python
AUTO_CLASSIFY_RULES = {
    '仕事': ['タスク', 'task', 'TODO', 'mtg', ...],
    'プログラミング': ['Python', 'React', 'Firebase', ...],
    # ...
}
```

新しいキーワードパターンを追加する場合は、このディクショナリを更新する。

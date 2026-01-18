# 同期トラブルシューティング知識

このプロジェクトで発生しやすい問題と対処法。

## IDベース同期について

ファイル先頭にIDコメントが埋め込まれ、これにより正確な同期が実現される。

```markdown
<!-- simplenote-id: 9f8a7c6b5e4d3c2b1a0f9e8d7c6b5a4f -->
# タイトル
```

**マッチング優先順位**: ID一致 → コンテンツ一致 → タイトル一致

## よくある問題

### 1. 重複ファイル（_1, _2サフィックス）

**原因**: IDがないファイルでタイトルマッチに失敗

**対処**: フルバックアップで全ファイルにIDを付与
```bash
rm -rf /path/to/backup-data/*
./simplenote-sync.sh
# または
./venv/bin/python3 simplenote-backup.py /path/to/backup-data
```

### 2. 大量のファイルがTRASHに移動

**原因**: `trash_orphans=True` で孤立ファイル検出が過剰に動作

**対処**: バックアップで復元
```bash
./venv/bin/python3 simplenote-backup.py /path/to/backup-data
```

**予防**: `trash_orphans=False` をデフォルトに維持（simplenote-pull.py）

### 3. 同期が実行されない

**確認項目**:
- `.env` ファイルにTOKENが設定されているか
- venvが正しくセットアップされているか
- launchdサービスが起動しているか

### 4. タグが反映されない

- ディレクトリ名が正しいタグ名か確認
- `simplenote-import.py dry-run` で確認

### 5. IDがないファイル（旧形式）

**原因**: IDベース同期導入前のファイル

**対処**: フルバックアップで全ファイルにIDを付与
```bash
rm -rf ~/Dropbox/SimplenoteBackups/*
./simplenote-sync.sh
```

**確認方法**:
```bash
head -1 ~/Dropbox/SimplenoteBackups/タグ名/ファイル.md
# 期待: <!-- simplenote-id: xxx -->
```

### 6. タイトル変更後に同期がおかしい

**原因**: IDがない状態でタイトルを変更した

**対処**: フルバックアップでID付与後、再度同期
```bash
rm -rf ~/Dropbox/SimplenoteBackups/*
./simplenote-sync.sh
```

## 診断コマンド

```bash
# 各スクリプトの状態確認
./venv/bin/python3 simplenote-pull.py status
./venv/bin/python3 simplenote-import.py status
python3 simplenote-classify.py status

# launchdサービス状態
launchctl list | grep simplenote
tail -f /tmp/simplenote-sync.log

# IDが付与されているか確認
head -1 ~/Dropbox/SimplenoteBackups/*/任意のファイル.md
```

# 同期トラブルシューティング知識

このプロジェクトで発生しやすい問題と対処法。

## よくある問題

### 1. 重複ファイル（_1, _2サフィックス）

**原因**: タイトルマッチ失敗で新規作成された

**対処**:
```bash
rm -rf /path/to/backup-data/*
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

## 診断コマンド

```bash
# 各スクリプトの状態確認
./venv/bin/python3 simplenote-pull.py status
./venv/bin/python3 simplenote-import.py status
python3 simplenote-classify.py status

# launchdサービス状態
launchctl list | grep simplenote
tail -f /tmp/simplenote-sync.log
```

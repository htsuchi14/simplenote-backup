---
description: 同期の問題をトラブルシューティング
allowed-tools: Bash, Read
---

# Simplenote 同期トラブルシューティング

## 概要

同期に関する問題を診断・解決します。

## Step 1: 現在の状態確認

!`./venv/bin/python3 simplenote-pull.py status 2>&1`

!`./venv/bin/python3 simplenote-import.py status 2>&1`

!`python3 simplenote-classify.py status 2>&1`

## Step 2: launchdサービス状態

!`launchctl list | grep simplenote || echo "サービス未登録"`

!`tail -20 /tmp/simplenote-sync.log 2>/dev/null || echo "ログファイルなし"`

## よくある問題と対処法

### 1. 重複ファイル（_1, _2サフィックス）

**原因**: タイトルマッチ失敗で新規作成された

**対処**:
```bash
# バックアップディレクトリをクリアして再取得
rm -rf /path/to/backup-data/*
./venv/bin/python3 simplenote-backup.py /path/to/backup-data
```

### 2. 大量のファイルがTRASHに移動

**原因**: `trash_orphans=True` で孤立ファイル検出が過剰に動作

**対処**:
```bash
# バックアップで復元
./venv/bin/python3 simplenote-backup.py /path/to/backup-data
```

**予防**: `trash_orphans=False` をデフォルトに維持

### 3. 同期が実行されない

**確認項目**:
- `.env` ファイルにTOKENが設定されているか
- venvが正しくセットアップされているか
- launchdサービスが起動しているか

```bash
# 手動で同期テスト
./simplenote-sync.sh
```

### 4. タグが反映されない

**確認**:
- ディレクトリ名が正しいタグ名か
- simplenote-import.py の dry-run で確認

```bash
./venv/bin/python3 simplenote-import.py dry-run | grep "tags"
```

## 診断後のアクション

問題を特定したら:
1. 必要に応じて dry-run で確認
2. 修正を適用
3. `./simplenote-sync.sh` で再同期

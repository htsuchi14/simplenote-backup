---
description: Simplenoteから全ノートをローカルにバックアップ
allowed-tools: Bash, Read
---

# Simplenote フルバックアップ

## 概要

Simplenoteの全ノートをローカルにダウンロードします。
**既存ファイルは上書きされるため、初回セットアップまたは完全リセット時に使用してください。**

## 現在の状態

!`ls -la ~/Dropbox/SimplenoteBackups/ 2>/dev/null | head -20 || echo "バックアップディレクトリが存在しません"`

## コマンド

```bash
# デフォルトディレクトリにバックアップ
./venv/bin/python3 simplenote-backup.py

# 指定ディレクトリにバックアップ
./venv/bin/python3 simplenote-backup.py /path/to/backup
```

## 出力

- 各ノートを `.md` ファイルとして保存
- 単一タグのノートはタグ名のディレクトリに配置
- 削除済みノートは `TRASH/` ディレクトリに保存
- ファイル末尾に `Tags:` と `System tags:` を付与

## 使い分け

| コマンド | 用途 |
|---------|------|
| `/backup-simplenote` | 初回セットアップ、完全リセット |
| `/pull-simplenote` | 日常的なリモート変更の取得 |
| `/sync-simplenote` | ローカル変更のプッシュ |

## 注意

- バックアップ先: `~/Dropbox/SimplenoteBackups/`
- 既存ファイルがある場合、重複ファイル名は連番付与
- 日常的な同期には `/pull-simplenote` を使用推奨

---
description: Simplenote同期の全体状態を確認
allowed-tools: Bash, Read
---

# Simplenote 同期状態

## 概要

ローカルとリモートの同期状態を一括確認します。

## ローカル→リモート（Push）

!`./venv/bin/python3 simplenote-import.py status 2>&1`

## リモート→ローカル（Pull）

!`./venv/bin/python3 simplenote-pull.py status 2>&1`

## ディレクトリ構成

!`ls -la ~/Dropbox/SimplenoteBackups/ 2>/dev/null | grep "^d" | tail -20`

## 未分類ノート

!`./venv/bin/python3 simplenote-classify.py status 2>&1`

## 次のアクション

状態に応じて以下のコマンドを実行:

| 状態 | コマンド |
|------|---------|
| リモートに変更がある | `/pull-simplenote` |
| ローカルに変更がある | `/sync-simplenote` |
| 未分類ノートがある | `/classify` |
| 完全リセットしたい | `/backup-simplenote` |

---
description: 開発サイクル - 調査→計画→実装→検証
allowed-tools: Bash, Read, Write, Edit
---

# Claude Code カスタムコマンド - 開発サイクル

## 概要

このプロジェクトの開発は4つのフェーズで進めます。

## フェーズ

### 1. 調査フェーズ `/investigate`

問題や要件の調査・分析

### 2. 計画フェーズ `/plan`

実装方針の策定

### 3. 実装フェーズ `/implement`

コードの実装

### 4. 検証フェーズ `/test`

動作確認・テスト

## Simplenote 操作コマンド

| コマンド | 説明 |
|---------|------|
| `/backup-simplenote` | Simplenoteから全ノートをバックアップ |
| `/pull-simplenote` | リモートの変更をローカルに反映 |
| `/sync-simplenote` | ローカルの変更をリモートに反映 |
| `/classify` | 未分類ノートをAIで分類 |
| `/simplenote-status` | 同期状態の確認 |
| `/troubleshoot` | 同期の問題をトラブルシューティング |
| `/add-classify-rule` | 自動分類のキーワードルールを追加 |

## クイックリファレンス

```bash
# 双方向同期（推奨）
./simplenote-sync.sh
# または
make sync

# 個別操作
./venv/bin/python3 simplenote-backup.py    # フルバックアップ
./venv/bin/python3 simplenote-pull.py pull  # リモート→ローカル
./venv/bin/python3 simplenote-import.py sync # ローカル→リモート
python3 simplenote-classify.py auto         # キーワードベース自動分類
```

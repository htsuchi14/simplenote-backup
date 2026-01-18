---
description: ローカルのノートをSimplenoteに同期（タグ更新含む）
allowed-tools: Bash, Read
---

# Simplenote 同期（ローカル → リモート）

## 概要

ローカルのバックアップディレクトリの変更をSimplenoteに同期します。
**ディレクトリ構成の変更（タグ変更）も反映されます。**

> **双方向同期が必要な場合**: `./simplenote-sync.sh` または `make sync` を使用してください。
> （Pull→整理→自動タグ付け→Push を一括実行）

## 現在の状態確認

!`./venv/bin/python3 simplenote-import.py status`

## 同期の仕組み

1. **ディレクトリ名 = タグ**: `仕事/meeting.md` → Simplenoteで `tags: ['仕事']`
2. **タイトル一致で更新判定**: 先頭行（タイトル）が同じノートは更新
3. **タグのみの変更も検出**: コンテンツが同じでもタグが違えば更新

## コマンド

```bash
# 状態確認
./venv/bin/python3 simplenote-import.py status

# プレビュー（実行せず確認）
./venv/bin/python3 simplenote-import.py dry-run

# 同期実行
./venv/bin/python3 simplenote-import.py sync

# JSON出力（Claude用）
./venv/bin/python3 simplenote-import.py json
```

## 自動同期フロー

1. `status` で変更件数を確認
2. `dry-run` で変更内容をプレビュー
3. ユーザー確認後、`sync` を実行

## 出力例

```
=== Sync Summary ===
Local files: 1980
Remote notes: 1850
To create: 130
To update (content): 5
To update (tags only): 45
Identical: 1800

Done: 130 created, 5 updated, 45 tags updated, 1800 unchanged.
```

## 注意

- `sync` 実行には `.env` ファイルの `TOKEN` が必要
- _trashディレクトリ内のファイルは同期されない
- 同期は片方向（ローカル → Simplenote）

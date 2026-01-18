---
description: リモートの変更をローカルに反映（タグ変更・コンテンツ変更）
allowed-tools: Bash, Read, AskUserQuestion
---

# Simplenote Pull（リモート→ローカル同期）

## 概要

Simplenoteで行った変更（タグ変更、コンテンツ編集、新規作成）をローカルに反映します。

## 現在の状態確認

!`./venv/bin/python3 simplenote-pull.py status 2>&1`

## 検出する変更

- **タグ変更**: リモートでタグを変更 → ローカルのディレクトリを移動
- **コンテンツ変更**: リモートで編集 → ローカルファイルを更新
- **新規ノート**: リモートで作成 → ローカルにダウンロード

## コマンド

```bash
# 状態確認
./venv/bin/python3 simplenote-pull.py status

# プレビュー（実行せず確認）
./venv/bin/python3 simplenote-pull.py dry-run

# 実行
./venv/bin/python3 simplenote-pull.py pull
```

## 使用例

### タグ名変更の反映

1. Simplenote（Web/アプリ）で「Health」タグを「ヘルス」に変更
2. `/pull-simplenote` を実行
3. ローカルの `Health/` → `ヘルス/` に自動移動

## 自動実行フロー

1. `status` で変更を確認
2. 変更がある場合、ユーザーに確認
3. 確認後 `pull` を実行

## 注意

- 同期方向: リモート → ローカル
- ローカルの未コミット変更がある場合は先に `/sync-simplenote` を実行推奨

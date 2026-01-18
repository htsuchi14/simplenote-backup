---
description: 未分類のSimplenoteノートを分析してタグ付け・リネーム
allowed-tools: Bash, Read, Write
---

# Simplenote ノート自動分類

## 概要

バックアップディレクトリ内の未分類ノートを分類します。

1. **キーワードベース自動分類** (`auto`コマンド): 高速・自動、sync時に実行
2. **AI分類** (このコマンド): 手動実行、より正確な判断

## Step 0: キーワードベース自動分類を先に実行

sync時に自動実行されますが、手動でも実行可能:

```bash
# プレビュー
python3 simplenote-classify.py auto --dry-run

# 実行
python3 simplenote-classify.py auto
```

これで分類できなかったノートのみ、以下のAI分類を使用します。

## AI分類（Step 1以降）

未分類ノートを**AIで連続分類**します。
確認なしで100件ずつ処理し、未分類がなくなるまで繰り返します。

## 既存タグ一覧

!`python3 simplenote-classify.py tags`

## 現在の状態確認

!`python3 simplenote-classify.py status`

## 自動処理ループ

**動的に対応**: 未分類ノートがなくなるまで以下を繰り返す

### Step 1: タグ付きファイルの整理

`has_tag_not_moved_count > 0` の場合、先に整理:
```bash
python3 simplenote-classify.py organize
```

### Step 2: 未分類ノートの分類

`needs_classification_count > 0` の場合:

1. `python3 simplenote-classify.py json` から未分類ノートを取得
2. 各ノートに適切なタグを判定
3. **確認なしで即座に** `python3 simplenote-classify.py apply` を並列実行（10件ずつ）
4. 100件処理したら残り件数を確認
5. 残りがあれば次の100件へ

### Step 3: 完了確認

`python3 simplenote-classify.py status` で確認:
- `root_files_total: 0` になれば完了

## タグ付けガイドライン

- 上記の「既存タグ一覧」から最も適切なタグを選択
- 判断に迷う場合は最も近いタグを選択
- 新規タグは作成しない（既存タグのみ使用）
- ノート内容を読んで、主題に合ったタグを判定

## 実行時の出力

各バッチ完了時に簡潔に報告:
```
## バッチ 1 完了（100件）
仕事: 25件, ライフ: 20件, 思考: 18件, ...
残り: XXX件 → 次のバッチへ

## バッチ 2 完了（100件）
...
```

最終完了時:
```
## 全分類完了
総処理: XXX件（動的にカウント）
ルートの未分類: 0件
```

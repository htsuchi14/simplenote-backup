---
description: 自動分類のキーワードルールを追加・更新
allowed-tools: Bash, Read, Edit
---

# 自動分類ルールの追加

## 概要

`simplenote-classify.py` のキーワードベース自動分類ルールを更新します。

## 現在のルール確認

!`python3 -c "import simplenote_classify; import json; print(json.dumps(simplenote_classify.AUTO_CLASSIFY_RULES, ensure_ascii=False, indent=2))"`

## 現在の未分類ノート

!`python3 simplenote-classify.py json 2>/dev/null | head -50`

## ルール追加の手順

### 1. パターン分析

未分類ノートを確認し、共通するキーワードを特定:
- ファイル名に含まれる単語
- コンテンツに頻出する単語

### 2. ルール追加

`simplenote-classify.py` の `AUTO_CLASSIFY_RULES` ディクショナリを編集:

```python
AUTO_CLASSIFY_RULES = {
    'タグ名': ['キーワード1', 'キーワード2', ...],
    # 新しいルールを追加
}
```

### 3. テスト

```bash
# dry-runで確認
python3 simplenote-classify.py auto --dry-run

# 問題なければ実行
python3 simplenote-classify.py auto
```

## ルール設計のガイドライン

- **大文字小文字**: マッチングは case-insensitive
- **部分一致**: キーワードが含まれていればマッチ
- **スコアリング**: 複数マッチした場合、マッチ数が多いタグが選択される
- **既存タグのみ**: `AUTO_CLASSIFY_RULES` のキーはバックアップディレクトリに存在するタグ名

## 例: 新しいキーワード追加

「会議」関連のノートを「仕事」タグに分類したい場合:

```python
'仕事': ['タスク', 'task', 'TODO', 'mtg', '会議', 'meeting', ...],
```

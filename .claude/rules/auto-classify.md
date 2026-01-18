# 自動分類ルール管理

キーワードベース自動分類の仕組みと更新方法。

## AUTO_CLASSIFY_RULES の構造

`simplenote-classify.py` 内の辞書:

```python
AUTO_CLASSIFY_RULES = {
    'タグ名': ['キーワード1', 'キーワード2', ...],
}
```

## マッチングロジック

- **大文字小文字**: case-insensitive
- **部分一致**: キーワードが含まれていればマッチ
- **スコアリング**: 複数マッチ時はマッチ数が多いタグを選択
- **対象**: ファイル名 + コンテンツ

## ルール追加時の注意

1. キーは既存のタグディレクトリ名と一致させる
2. 追加前に `--dry-run` でテスト
3. 汎用的すぎるキーワードは避ける（誤分類の原因）

## テスト方法

```bash
# プレビュー
python3 simplenote-classify.py auto --dry-run

# 実行
python3 simplenote-classify.py auto
```

## 未分類ノートの確認

```bash
python3 simplenote-classify.py json
python3 simplenote-classify.py status
```

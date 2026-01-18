# Simplenote Backup & Sync Tools

Simplenoteのノートをローカルにバックアップし、双方向同期を行うツール群です。

## 機能概要

| スクリプト | 機能 | 方向 |
|-----------|------|------|
| `simplenote-sync.sh` | **双方向同期（推奨）** - Pull→Push を自動実行 | Bidirectional |
| `simplenote-backup.py` | リモートからローカルへ全ノートをダウンロード | Remote → Local |
| `simplenote-import.py` | ローカルの変更をリモートにプッシュ | Local → Remote |
| `simplenote-pull.py` | リモートの変更をローカルに反映（差分同期） | Remote → Local |
| `simplenote-classify.py` | 未分類ノートの自動タグ付け | Local |

## クイックスタート

### 1. セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/hiroshi/simplenote-backup.git
cd simplenote-backup

# Python仮想環境を作成
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install simperium
```

### 2. トークンの取得

1. https://app.simplenote.com にログイン
2. DevToolsを開く (`Cmd + Option + I`)
3. **Application** タブ → **Cookies** → `app.simplenote.com` → `token` の値をコピー

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env` ファイルを編集:
```
TOKEN=your_simplenote_token_here
```

### 4. 動作確認

```bash
# バックアップを実行
./venv/bin/python3 simplenote-backup.py

# 出力例:
# Starting backup your simplenote to: /Users/xxx/Dropbox/SimplenoteBackups
# Done: 1981 files (0 in TRASH).
```

---

## スクリプト詳細

### simplenote-backup.py（フルバックアップ）

リモートのSimplenoteから全ノートをダウンロードします。

```bash
# デフォルトディレクトリ（~/Dropbox/SimplenoteBackups）にバックアップ
./venv/bin/python3 simplenote-backup.py

# 指定ディレクトリにバックアップ
./venv/bin/python3 simplenote-backup.py /path/to/backup
```

**特徴:**
- 各ノートを `.md` ファイルとして保存
- ファイル名は先頭行（タイトル）から生成
- 単一タグのノートはタグ名のディレクトリに配置
- 削除済みノートは `TRASH/` ディレクトリに保存
- ファイル末尾に `Tags:` と `System tags:` を付与

**出力例:**
```
仕事/
├── 会議メモ.md
├── プロジェクトA.md
└── タスク一覧.md
ライフ/
├── 買い物リスト.md
└── 旅行計画.md
TRASH/
└── 削除したノート.md
```

---

### simplenote-import.py（ローカル→リモート同期）

ローカルの変更をSimplenoteにプッシュします。

```bash
# 状態確認
./venv/bin/python3 simplenote-import.py status

# プレビュー（実行せず確認）
./venv/bin/python3 simplenote-import.py dry-run

# 同期実行
./venv/bin/python3 simplenote-import.py sync

# JSON出力（自動処理用）
./venv/bin/python3 simplenote-import.py json
```

**同期ロジック（マッチング優先順位）:**
1. **ID一致（最優先）**: ファイル先頭のIDコメントでマッチング
2. **コンテンツ完全一致**: 内容が同じならスキップ
3. **タイトル一致（後方互換）**: 先頭行が同じノートは更新
4. **新規**: マッチしないファイルは新規作成
- **ディレクトリ = タグ**: `仕事/memo.md` → `tags: ['仕事']`

**出力例:**
```
=== Sync Summary ===
Local files: 1980
Remote notes: 1981
To create: 5
To update (content): 10
To update (tags only): 3
Identical: 1962

Creating 5 notes...
  Progress: 5/5 created
Done: 5 created, 10 updated, 3 tags updated, 1962 unchanged.
```

---

### simplenote-sync.sh（双方向同期 - 推奨）

Pull（Remote→Local）と Push（Local→Remote）を順番に実行し、ローカルとリモートを同期します。
未分類ノートはキーワードベースで自動タグ付けされます。

```bash
# 同期を実行
./simplenote-sync.sh

# プレビュー（実行せず確認）
./simplenote-sync.sh --dry-run
```

**動作フロー:**
```
1. Pull (Remote → Local)
   - リモートの変更をローカルに反映
   - タグ変更、コンテンツ変更、削除を検出

2. Organize
   - タグ付きファイルを適切なディレクトリへ移動

3. Auto-classify（キーワードベース）
   - 未タグファイルをキーワードで自動分類
   - 分類できないファイルは警告を出力

4. Push (Local → Remote)
   - ローカルの変更をリモートに反映
   - 自動分類したタグもプッシュ
```

**ログ出力:** `/tmp/simplenote-sync.log`

**自動分類できなかったファイルがある場合:**
```bash
# Claude Codeで手動分類
/classify
```

---

### simplenote-pull.py（リモート→ローカル差分同期）

リモートの変更をローカルに反映します。タグ変更やコンテンツ変更を検出して適用します。

```bash
# 状態確認
./venv/bin/python3 simplenote-pull.py status

# プレビュー
./venv/bin/python3 simplenote-pull.py dry-run

# 実行
./venv/bin/python3 simplenote-pull.py pull
```

**検出する変更:**
- **タグ変更**: リモートでタグを変更 → ローカルのディレクトリを移動
- **コンテンツ変更**: リモートで編集 → ローカルファイルを更新
- **新規ノート**: リモートで作成 → ローカルにダウンロード
- **削除（Trash）**: リモートで削除 → ローカルを`TRASH/`へ移動
- **孤立ファイル**: ローカルのみに存在するファイルを検出（警告表示）

**使用例（タグ名変更の反映）:**
```bash
# リモートで「Health」タグを「ヘルス」に変更した場合
./venv/bin/python3 simplenote-pull.py status
# Tag changes: Health/ -> ヘルス/

./venv/bin/python3 simplenote-pull.py pull
# Moved: ファイル1.md -> ヘルス/
# Moved: ファイル2.md -> ヘルス/
# Removed empty directory: Health/
```

**使用例（リモートで削除したノート）:**
```bash
./venv/bin/python3 simplenote-pull.py pull
# [2026-01-18 12:00:00] INFO: Moved to TRASH: 削除したノート.md
```

---

### simplenote-classify.py（未分類ノートの自動分類）

ルートディレクトリにある未分類ノートにタグを付けてディレクトリに移動します。

```bash
# 状態確認
./venv/bin/python3 simplenote-classify.py status

# 未分類ファイル一覧
./venv/bin/python3 simplenote-classify.py list

# 既存タグ一覧
./venv/bin/python3 simplenote-classify.py tags

# キーワードベースの自動分類（sync.shで使用）
./venv/bin/python3 simplenote-classify.py auto
./venv/bin/python3 simplenote-classify.py auto --dry-run  # プレビュー

# タグを適用（ファイルをディレクトリに移動）
./venv/bin/python3 simplenote-classify.py apply <filename> <tag>

# ファイル名を変更
./venv/bin/python3 simplenote-classify.py rename <filename> "<new_title>"

# タグ付きだが未移動のファイルを整理
./venv/bin/python3 simplenote-classify.py organize
```

**自動分類の仕組み:**

`auto` コマンドはキーワードマッチングで分類します:

| タグ | キーワード例 |
|------|------------|
| 仕事 | タスク, mtg, API, AWS, デプロイ, ヘルプ... |
| プログラミング | Python, React, Firebase, エラー, テスト... |
| ライフ | 買い物, 旅行, 料理, 掃除... |
| ヘルス | 健康, 運動, 筋トレ, 睡眠... |
| 思考 | アイデア, メモ, 反省, 日記... |

キーワードで判定できないノートは `/classify` で手動分類が必要です。

---

## Claude Code 連携

Claude Codeのカスタムコマンド（スラッシュコマンド）で簡単に操作できます。

### コマンド一覧

| コマンド | 方向 | 説明 |
|---------|------|------|
| `/simplenote-status` | - | 全体の同期状態を一括確認 |
| `/sync-simplenote` | Local → Remote | ローカル変更をSimplenoteにプッシュ |
| `/pull-simplenote` | Remote → Local | リモート変更をローカルに反映 |
| `/backup-simplenote` | Remote → Local | 全ノートをフルバックアップ |
| `/classify` | Local | 未分類ノートの自動タグ付け |

### ケース別実行手順

#### 🔄 日常的な同期（推奨フロー）

**自動実行（launchd）:** 1時間ごとに自動で双方向同期が実行されます。

**手動実行:**
```bash
./simplenote-sync.sh   # Pull → Auto-classify → Push
```

**Claude Codeで手動実行:**
```
/simplenote-status     # まず状態確認
/pull-simplenote       # リモートの変更を取得
/classify              # 未分類ノートをAIで分類（必要な場合）
/sync-simplenote       # ローカルの変更をプッシュ
```

#### 📱 スマホで編集した内容をローカルに反映したい

```
/pull-simplenote
```

#### 💻 ローカルで編集した内容をSimplenoteに反映したい

```
/sync-simplenote
```

#### 🏷️ Simplenoteでタグ名を変更した（例: Health → ヘルス）

```
/pull-simplenote
```
→ ローカルのディレクトリが自動で `Health/` → `ヘルス/` に移動

#### 📂 ローカルでファイルを別ディレクトリに移動した（タグ変更）

```
/sync-simplenote
```
→ Simplenote上のタグが自動で更新

#### 🆕 初回セットアップ

```
/backup-simplenote     # 全ノートをダウンロード
/classify              # 未分類ノートにタグ付け
/sync-simplenote       # タグ変更をリモートに反映
```

#### 🗂️ 未分類ノートを整理したい

**方法1: 自動分類（キーワードベース）**
```bash
./simplenote-sync.sh   # sync時に自動実行される
# または
./venv/bin/python3 simplenote-classify.py auto
```
→ キーワードマッチングで高速に分類

**方法2: AI分類（高精度）**
```
/classify
```
→ Claude Codeがノート内容を分析して適切なタグを判定
→ キーワードで分類できなかったノートはこちらで対応

#### ❓ 今どうなってるか確認したい

```
/simplenote-status
```
→ Push/Pull両方の状態、未分類ノート数を一括表示

---

## 定期バックアップの設定

### 方法1: crontab

```bash
crontab -e
```

毎時同期（推奨）:
```cron
0 * * * * cd ~/simplenote-backup && ./simplenote-sync.sh > /tmp/simplenote-sync.log 2>&1
```

毎時バックアップのみ:
```cron
0 * * * * cd ~/simplenote-backup && ./venv/bin/python3 simplenote-backup.py > /tmp/simplenote-backup.log 2>&1
```

毎日6時にバックアップ:
```cron
0 6 * * * cd ~/simplenote-backup && ./venv/bin/python3 simplenote-backup.py > /tmp/simplenote-backup.log 2>&1
```

### 方法2: launchd（macOS推奨）

#### 初回セットアップ

```bash
./install-launchd.sh
```

#### 設定内容

| 項目 | 値 |
|------|-----|
| サービス名 | `com.simplenote.sync` |
| 実行間隔 | 1時間ごと（3600秒） |
| 起動時実行 | あり（RunAtLoad） |
| ログ出力 | `/tmp/simplenote-sync.log` |
| 実行スクリプト | `simplenote-sync.sh` |

#### 管理コマンド

```bash
# 状態確認
launchctl list | grep simplenote

# 手動実行
launchctl start com.simplenote.sync

# 一時停止
launchctl unload ~/Library/LaunchAgents/com.simplenote.sync.plist

# 再開
launchctl load ~/Library/LaunchAgents/com.simplenote.sync.plist

# アンインストール
./uninstall-launchd.sh
```

#### ログ確認

```bash
tail -f /tmp/simplenote-sync.log
```

#### 動作確認

```bash
# 1. サービスが登録されているか確認
launchctl list | grep simplenote

# 2. 手動実行してテスト
launchctl start com.simplenote.sync

# 3. ログで成功を確認
tail -30 /tmp/simplenote-sync.log
# 期待される出力:
# [2026-01-18 12:00:00] Simplenote Sync Started
# [2026-01-18 12:00:00] Step 1: Pull (Remote -> Local)
# ...
# [2026-01-18 12:00:05] Step 2: Organize (Move tagged files)
# [2026-01-18 12:00:05] Step 2.5: Auto-classify (X untagged files)
# ...
# [2026-01-18 12:00:10] Step 3: Push (Local -> Remote)
# ...
# [2026-01-18 12:00:15] Sync Complete
```

#### トラブルシューティング

**サービスが動かない場合:**
```bash
# エラーログを確認
cat /tmp/simplenote-sync-error.log

# サービスを再登録
./uninstall-launchd.sh
./install-launchd.sh
```

**トークン期限切れの場合:**
1. 新しいトークンを取得（Simplenote Web → DevTools → Cookies）
2. `.env` ファイルを更新
3. `launchctl start com.simplenote.sync` で動作確認

---

## データ構造

### ディレクトリとタグの関係

```
~/Dropbox/SimplenoteBackups/
├── 仕事/              # タグ: 仕事
│   ├── 会議メモ.md
│   └── タスク.md
├── ライフ/            # タグ: ライフ
│   └── 買い物.md
├── TRASH/             # 削除済み（同期対象外）
│   └── 古いノート.md
└── 未分類ノート.md    # タグなし（ルート）
```

### ファイル形式

```markdown
<!-- simplenote-id: 9f8a7c6b5e4d3c2b1a0f9e8d7c6b5a4f -->
# ノートのタイトル

ノートの本文...

Tags: 仕事, プロジェクト
System tags: pinned
```

**IDコメントについて:**
- 先頭行のHTMLコメントにSimplenoteの内部IDが埋め込まれます
- このIDにより、タイトルを変更しても正確に同期されます
- IDはバックアップ/Pull時に自動付与されるため、手動編集は不要です
- Simplenoteに同期されても表示には影響しません（HTMLコメントのため）

---

## クイックリファレンス

| やりたいこと | コマンド |
|-------------|---------|
| **双方向同期（推奨）** | `./simplenote-sync.sh` |
| 状態確認 | `./venv/bin/python3 simplenote-classify.py status` |
| フルバックアップ | `./venv/bin/python3 simplenote-backup.py` |
| 未分類ノート自動分類 | `./venv/bin/python3 simplenote-classify.py auto` |
| 未分類ノートAI分類 | `/classify`（Claude Code） |

---

## IDベース同期へのマイグレーション

既存のバックアップにIDを付与して、より安定した同期を実現できます。

```bash
# 1. ローカルファイルを削除
rm -rf ~/Dropbox/SimplenoteBackups/*

# 2. フルバックアップ（ID付きで再エクスポート）
./simplenote-sync.sh
# または
./venv/bin/python3 simplenote-backup.py ~/Dropbox/SimplenoteBackups

# 3. IDが付与されているか確認
head -1 ~/Dropbox/SimplenoteBackups/*/任意のファイル.md
# 期待: <!-- simplenote-id: xxxxxxxx... -->
```

**マイグレーション後のメリット:**
- タイトルを変更しても正しく同期される
- 重複タイトルでも正確にマッチング
- 同期の安定性が大幅に向上

---

## トラブルシューティング

### トークンの有効期限切れ

エラー例: `HTTPError: 401 Unauthorized`

**対処法:** 新しいトークンを取得して `.env` を更新

### 同期が安定しない

同じファイルが毎回「更新が必要」と判定される場合:

**対処法1: IDベース同期にマイグレーション（推奨）**
```bash
rm -rf ~/Dropbox/SimplenoteBackups/*
./simplenote-sync.sh
```

**対処法2: 2回連続sync**
```bash
./venv/bin/python3 simplenote-import.py sync
./venv/bin/python3 simplenote-import.py sync
```

### 重複タイトルの問題

**IDがある場合:** 問題なし（IDで正確にマッチング）

**IDがない場合:** 同じタイトルのノートが複数あると、最初のマッチ以降は新規作成されます。
→ IDベース同期へのマイグレーションを推奨

### 重複ファイル（_1, _2サフィックス）が作成される

**原因:** タイトルマッチに失敗して新規ファイルとして作成された

**対処法:** フルバックアップで再同期（IDが付与される）
```bash
rm -rf ~/Dropbox/SimplenoteBackups/*
./venv/bin/python3 simplenote-backup.py ~/Dropbox/SimplenoteBackups
```

---

## Docker

```bash
# イメージをビルド
docker build -t simplenote-backup .

# バックアップを実行
docker run --rm \
  -e TOKEN=your_token \
  -v /path/to/backup:/data \
  simplenote-backup

# 同期（Local → Remote）を実行
docker run --rm \
  -e TOKEN=your_token \
  -v /path/to/backup:/data \
  simplenote-backup python3 simplenote-import.py sync /data

# プル（Remote → Local）を実行
docker run --rm \
  -e TOKEN=your_token \
  -v /path/to/backup:/data \
  simplenote-backup python3 simplenote-pull.py pull /data
```

---

## ファイル構成

```
simplenote-backup/
├── simplenote-sync.sh      # 双方向同期スクリプト（メイン）
├── simplenote-backup.py    # フルバックアップ（Remote → Local）
├── simplenote-import.py    # プッシュ同期（Local → Remote）
├── simplenote-pull.py      # プル同期（Remote → Local, 差分）
├── simplenote-classify.py  # 未分類ノートの自動タグ付け
├── simplenote_metadata.py  # ID管理ユーティリティ
├── install-launchd.sh      # launchd インストーラー
├── uninstall-launchd.sh    # launchd アンインストーラー
├── com.simplenote.sync.plist.template  # launchd設定テンプレート
├── sync-upstream.sh        # Fork元リポジトリとの同期
├── .env                    # トークン設定（要作成）
├── .env.example            # 設定ファイルのテンプレート
├── Makefile                # makeコマンド定義
├── Dockerfile              # Docker設定
└── venv/                   # Python仮想環境
```

---

## Makeコマンド

```bash
make sync                   # 双方向同期（推奨）
make run                    # バックアップ実行
make import                 # インポート実行
make classify-list          # 未分類ファイル一覧
make classify-tags          # 既存タグ一覧
make classify-json          # JSON出力
```

---

## ライセンス

MIT License

# Claude Code 活用術 — 非エンジニア向け講座カリキュラム

## コンセプト

非エンジニアが Claude Code を使って「自分で作れる」を体験する講座。
コードを書くことが目的ではなく、AIに指示を出してプロダクトを形にする力を身につける。

## 販売チャネル

| チャネル | 用途 | 形式 |
|---------|------|------|
| **ココナラ** | 単発講座の申込窓口 | 1回90分のオンライン講座 |
| **MENTA** | 伴走型メンター | 月額サブスクで継続サポート |
| **Notion** | 教材配布 | 辞書セクション・テンプレート・宿題 |

## 商品ラインナップ

```
┌─────────────────────────────────────────────────┐
│  ココナラ（単発講座）                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  基本コース（全4回）                               │
│    第1回 導入・環境構築                             │
│    第2回 ローカルアプリ開発                          │
│    第3回 Supabase + GitHub                        │
│    第4回 Vercel デプロイ                            │
│                                                   │
│  応用（単発）※基本コース修了者向け                   │
│    応用1: VSCode で Git/GitHub 入門                │
│    応用2: Google Drive / Sheets セキュリティ入門    │
│    応用3: Claude Code で GAS 開発入門（Clasp）     │
│    応用4: SNS マーケ API 連携入門                  │
│    応用5: 請求データ自動収集 × Live Artifact       │
│    Skills 入門 / etc.                              │
├─────────────────────────────────────────────────┤
│  MENTA（伴走型メンター）                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  月額プラン                                        │
│    ・週1回30分のオンライン相談                       │
│    ・Slack/Discord で随時質問                       │
│    ・受講者のやりたいこと起点で伴走                   │
│    ・業務自動化 / アプリ開発 / Skills 作成           │
├─────────────────────────────────────────────────┤
│  ビジネスユース（将来拡張）                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│    財務管理 / タスク管理 / 資料作成 / DX推進         │
│    → 法人研修 or MENTAの上位プランとして展開          │
└─────────────────────────────────────────────────┘
```

## 導線設計

```
X / Qiita 発信（認知）
  ↓
ココナラ 第1回 体験（3,000〜5,000円）
  ↓
ココナラ 第2〜4回 継続（各回 5,000〜8,000円）
  ↓
MENTA 伴走プラン（月額 15,000〜30,000円）
  ↓
法人研修・DXコンサル（将来）
```

---

## 基本コース（全4回）— ココナラ

### 第1回: 導入・環境構築（90分）

**ゴール**: Claude Code が動く環境を作り、最初の指示を出して成果物を手に入れる

**講義（20分）**
- Claude Code とは何か — ChatGPT/Cursor との違い
- 非エンジニアにとって何が変わるのか
- 料金プラン（Pro / Max）と始め方

**ハンズオン（60分）**
- Node.js インストール
- Claude Code インストール（`npm install -g @anthropic-ai/claude-code`）
- 初回認証・ログイン
- 最初の指示: 「自己紹介ページを作って」→ ブラウザで確認
- 修正を指示で行う体験（色・レイアウト・写真追加）
- CLAUDE.md を作って「指示の前提」を覚えさせる

**まとめ・次回案内（10分）**

**Notion 教材（自習用・辞書）**
- コマンド一覧（/help, /clear, /compact, /model 等）
- 権限モード解説（plan / auto）
- settings.json の設定
- キーボードショートカット
- トラブルシューティング集（認証エラー、タイムアウト等）
- 指示の出し方テンプレート10選

---

### 第2回: ローカルアプリ開発（90分）

**ゴール**: Next.js で動く Web アプリを作り、「自分で作れた」を実感する

**講義（15分）**
- Web アプリの仕組み（フロントエンド / バックエンド / DB）
- Next.js を選ぶ理由（Claude Code との相性が最高）
- 完成イメージの共有

**ハンズオン（65分）**
- `npx create-next-app` でプロジェクト作成
- Claude Code に「TODOアプリを作って」と指示
- `npm run dev` で動作確認
- 画面の修正を指示で行う（色・レイアウト・機能追加）
- CLAUDE.md にプロジェクトルールを追加
- エラーが出たときの対処法（エラーをそのまま貼るだけでOK）
- 受講者が作りたいもののアイデア出し

**まとめ・次回案内（10分）**

**Notion 教材（自習用・辞書）**
- Next.js プロジェクト構造ガイド
- よく使う npm コマンド
- ブラウザ DevTools の使い方
- CLAUDE.md テンプレート集
- 「こんなアプリ作りたい」指示文テンプレート

---

### 第3回: Supabase + GitHub（90分）

**ゴール**: データが保存されるアプリにし、コードをバックアップできるようになる

**講義（15分）**
- なぜデータベースが必要か（ブラウザを閉じてもデータが消えない）
- Supabase とは（無料で使える PostgreSQL）
- GitHub とは（コードのバックアップ。壊しても戻せる安心感）

**ハンズオン（65分）**
- Supabase アカウント作成・プロジェクト作成
- テーブル作成（TODO テーブル）
- 環境変数の設定（.env.local）
- Claude Code に「Supabase に接続して」と指示
- データの保存・表示を確認
- GitHub アカウント作成・リポジトリ作成
- `git init` → `git push`
- .gitignore で .env を除外する（セキュリティ）

**まとめ・次回案内（10分）**

**Notion 教材（自習用・辞書）**
- Supabase ダッシュボード操作ガイド
- SQL 基本チートシート
- RLS（Row Level Security）の概要
- Git コマンドチートシート
- GitHub 画面ガイド

---

### 第4回: Vercel デプロイ — アプリを世界に公開する（90分）

**ゴール**: 作ったアプリに URL がつき、誰でもアクセスできるようになる

**講義（15分）**
- デプロイとは（ローカル → インターネット）
- Vercel を選ぶ理由（Next.js 公式、無料枠あり）
- 「自分の URL を持つ」ということ

**ハンズオン（55分）**
- Vercel アカウント作成
- GitHub リポジトリと連携
- 環境変数の設定（Vercel ダッシュボード）
- デプロイ → URL 確認 → スマホからアクセス
- 修正 → push → 自動デプロイの体験
- OGP 画像の設定（SNS シェア用）

**振り返り・今後の学び方（20分）**
- 4回で学んだことの全体像
- ここから先の選択肢（Skills / MCP / API連携 / ビジネス活用）
- MENTA 伴走プランの案内
- 「次に作りたいもの」を言語化する

**Notion 教材（自習用・辞書）**
- Vercel ダッシュボード操作ガイド
- デプロイログの読み方
- ビルドエラー対処法
- 無料枠の制限事項
- 独自ドメインの取得・設定方法

---

## 応用コース（単発）— ココナラ

基本コース修了者または Claude Code を既に使っている方向けの単発講座。

### 応用1: VSCode で Git/GitHub 入門（90分）

**前提**: 基本コース第3回まで修了（GitHub アカウント・リポジトリ作成済み）

**ゴール**: VSCode の GUI で Git 操作ができるようになり、ブランチ・Pull Request の概念を理解する

**講義（10分）**
- ブランチの概念（「本の原稿のコピーで試し書き」）
- Pull Request の概念（「変更の稟議書」）
- CLI と GUI の使い分け

**ハンズオン（65分）**
- VSCode Source Control パネルでステージング・コミット・差分確認
- Git Graph 拡張機能でコミット履歴を可視化
- ブランチを作成して機能を追加（VSCode GUI で完結）
- GitHub 上で Pull Request を作成・マージ
- Claude Code の /commit スキルと git 安全機構の紹介

**まとめ（10分）**

**Notion 教材（自習用・辞書）**
- VSCode Source Control パネル操作ガイド
- Git Graph の見方ガイド
- ブランチ命名規則チートシート
- Pull Request テンプレート

---

### 応用2: Google Drive / スプレッドシート セキュリティ入門（90分）

**前提**: 基本コース第1回修了（Claude Code が動く環境がある）、macOS 推奨

**ゴール**: Claude Code から gog CLI を使って Google Drive / Sheets を安全に読み書きできるようになり、OAuth 認証の仕組みと「自分で鍵を管理する」運用責任を理解する

**講義（20分）**
- Claude.ai コネクタと Claude Code の違い（コネクタは Claude Code からは使えない）
- gog CLI とは — Google Workspace 用 OSS コマンドラインツール
- OAuth 2.0 の仕組み（クライアント / スコープ / リフレッシュトークン）
- セキュリティ 3 層（スコープ / Google 権限管理 / 組織 Workspace Admin）

**ハンズオン（60分）**
- Homebrew で gog CLI をインストール（5分）
- Google Cloud Console で OAuth クライアントを作成（20分）
- gog CLI の認証とスコープ指定（10分）
- Drive 検索・読み取り（10分）
- Sheets への書き込み・更新と `--dry-run` による安全運用（10分）
- 権限の確認と取り消し方法（5分）

**まとめ（5分）**

**Notion 教材（自習用・辞書）**
- gog CLI コマンドチートシート
- Google Cloud Console OAuth セットアップガイド
- 「やっていいこと・ダメなこと」チェックリスト
- IT 部門への相談テンプレート（gog CLI 利用許可）
- OAuth クライアント JSON 漏洩時の緊急対応手順

---

### 応用3: Claude Code で GAS 開発入門（Clasp セットアップ編）（90分）

**前提**: 基本コース第1〜2回修了（Node.js・Claude Code が動く）、Google アカウント所有

**ゴール**: Clasp（Google 公式 CLI）を PC にセットアップし、Claude Code で書いた GAS を `clasp push` で Google に送り、勤怠記録スプレッドシートを自動生成できるようになる

**講義（15分）**
- GAS（Google Apps Script）とは -- Google 版の VBA
- 従来のブラウザエディタ開発の限界
- Clasp とは -- ローカル ⇄ Google の同期ツール
- Claude Code × Clasp の組み合わせメリット

**ハンズオン（65分）**
- Node.js 22 以上へのアップグレード確認
- `npm install -g @google/clasp`
- Apps Script API の有効化（`script.google.com/home/usersettings`）
- `clasp login` で Google 連携
- `clasp create --title "勤怠記録ジェネレーター" --type standalone`
- Claude Code に指示して勤怠表生成関数を作成
- `clasp push` → スクリプトエディタで実行 → Drive で成果物確認
- 追い指示で書式変更 → 再 push の往復体験
- `clasp pull` で Google 側の変更を取り込む体験

**まとめ（10分）**
- `clasp clone` で既存シートに紐付ける運用
- トリガー（定期実行）で完全自動化する世界観
- 応用テーマ（Gmail 自動化、Form → Slack 連携、AI API 連携）

**Notion 教材（自習用・辞書）**
- Clasp コマンドチートシート
- 認証トラブル対処集
- `.clasp.json` / `appsscript.json` の読み方
- GAS 指示文テンプレート10選
- 会社利用時の IT 部門相談テンプレート

---

### 応用4: Claude Code で SNS マーケ API 連携入門（90分）

**ゴール**: MCP / Agent Skills / API 直叩きの3方式を使い分けて、GA4・Shopify・X・ニュース RSS から数値を取得し、Google スプレッドシートに自動転記できるようになる。題材は「週次マーケ KPI レポート自動生成」

**講義（15分）**
- MCP / Agent Skills / API の使い分けと意思決定フロー
- 認証の3類型（API キー / OAuth 2.0 / Service Account）
- レート制限と「やっていい使い方」（自社データのみ・第三者収集 NG）

**ハンズオン（60分）**
- Step 1: Claude Code 自身に各サービスの連携手段を調べさせる
- Step 2: 採用する連携方式の意思決定（MCP > Skills > API / RSS）
- Step 3-A: Shopify 公式 Dev MCP を 1 コマンドで導入
- Step 3-B: GA4 公式 MCP + Service Account で実データ取得（本命）
- Step 3-C: `openclaw-xurl` スキル導入と X API 認証（実取得は任意）
- Step 4: 取得値をローカル CSV に書き出し → Claude.ai デスクトップの Drive コネクタで Sheets にアップロード
- Step 5: 公式 RSS フィードから業界ニュースを取得 → 同様に Sheets に追加

**まとめ（10分）**
- 定期実行（GAS トリガーと組み合わせる構成）
- Shopify / Instagram 実データ取得の応用テーマ案内
- セキュリティ確認（Service Account 鍵 / `~/.xurl` / `.env` 管理）

**Notion 教材（自習用・辞書）**
- Shopify 実データ取得編（Custom App 作成 → Admin GraphQL）
- Instagram 実データ取得編（Porter MCP / Graph API v22）
- GA4 Service Account セットアップ完全ガイド（GCP 画面付き）
- xurl スキル完全リファレンス
- Google News RSS クエリ修飾子チートシート
- ライセンス注意点（Bloomberg / Reuters / 日経 / TechCrunch）
- 「会社で使う」前の IT 部門相談テンプレート

---

### 応用5: Claude Code で作る請求データ自動収集 × Live Artifact ダッシュボード（90分）

**前提**: 基本コース第1〜2回修了（Node.js / Claude Code が動く）、応用3 か Clasp の経験があると有利。Claude.ai Pro / Max / Team / Enterprise プラン必須。invox 連携は本編対象外（拡張ガイドあり）。

**ゴール**: Kintone から API でデータを取得し、毎朝 6 時に Google スプレッドシートを自動更新する GAS を Claude Code に書かせ、その台帳を Claude.ai デスクトップの **Live Artifact** でダッシュボード化し、**自分のブックマークから毎朝開ける状態にし、社内共有の代替手段（スクショ / PDF / Sheets URL）を選べる** ようになる。題材は「請求ダッシュボード（月次請求額 / 取引先別 / 支払予定 / 滞納アラート）」

**講義（15分）**
- アーキテクチャ全体像（Kintone → GAS → Sheets → Live Artifact）
- API トークン認証 vs OAuth 2.0
- Live Artifact とは（通常 Artifact との違い、MCP コネクタ連携、Pro 以上必須）

**ハンズオン（65分）**
- Part 1: GAS でデータ収集（45分）
  - Step 1: Kintone「請求案件」アプリ作成 + API トークン発行
  - Step 2: GAS プロジェクトを Clasp で作成 + スクリプトプロパティ登録
  - Step 3: Claude Code で 6 ファイル分割の GAS を生成 + clasp push + 動作確認
  - Step 4: 毎朝 6 時の時間トリガー設定 + Slack 通知
- Part 2: Live Artifact 化（20分）
  - Step 5: Claude.ai に Google Sheets MCP コネクタを接続
  - Step 6: ダッシュボード生成 → Live Artifact 化
  - Step 7: ローカル運用 + 社内共有の代替手段（スクショ / PDF / Sheets URL）

**まとめ（5分）**
- 運用ルール（5か条）— トリガー監視 / 鍵ローテーション / Live Artifact は自分専用・Sheets URL で代替共有 / Sheets バックアップ / 失敗時通知
- 拡張先の選択肢 — invox / freee / マネフォ / Shopify / GA4 などへの横展開
- 他応用編との接続 — 応用1（Git/GitHub）/ 応用2（Drive セキュリティ）/ 応用3（GAS）/ 応用4（API 連携）の集大成

**Notion 教材（自習用・辞書）**
- 配布スキル `kintone-api` リファレンス（query 文法・cursor API・エラーコード）
- 配布スキル `gas-clasp` リファレンス（Critical Rules・templates.md・quotas.md）
- 配布スキル `invox-api` リファレンス（OAuth 2.0 フロー・契約者向け）
- invox 連携拡張ガイド（`references/invox-連携ガイド.md`）
- スクリプトプロパティ管理チートシート
- **Live Artifact のローカル運用と社内共有の代替手段チートシート（スクショ / PDF / Sheets URL）**
- 横展開アイデア集（在庫管理 / 受注 / 勤怠 / KPI 等）

---

## MENTA 伴走プラン

### 対象
- 基本コース修了者 or Claude Code を既に使っている非エンジニア
- 自分のやりたいことがあるが、一人だと詰まる人

### プラン内容

| 項目 | 内容 |
|------|------|
| オンライン相談 | 週1回 30分（Zoom/Google Meet） |
| チャットサポート | Slack or Discord で随時質問（24h以内返信） |
| 伴走テーマ例 | 業務自動化 / Webアプリ開発 / Skills作成 / MCP連携 / DX推進 |
| 教材アクセス | Notion 辞書セクション全開放 |
| 月次振り返り | 月1回、学習の進捗と次の目標を整理 |

### 伴走で扱えるテーマ

**アプリ開発系**
- 社内ツール（勤怠管理、在庫管理、顧客管理等）
- LP / ポートフォリオサイト
- SaaS のプロトタイプ

**業務自動化系**
- スプレッドシート / Excel の自動処理
- メール・Slack の自動化
- 定型業務の Skills 化

**AI活用系**
- Claude Code Skills の設計・作成
- MCP サーバーとの連携
- AIエージェントのワークフロー設計

**ビジネス活用系**
- 提案書・マニュアルの自動生成
- データ分析・レポート作成
- DX推進の戦略設計

---

## ビジネスユース（将来拡張）

基本コース・MENTA で実績を積んだ後、以下を展開:

### 単発講座（ココナラ or 法人研修）

| テーマ | 内容 |
|--------|------|
| Claude Code Skills 入門 | 繰り返し業務をスキル化する方法 |
| MCP 連携入門 | 外部ツール（Slack/Google/DB）との接続 |
| AI×財務管理 | PL自動生成、予実管理、キャッシュフロー予測 |
| AI×タスク管理 | Backlog/GitHub連携、日次ブリーフィング自動化 |
| AI×資料作成 | 提案書PPTX、操作マニュアルPDF、契約書レビュー |
| AI×SNSマーケ | GA4 / Shopify / X / ニュースRSS 連携、週次KPI自動レポート |
| 管理職向けDX推進 | AI導入の意思決定フレームワーク、ROI算出 |

### 法人研修パッケージ
- 半日体験: 5万円（助成金で実質1.25万円）
- 2日間実践: 50万円（助成金で実質12.5万円）
- 伴走型DX推進: 月額30万円 × 6ヶ月

---

## 受講者の前提条件

- PC（Mac 推奨、Windows 可）を持っている
- ブラウザが使える
- プログラミング経験は不要
- Anthropic のアカウント（Pro プラン以上）を用意できる

## 講師プロフィール（訴求ポイント）

- 非エンジニア出身でClaude Code Skills 81個を運用
- SES企業取締役として全社DX推進を実践中
- Qiita で Claude Code 実践記事を15本以上公開
- 「コードを書かずにAIで業務を変える」を自ら体現

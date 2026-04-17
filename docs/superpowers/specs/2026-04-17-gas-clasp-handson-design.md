# 応用3: Claude Code で GAS 開発入門（Clasp セットアップ編）— 教材設計

## 背景と目的

基本コース（第1〜4回）と応用1・2（VSCode Git、Google Drive MCP）に続く応用コースの第3弾。
受講者が「Google Apps Script をブラウザのエディタではなく、手元の Claude Code で書いて Google へ送る」体験を得ることをゴールとする。

これまでの応用コースは「既存ツールを安全に使う」方向の内容だったが、本回は**ローカル開発環境 × Claude Code × Google Workspace の組み合わせで業務自動化を自作する**という、より能動的な切り口を提供する。

## 対象読者と前提

- 基本コース第1〜2回修了（Node.js・Claude Code が動く状態）
- **Node.js 22.0.0 以上**（Clasp v3 系の必須要件。基本コース時点で古い Node を入れた受講者はアップグレードが必要）
- Google アカウントを所有（Workspace でも個人でも可）
- Git/GitHub の基礎は不要（本回では扱わない）

## ゴール（受講後の状態）

1. 自分の PC に Clasp がインストールされ、Google アカウントと連携できている
2. Claude Code に日本語で指示して GAS コードを生成できる
3. `clasp push` でローカルのコードを Google 側の Apps Script プロジェクトに反映できる
4. `clasp pull` で逆方向の同期もできる
5. スクリプトエディタで実行して、成果物（勤怠記録シート）が生成されることを確認できる

## 成果物ファイル

- `07_応用3_ClaudeCode_GAS_Clasp.md` — 教材本体（新規）
- `curriculum.md` — 応用コース一覧に「応用3」を追記（更新）

## 構成（90分）

### 講義（15分）
- GAS とは（Google Workspace を操作できる JavaScript 実行環境）
- 従来のブラウザエディタ開発の限界（Claude Code が使えない、履歴管理が弱い、補完が弱い）
- Clasp とは（Google 公式 CLI。ローカル ⇄ Google 間の同期ツール）
- Claude Code × Clasp の組み合わせメリット（自然言語で書ける／CLAUDE.md にルールを蓄積／差分管理ができる）

### ハンズオン（65分）

#### フェーズ1: 環境セットアップ（20分）
1. Node.js のバージョン確認（`node -v` → 22.0.0 以上であること）
   - 古い場合のアップグレード手順（nvm or 公式インストーラ）も補足
2. Clasp グローバルインストール（`npm install -g @google/clasp`）
3. `clasp login`（ブラウザで Google 認証→許可→ターミナルに戻る。`~/.clasprc.json` にトークン保存）
4. Apps Script API の有効化（`https://script.google.com/home/usersettings` で ON）

#### フェーズ2: 新規プロジェクト作成（10分）
1. 作業ディレクトリ作成（例: `~/Desktop/gas-kintai`）
2. `clasp create --title "勤怠記録ジェネレーター" --type standalone`
3. 生成されたファイル構成の確認（`.clasp.json` / `appsscript.json` / `Code.js`）
4. 補足: ローカルの `.js` は `clasp push` 時に Google 側で `.gs` として扱われる仕組みを説明

#### フェーズ3: Claude Code で GAS コード生成（25分）
1. そのディレクトリで Claude Code を起動
2. CLAUDE.md 作成（「このプロジェクトは Google Apps Script。出力先は Code.js 等の .gs 相当」など）
3. 指示例: 「今月1ヶ月分の勤怠記録スプレッドシートを新規作成する関数を書いて。列は日付・曜日・出勤・退勤・休憩・実働・備考。日付行は営業日ごとに色分けして」
4. `clasp push` で Google 側へ反映
5. スクリプトエディタで関数を実行 → Google Drive に生成されたスプレッドシートを確認
6. 追い指示: 「土日の行はグレーにして、ヘッダーは太字で青背景にして」→ 再 push → 再実行

#### フェーズ4: pull の体験（10分）
1. ブラウザのスクリプトエディタで1行だけ編集
2. 手元で `clasp pull` → ローカルに変更が降りてくることを確認
3. 「ブラウザでもローカルでも触れる」という両輪感覚を体得

### まとめ・次回案内（10分）
- 既存スプレッドシートに紐付ける運用（`clasp clone`）
- トリガー（onEdit、時間ベース）で定期実行する世界観
- 応用テーマ: Gmail 自動化／Google Form 連携／Slack Webhook 連携

## Notion 教材（自習用・辞書）

- Clasp コマンドチートシート（login / create / clone / push / pull / open / logs）
- 認証トラブル対処集（Apps Script API 未有効化、ブラウザ未起動、トークン失効）
- `.clasp.json` と `appsscript.json` の読み方
- Claude Code への GAS 指示文テンプレート10選（集計／通知／定期実行／メール送信 等）
- Workspace 管理者が OAuth アプリを制限しているケースの相談テンプレート

## 画像素材（本回で新規作成が必要なもの）

- `images/gas-clasp-architecture.png` — ローカル ⇄ Clasp ⇄ Google Apps Script の関係図
- スクリーンショット（`screenshots/` 配下）:
  - `G1_clasp_login_browser.png` — Google 認証画面
  - `G2_clasp_create_terminal.png` — `clasp create` 実行後のターミナル
  - `G3_claude_code_gas_prompt.png` — Claude Code に指示を出している画面
  - `G4_spreadsheet_result.png` — 生成された勤怠記録シート
  - `G5_script_editor_run.png` — スクリプトエディタでの実行

※ 画像は今回の教材追加では **ファイルパスのみ仮で埋め込み、実物は後日用意**（既存応用コースと同じ運用）。

## セキュリティ注意書き

教材内で明記すべき点:
- `clasp login` は OAuth トークンを `~/.clasprc.json` に保存する（個人PC限定で使うこと）
- 共有PCでは必ず `clasp logout`
- `.clasp.json` にはスクリプトID が入るが秘匿情報ではない（ただし個人の作業ログとしてGit公開する際は注意）
- 業務データを扱う場合は IT 部門に OAuth アプリの許可状況を確認する

## CLAUDE.md への追記方針

リポジトリの CLAUDE.md は「教材リポジトリとしての運用ルール」を記述している。
本教材ファイル追加に伴う CLAUDE.md の変更は**不要**（既存の運用ルール＝画像パス統一、未経験者向け言い回し、技術スタック前提が、そのまま本教材にも当てはまる）。

## スコープ外（今回やらないこと）

- Google Workspace 管理者コンソール側の OAuth アプリ管理（別回で扱う）
- Git/GitHub との連携（応用1で既習。本回では触れない）
- TypeScript での GAS 開発（`--type ts`）— 非エンジニア向けには情報過多なので省略
- Web Apps としてデプロイして URL 公開する手順 — 90分枠を超えるため別回候補

## 成功基準

1. 受講者が自分の PC で `clasp push` を成功させ、Google Drive に勤怠シートが生成される
2. 受講者が Claude Code への追い指示で書式（色・太字）を変更し、再 push で反映できる
3. `curriculum.md` の応用コース一覧から本教材の存在が分かる

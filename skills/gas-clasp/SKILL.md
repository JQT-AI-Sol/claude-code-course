---
name: gas-clasp
description: Google Apps Script を Claude Code から Clasp 経由で扱うスキル。基本は「手元に Clasp v3 + Node.js 20 以上が入っている前提で push / pull / トリガー設定までを支援」する。入っていなければセットアップ手順を案内する。スクリプトプロパティ・時間トリガー・UrlFetchApp の基本パターンも提供。「Clasp」「clasp」「GAS」「Apps Script」「clasp push」「Apps Script トリガー」「スクリプトプロパティ」が出てきたら発火する。
---

# gas-clasp スキル

応用5「請求データ自動収集ダッシュボード」で、Claude Code から GAS を Clasp 経由で扱うためのスキル。

## 責務

**基本**: 手元に Clasp が入っている前提で、Claude Code から GAS を書く → `clasp push` → 動かす、までを最短で支援する。

**フォールバック**: Clasp や Node.js が入っていなければセットアップ手順を案内する。

それ以上は深追いしない。スクリプトプロパティ・時間トリガー・UrlFetchApp は「Clasp 環境ができたあとの実装支援」として最小限のテンプレを提供する程度に留め、詳細・パターン集は `references/` に分離してある。

範囲外（本スキル外の高度トピック・公式 `google-apps-script` スキルがある環境ではそちらを参照）:
- Clasp の TypeScript / Rollup バンドル運用
- Web App / API Executable のデプロイ
- GAS 上での HTML サイドバー UI 開発
- カスタムスプレッドシート関数（`=MY_FUNCTION()`）の開発

---

## Step 0: 環境診断と分岐

ユーザーから「GAS 始めたい」「Clasp 使いたい」と言われたら、まずこの 3 つを並列で実行して状態を判定する。

```bash
node -v
npm -v
clasp --version
```

| 項目 | 期待値 | 不足のときの行き先 |
|------|--------|------------------|
| Node.js | `v20.x.x` 以上（推奨 22 LTS） | Step 1（Node 導入） |
| npm | `10.x` 以上 | Node 同梱なので Step 1 で解決 |
| Clasp | `3.x.x` | Step 2（Clasp 導入） |

> 出典: Clasp v3 の `package.json` engines は `"node": ">=20.0.0"`。Node 20 でも動作するが、サポート期間の長い 22 LTS を推奨。

### 分岐ロジック

- **3 つとも揃っている → 基本フロー**: Step 1〜3 はスキップして **Step 4（プロジェクト作成 / clone）** から進める
- **どれか欠けている → セットアップフロー**: 該当 Step だけ実施 → 揃ったら Step 4 へ合流

> ⚠️ **Clasp は v3 系を推奨**
> v2 系は機能後退・新コマンドに非対応・TypeScript ネイティブ対応も廃止されている。`clasp --version` で `2.x` が出たら **v3 にアップグレード** すること。

> 💡 配下に診断スクリプトあり: `references/diagnose.sh` を実行すると上記の判定をワンコマンドで済ませられる。

---

# セットアップフロー（不足部品があるとき）

## Step 1: Node.js を 20 以上にする（推奨 22 LTS）

### Mac（Homebrew がある場合）

```bash
brew install node@22         # 推奨は 22 LTS（20 でも可）
brew link --overwrite node@22
```

### Mac（nvm を使う場合・複数バージョン共存）

```bash
# nvm 自体が無ければ
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# 新シェルを開き直して
nvm install 22
nvm use 22
nvm alias default 22
```

### Windows

[Node.js 公式](https://nodejs.org/) から **22 LTS の Windows Installer (.msi)** をダウンロードして実行（20 LTS でも可）。完了後 PowerShell を再起動して `node -v` で確認。

または winget:

```powershell
winget install OpenJS.NodeJS.LTS
```

---

## Step 2: Clasp v3 をインストール

```bash
# 既に v2 系が入っている場合は先にアンインストール
npm uninstall -g @google/clasp

# v3 系をインストール
npm install -g @google/clasp@latest

# 確認
clasp --version   # → 3.x.x が表示されれば OK
```

### Apps Script API の有効化

ブラウザで以下を開いて **「Google Apps Script API」をオンに**:

```
https://script.google.com/home/usersettings
```

これを忘れると `clasp create-script` が必ず失敗する。

---

## Step 3: clasp login

```bash
clasp login
```

ブラウザが起動して Google ログイン画面 → 権限同意。**作業対象のスプレッドシートを所有している Google アカウントでログインする** こと。

### 複数アカウント運用（仕事用 + 個人用など）

```bash
clasp login -u personal      # 個人アカウントで認証 → "personal" として保存
clasp login -u work          # 仕事アカウントで認証 → "work" として保存

clasp -u work push           # 仕事アカウントで push
clasp -u personal create-script ...   # 個人で作成
```

### 認証エラー時の典型対応

| エラー | 原因 | 対処 |
|--------|------|------|
| `Drive ACL permission denied` | ログインアカウントと対象 GAS のオーナーが不一致 | `clasp logout` → 正しいアカウントで `clasp login` |
| `Apps Script API has not been used` | API 未有効化 | https://script.google.com/home/usersettings で ON |
| `invalid_grant` | 認証情報の期限切れ | `clasp logout && clasp login` |

---

# 基本フロー（Clasp が使える状態）

## Step 4: プロジェクト新規作成

応用5 では「スプレッドシートに紐付かない standalone スクリプト」で作る（複数シートを操作する可能性があるため）。

```bash
# 作業ディレクトリを作成
mkdir billing-gas && cd billing-gas

# プロジェクト初期化
clasp create-script --title "請求ダッシュボード自動更新" --type standalone --rootDir ./src
```

完了すると以下が生成される:

```
billing-gas/
├── .clasp.json            # scriptId の保存先
├── src/
│   ├── appsscript.json    # GAS マニフェスト
│   └── (空)
```

ここに `src/main.js` を作って Claude Code に書かせる。

### 既存スプレッドシートに紐付ける場合

```bash
# 既存スクリプトの scriptId（URL の /d/{ID}/edit）を控えて
clasp clone-script <scriptId> --rootDir ./src
```

### push / pull

```bash
clasp push        # ローカル → Google
clasp push --watch  # ファイル変更を検知して自動 push
clasp pull        # Google → ローカル（ブラウザで直接編集したものを取り込む）
```

---

## Step 5: スクリプトプロパティで API キーを安全に管理

**絶対にコード本文に API キーを書かない**。GAS のスクリプトプロパティを使う。

### 設定方法

1. ブラウザで対象 GAS プロジェクトを開く（`clasp open-script`）
2. 左メニュー ⚙️「プロジェクトの設定」
3. 「スクリプト プロパティ」セクション > 「スクリプト プロパティを追加」
4. キーと値を入力 → 「スクリプト プロパティを保存」

### コードから読む

```javascript
function getConfig_() {
  const props = PropertiesService.getScriptProperties();
  const config = {
    kintoneSubdomain: props.getProperty('KINTONE_SUBDOMAIN'),
    kintoneAppId:     props.getProperty('KINTONE_APP_ID'),
    kintoneToken:     props.getProperty('KINTONE_TOKEN'),
    sheetId:          props.getProperty('TARGET_SHEET_ID')
  };

  const missing = Object.entries(config)
    .filter(([_, v]) => !v)
    .map(([k]) => k);

  if (missing.length > 0) {
    throw new Error(`必須プロパティが未設定: ${missing.join(', ')}`);
  }
  return config;
}
```

### コードからプロパティを書く（初回セットアップ自動化）

```javascript
function setupProperties_() {
  // 自分のローカル環境で1回だけ実行する想定。実行後はこの関数を削除する
  PropertiesService.getScriptProperties().setProperties({
    KINTONE_SUBDOMAIN: 'your-tenant',
    KINTONE_APP_ID:    '123',
    // KINTONE_TOKEN は UI から手で入れる（コードに残さない）
  });
}
```

> ⚠️ **トークンを setProperties で渡すコードを書くと、Git に push して漏洩する**。**UI から手入力** が原則。

---

## Step 6: 時間トリガー（定期実行）

毎朝 6 時に自動実行するためのトリガー設定。**コード経由が再現性が高くておすすめ**。

### コード経由（推奨）

```javascript
/**
 * 毎朝6時にmain関数を実行するトリガーをセット。
 * 1回だけ手動実行すればよい。
 */
function installDailyTrigger() {
  // 既存トリガーをクリア（重複防止）
  const existing = ScriptApp.getProjectTriggers();
  for (const t of existing) {
    if (t.getHandlerFunction() === 'main') {
      ScriptApp.deleteTrigger(t);
    }
  }

  // 新規セット: 毎朝6時台に実行
  ScriptApp.newTrigger('main')
    .timeBased()
    .atHour(6)
    .everyDays(1)
    .create();

  Logger.log('トリガー設定完了: 毎日 6時台に main() を実行');
}
```

実行手順:
1. `clasp push`
2. `clasp open-script` で GAS エディタを開く
3. 関数選択で `installDailyTrigger` を選んで実行
4. 初回は権限同意ダイアログ（「詳細 > 〈プロジェクト名〉（安全ではないページ）に移動 > 許可」／英語 UI: 「Advanced > Go to 〈project〉 (unsafe) > Allow」）

### UI 経由（補助）

1. GAS エディタ > 左の ⏰「トリガー」
2. 右下「トリガーを追加」
3. 実行する関数: `main`
4. デプロイ時の関数: `Head`
5. イベントのソース: `時間主導型`
6. 時間ベースのトリガーのタイプ: `日付ベースのタイマー`
7. 時刻: `午前6時〜午前7時`
8. 保存

### トリガーの確認・削除

```javascript
function listTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => {
    Logger.log(`${t.getHandlerFunction()} - ${t.getEventType()}`);
  });
}

function deleteAllTriggers() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
}
```

> 💡 **時間トリガーの精度**
> GAS の時間トリガーは「指定した時間帯のどこか」で起動する（6時00分00秒ピッタリではなく、6:00〜6:59のいずれか）。秒精度が要るなら別の仕組みを検討。

---

## Step 7: UrlFetchApp 外部 API 呼び出しテンプレ

Kintone・Slack・Discord・各種 SaaS の Web API を叩くときの定型。

```javascript
/**
 * GET リクエストの定型
 */
function apiGet_(url, headers) {
  const res = UrlFetchApp.fetch(url, {
    method: 'get',
    headers: headers || {},
    muteHttpExceptions: true   // 4xx/5xx でも例外を投げない（自分でハンドリング）
  });

  const code = res.getResponseCode();
  const body = res.getContentText();

  if (code < 200 || code >= 300) {
    throw new Error(`API GET 失敗 (${code}): ${url}\n${body}`);
  }
  return JSON.parse(body);
}

/**
 * POST リクエストの定型（JSON ボディ）
 */
function apiPost_(url, headers, payload) {
  const res = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: headers || {},
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const code = res.getResponseCode();
  const body = res.getContentText();

  if (code < 200 || code >= 300) {
    throw new Error(`API POST 失敗 (${code}): ${url}\n${body}`);
  }
  return JSON.parse(body);
}
```

### Slack Webhook で結果通知

```javascript
function notifySlack_(text) {
  const webhook = PropertiesService.getScriptProperties().getProperty('SLACK_WEBHOOK');
  if (!webhook) return;  // 設定なしならスキップ
  UrlFetchApp.fetch(webhook, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({ text })
  });
}
```

---

## Step 8: 応用5 用の完全な実装パターン

応用5 ハンズオンで実際に動かす GAS は `main()` → 設定取得 → Kintone 取得 → Sheets 更新 → Slack 通知 という流れ。**完全なコードと 7 ファイル構成は `references/templates.md` に置いてある**ので、Claude はそれをそのまま流用する。

主要な関数構成（`templates.md` に詳細）:

| 関数名 | 責務 |
|--------|------|
| `main` | エントリポイント。try/catch で全体を囲み、失敗時は Slack に通知 |
| `getConfig` | スクリプトプロパティから設定を取得・必須チェック |
| `fetchKintoneRecords` | Kintone API 呼び出し（kintone-api スキル参照） |
| `updateSheet` | Sheets への全件洗い替え更新 |
| `notifySlack` | 結果通知（Webhook） |
| `installDailyTrigger` | 毎朝 6 時のトリガー設定（1回だけ手動実行） |

---

## Critical Rules（要約）

Claude がコード生成時に **無意識で違反しやすい** 7 ルール。**生成コードは必ずこのリストで自己レビュー** すること。詳細・コード例・違反時のエラーは `references/critical-rules.md` を参照。

1. **末尾 `_` ルール** — エントリポイント関数（`main` / `installDailyTrigger`）は public（末尾 `_` なし）。内部ヘルパーは `_` 付き
2. **バッチ操作** — `getRange().getValues()` / `setValues()`。セル単位ループは 70 倍遅い
3. **V8 ランタイム制約** — `setTimeout` / `fetch` / `FormData` / `URL` / `crypto` は使えない。GAS 代替（`Utilities.sleep` / `UrlFetchApp.fetch` 等）へ
4. **`function` 宣言形式必須** — `const main = () => {}` ではトリガーから呼べない
5. **`SpreadsheetApp.flush()`** — シート書き込み後の return 直前に必ず呼ぶ
6. **Installable Trigger を使う** — 時間ベース / `UrlFetchApp` を使うなら Simple ではなく Installable
7. **シークレットは Properties へ** — トークンをコード本文に直書きしない（GitHub push 即漏洩）

破ったときの代表エラーと対処は `references/critical-rules.md` 末尾の **Error Prevention 早見表** に集約。

---

## 制限と落とし穴

| 項目 | 制限 | 対処 |
|------|------|------|
| **実行時間** | 1回 6 分 | 大量処理は分割 + state を Properties に保存 |
| **UrlFetchApp** | 1日 20,000 リクエスト | バッチ化 |
| **メール送信** | 1日 100通（無料）/ 1,500通（Workspace） | 通知は Slack/Discord に逃す |
| **トリガー** | 1ユーザー / 20 個まで | 不要なトリガーは削除 |
| **ログ** | 7日で消える | 重要ログは Sheets に書き出す |
| **Properties の値サイズ** | 1 プロパティ 9KB / 合計 500KB | 大きな state は Drive ファイルへ |

詳細クォータは `references/quotas.md` を参照。

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `clasp push` で 403 | アカウント不一致。`clasp logout && clasp login` |
| トリガー実行されない | トリガーログ確認（GAS エディタ > 「実行数」） / クォータ確認 |
| 「承認が必要です」と毎回出る | スコープが増えた可能性。手動実行で再承認 |
| `Cannot read property 'value' of undefined` | Kintone レコードに該当フィールドが無い。`r['フィールド'] ? r['フィールド'].value : ''` でガード |
| `SpreadsheetApp.openById` で 404 | sheetId 誤り or GAS オーナーがシート閲覧権なし |

## Reference Index

トピックが具体的になったら以下のリファレンスをロードする:

| ファイル | 読むべきタイミング |
|---------|------------------|
| `references/critical-rules.md` | コード生成前後のセルフレビュー / Error Prevention 早見表 |
| `references/diagnose.sh` | 環境診断を一括実行したいとき（ユーザーに実行を促す） |
| `references/templates.md` | 応用5 用の GAS プロジェクト雛形（7ファイル構成）が必要なとき |
| `references/patterns.md` | カスタムメニュー / トリガー / メール / PDF / Properties / API 呼び出しの実装パターン |
| `references/quotas.md` | クォータ・実行時間制限・デバッグ手順・デプロイチェックリスト |

---

## このスキルの使い方（Claude 向け）

判断は **「Clasp が使える状態か」** の一点で分岐する:

```
ユーザー「GAS 書きたい / clasp push したい / 定期実行したい」
        ↓
   Step 0 で環境診断
        ↓
   ┌────────────┴────────────┐
   ▼                          ▼
[基本フロー]                [セットアップフロー]
Clasp 使える                Clasp 未導入
   ↓                          ↓
Step 4 へ                  Step 1〜3 を実施
（プロジェクト作成）         ↓
   ↓                       揃ったら Step 4 へ
Step 5〜7 を必要に応じて
（実装支援）
```

**基本フロー時の判断**:

- プロジェクト未作成なら Step 4 で初期化（雛形が必要なら `references/templates.md`）
- API キーが絡むなら Step 5 を必ず案内（コード直書き禁止）
- 定期実行なら Step 6 で時間トリガーをコード経由でセット
- 外部 API なら Step 7 のテンプレを流用
- 生成したコードは Critical Rules（要約 7 項目）でセルフレビュー

**禁止事項**:
- ユーザーの API キー / トークン実値を含むコードを生成しない
- `setProperties({ KINTONE_TOKEN: '実トークン' })` のような書き方を提案しない（手動入力誘導）
- 古い Clasp v2 系の手順を提案しない
- アロー関数で `const main = () => { ... }` のような形をエントリポイント関数に使わない
- `setTimeout` / `fetch` などブラウザ専用 API を使わない（必ず GAS 代替を）

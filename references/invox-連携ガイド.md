# invox 受取請求書 連携ガイド（応用5 拡張）

> 📌 **この資料の位置づけ**
> 応用5 本編「請求データ自動収集ダッシュボード」では、データソースを **Kintone のみ** で構成しています。本資料は **invox 受取請求書（プロフェッショナルプラン契約済み）** を併用したい受講者向けの拡張ガイドです。本編完走後、社内で本格運用する段階で読んでください。

---

## なぜ別資料にしたのか

invox 受取請求書 API は、以下の制約があり **無料トライアル / 無償アカウントでは利用できません**。応用5 のハンズオンに組み込むには受講者全員に契約を求める必要があり、現実的でないため切り離しました。

| 制約 | 内容 |
|------|------|
| **プラン要件** | プロフェッショナルプラン（有料）必須。無料トライアル不可 |
| **client_id 発行** | invox サポートに事務申請が必要（メールでの確認・営業日 2〜3 日） |
| **認証方式** | OAuth 2.0（client_credentials を Basic 認証で送る Authorization Code フロー） |
| **トークン有効期限** | access_token: 10 時間 / refresh_token: 無期限 |

ただし、契約済みなら **Kintone と並列で同じ GAS から取得できる** ので、応用5 のアーキテクチャは invox を後付けする前提で組まれています。

---

## アーキテクチャ全体像（invox 追加版）

```
┌──────────────┐        ┌──────────────┐
│   Kintone    │        │    invox     │
│  (請求案件)   │        │ (受領請求書)  │
└──────┬───────┘        └──────┬───────┘
       │ X-Cybozu-API-Token    │ Bearer access_token
       │ (API トークン)          │ (OAuth 2.0)
       └─────────┬─────────────┘
                 ▼
       ┌─────────────────────┐
       │ Google Apps Script  │  ← 同じ main() に2系統合流
       └─────────┬───────────┘
                 ▼
       ┌─────────────────────┐
       │  Google Sheets      │  ← タブ「案件」「受領」「突合」
       └─────────┬───────────┘
                 ▼
       ┌─────────────────────┐
       │ Claude Live Artifact│  ← 突合済みダッシュボード
       └─────────────────────┘
```

「案件」タブ（Kintone から）と「受領」タブ（invox から）を `案件番号` 等の共通キーで突合し、「突合」タブを生成する形が王道です。

---

## 利用開始までの流れ

1. **invox プロフェッショナルプラン** を契約（https://invox.jp/ から見積依頼）
2. **invox サポートに API 利用申請**:
   - 企業 ID（[設定] > [会社] で確認できる ID）
   - 接続用ユーザのメールアドレス（[設定] > [スタッフ] に登録済みの管理者ユーザ）
   - 利用用途（「Google Apps Script から請求書一覧を取得しスプレッドシートへ転記」など）
3. invox サポートから **client_id** と **client_secret** がメールで届く（営業日 2〜3 日）
4. リダイレクト URL を invox サポートに **事前申請** する（任意の URL は使えない。テスト用に `http://localhost:8080/callback` を申請するのが現実的）
5. 認可フローを 1 回だけ手動実行して **refresh_token を取得**
6. GAS のスクリプトプロパティに保存して以後は自動化（**企業 ID `INVOX_COMPANY_CODE` も同時に登録**）

---

## OAuth 2.0 認可フロー（初回 1 回だけ手動）

### ステップ 1: 認可コードを取得

ブラウザで以下の URL を開く（`{CLIENT_ID}` と `{REDIRECT_URI}` は invox サポートに事前申請したものに置換）:

```
https://api.invox.jp/oauth2/authorize/
  ?client_id={CLIENT_ID}
  &response_type=code
  &redirect_uri={REDIRECT_URI}
  &scope=read+write
```

> ⚠️ **`scope` は `read write`** （半角スペース or `+` 区切り）。`receive_invoice` ではない（サービス名と scope を混同しない）。読み取りだけなら `read` のみで OK。
> ⚠️ **`redirect_uri` は事前申請制**。invox では任意 URL を使えない。`urn:ietf:wg:oauth:2.0:oob`（OOB）が使えるかは公式ドキュメントに明記なし。事前にサポート確認。

invox にログイン → 同意ボタンを押すと、画面に **認可コード**（1分以内に使い切らないと失効）が表示される。

### ステップ 2: 認可コードをアクセストークンに交換

ターミナルで以下を実行（`{CLIENT_ID}`、`{CLIENT_SECRET}`、`{AUTH_CODE}`、`{REDIRECT_URI}` を置換）:

```bash
CLIENT_ID="..."
CLIENT_SECRET="..."
AUTH_CODE="認可コード"
REDIRECT_URI="申請したリダイレクトURL"

curl -X POST https://api.invox.jp/oauth2/token/ \
  -u "${CLIENT_ID}:${CLIENT_SECRET}" \
  -d "grant_type=authorization_code" \
  -d "code=${AUTH_CODE}" \
  -d "client_id=${CLIENT_ID}" \
  -d "redirect_uri=${REDIRECT_URI}"
```

> ⚠️ Basic ヘッダ（`-u`）と **body の `client_id` 両方** が必要。

レスポンス例:

```json
{
  "access_token":  "eyJhbGciOi...",
  "token_type":    "Bearer",
  "expires_in":    36000,
  "refresh_token": "rt_xxxxxxxx",
  "scope":         "read write"
}
```

### ステップ 3: 取得した値を GAS のスクリプトプロパティへ保存

| キー | 値 |
|---|---|
| `INVOX_CLIENT_ID` | 受領した client_id |
| `INVOX_CLIENT_SECRET` | 受領した client_secret |
| `INVOX_REFRESH_TOKEN` | 上のレスポンスの refresh_token |
| `INVOX_COMPANY_CODE` | 企業 ID（設定 > 会社、≤30文字）。**全 API 呼び出しで必須** |

`access_token` は 10 時間で失効するので **保存しない**。GAS の実行ごとに `refresh_token` から再取得する。

---

## GAS 実装サンプル

### トークン取得（毎回）

```javascript
/**
 * refresh_token から新しい access_token を取得する。
 * GAS 実行ごとに呼ぶ（10時間有効なのでキャッシュしてもよい）。
 */
function getInvoxAccessToken_() {
  const props = PropertiesService.getScriptProperties();
  const clientId     = props.getProperty('INVOX_CLIENT_ID');
  const clientSecret = props.getProperty('INVOX_CLIENT_SECRET');
  const refreshToken = props.getProperty('INVOX_REFRESH_TOKEN');

  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error('invox の認証情報が不足: INVOX_CLIENT_ID / INVOX_CLIENT_SECRET / INVOX_REFRESH_TOKEN');
  }

  // 公式仕様: Basic ヘッダ + body の client_id 両方が必要
  const basic = Utilities.base64Encode(`${clientId}:${clientSecret}`);
  const res = UrlFetchApp.fetch('https://api.invox.jp/oauth2/token/', {
    method: 'post',
    headers: { 'Authorization': `Basic ${basic}` },
    payload: {
      grant_type:    'refresh_token',
      refresh_token: refreshToken,
      client_id:     clientId        // body 側にも必須
    },
    muteHttpExceptions: true
  });

  if (res.getResponseCode() !== 200) {
    throw new Error(`invox トークン更新失敗: ${res.getContentText()}`);
  }

  return JSON.parse(res.getContentText()).access_token;
}
```

### 受領請求書の一覧取得

```javascript
/**
 * invox から受領請求書を取得する。
 *
 * 公式仕様:
 *   GET /api/public/invoice_receive/invoice/list
 *   必須: invox_company_code
 *   レスポンス: { count, next, previous, results: [...] }
 *   ページング: next が null になるまで（per_page パラメータは無い）
 *
 * @param {Object} filters - 検索条件（任意）
 *   - invoice_date_from / invoice_date_to: 請求日 (YYYY-MM-DD)
 *   - payment_plan_date_from / payment_plan_date_to: 支払予定日
 *   - posting_date_from / posting_date_to: 計上日
 *   - fixed_only: "true" / "false"
 *   - export_status / payment_method / department_code / include_sub_departments
 * @returns {Array} 請求書配列
 */
function fetchInvoxInvoices_(filters) {
  const props = PropertiesService.getScriptProperties();
  const companyCode = props.getProperty('INVOX_COMPANY_CODE');
  if (!companyCode) {
    throw new Error('INVOX_COMPANY_CODE が未設定（企業 ID。設定 > 会社で確認）');
  }

  const token = getInvoxAccessToken_();
  const baseUrl = 'https://api.invox.jp/api/public/invoice_receive/invoice/list';

  const qs = Object.entries({
    invox_company_code: companyCode,   // 必須
    ...(filters || {}),
    page: 1
  })
    .filter(([_, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&');

  const invoices = [];
  let nextUrl = `${baseUrl}?${qs}`;

  // next ベースでページング（per_page は存在しない）
  while (nextUrl) {
    const res = UrlFetchApp.fetch(nextUrl, {
      method: 'get',
      headers: { 'Authorization': `Bearer ${token}` },
      muteHttpExceptions: true
    });

    if (res.getResponseCode() !== 200) {
      throw new Error(`invox API エラー: ${res.getContentText()}`);
    }

    const body = JSON.parse(res.getContentText());
    invoices.push(...(body.results || []));
    nextUrl = body.next || null;       // 終端判定
  }

  return invoices;
}
```

> ⚠️ **個別フィールド名（`invoice_number`, `supplier_name`, `total_amount` 等）は公開情報からの推測**です。契約後に提供される公式 API ドキュメントで正しい命名に置き換えてください。一覧 API のレスポンス構造（`count` / `next` / `previous` / `results`）と必須パラメータ（`invox_company_code`）、エンドポイント パスは公式仕様で確認済みです。

### main() への組み込み

```javascript
function main() {
  try {
    const config = getConfig();

    // Kintone から請求案件
    const kintoneRecords = fetchKintoneRecords(config);
    updateSheet(kintoneRecords, config.sheetId, '案件');

    // invox から受領請求書（今月分・確定済み）
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const invoxInvoices = fetchInvoxInvoices_({
      invoice_date_from: Utilities.formatDate(firstDay, 'Asia/Tokyo', 'yyyy-MM-dd'),
      fixed_only:        'true'
    });
    updateInvoxSheet_(invoxInvoices, config.sheetId, '受領');

    // 突合
    reconcileSheets_(config.sheetId);

    notifySlack(`✅ 案件 ${kintoneRecords.length} / 受領 ${invoxInvoices.length} 件 を更新`);
  } catch (e) {
    notifySlack(`❌ 失敗: ${e.message}`);
    throw e;
  }
}
```

---

## レート制限と運用上の注意

| 項目 | 制限 |
|------|------|
| **1リクエスト** | 50 MB まで |
| **仕訳エクスポート** | 1 回 100 件まで |
| **ファイル一括 DL** | 1 回 100 件まで |
| **access_token** | 10 時間 |
| **refresh_token** | 無期限（ただし会社が API 利用を解約すれば失効） |

毎朝 6 時の自動実行で月次〜日次の請求書を取得する程度であれば、上限に当たることはほぼありません。

---

## トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| 401 Unauthorized | access_token 期限切れ | `getInvoxAccessToken_` で再取得（10時間ごとに再発行） |
| 403 Forbidden | プラン要件未充足 / スコープ不足 | プラン契約状況確認、scope を見直し |
| `invalid_grant` (token) | refresh_token 失効 | 認可フロー（ステップ 1〜3）をやり直し |
| `invalid_client` (token) | client_id/secret 誤り | invox サポートから再受領 |
| 500 Internal Server Error | invox 側障害 | 指数バックオフで再試行 |

---

## セキュリティ上の重要事項

1. **client_secret / refresh_token は絶対にコード本文に書かない**。必ずスクリプトプロパティ。
2. **client_secret はメール添付で送られてくる**。受信後すぐに 1Password / Bitwarden 等のシークレットマネージャに転記して、メールは削除。
3. **refresh_token が漏洩したら即 invox サポートに無効化依頼**。新しい client_secret を再発行してもらう。
4. **API 経由でできる操作の権限**（取得のみ vs 登録・更新も可）は scope で絞る。

---

## 公式リソース

| トピック | URL |
|---------|-----|
| invox 受取請求書 API（公式案内） | https://invox.jp/receive_api |
| invox API ドキュメント | https://invox.jp/api/ |
| プラン・料金 | https://invox.jp/receive/price |
| サポート問い合わせ | https://invox.jp/contact/ |

> 詳細仕様（全エンドポイント・レスポンス形式・スコープ一覧）は **契約後にサポートから案内される正式 API ドキュメント** を参照してください。本資料は公開情報に基づくため、契約後の最新仕様で確認のうえ実装してください。

# invox API GAS 実装サンプル（完全版）

`oauth-setup.md` でスクリプトプロパティへ認証情報を保存した前提。

応用5 教材の `templates.md`（gas-clasp スキル付属）と組み合わせて、Kintone と invox の両方を `main()` から取得する構成を想定。

## 必要なスクリプトプロパティ

| キー | 値 |
|------|-----|
| `INVOX_CLIENT_ID` | クライアント ID |
| `INVOX_CLIENT_SECRET` | クライアントシークレット |
| `INVOX_REFRESH_TOKEN` | refresh_token |
| `INVOX_COMPANY_CODE` | **企業 ID（必須、≤30文字）** |

---

## ファイル構成例

```
billing-gas/src/
├── main.js
├── config.js
├── kintone.js
├── invox.js        ← この章のコード
├── sheet.js
├── notify.js
└── trigger.js
```

---

## `src/invox.js`

```javascript
/**
 * invox 受取請求書 API クライアント
 *
 * 公式仕様メモ:
 *   - 一覧 API: GET /api/public/invoice_receive/invoice/list
 *   - 必須クエリ: invox_company_code
 *   - レスポンス: { count, next, previous, results: [...] }
 *   - ページング: next が null になるまで（per_page パラメータは無い）
 */

const INVOX_TOKEN_URL    = 'https://api.invox.jp/oauth2/token/';
const INVOX_INVOICE_LIST = 'https://api.invox.jp/api/public/invoice_receive/invoice/list';

/**
 * refresh_token から短命の access_token を取得する。
 * access_token は 10 時間有効（36000 秒）。GAS 実行ごとに呼んでよい。
 *
 * 公式仕様: Basic ヘッダに client_id:client_secret、body にも client_id を渡す。
 */
function getInvoxAccessToken_() {
  const props = PropertiesService.getScriptProperties();
  const clientId     = props.getProperty('INVOX_CLIENT_ID');
  const clientSecret = props.getProperty('INVOX_CLIENT_SECRET');
  const refreshToken = props.getProperty('INVOX_REFRESH_TOKEN');

  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error('invox 認証情報が不足: INVOX_CLIENT_ID / INVOX_CLIENT_SECRET / INVOX_REFRESH_TOKEN を確認');
  }

  const basic = Utilities.base64Encode(`${clientId}:${clientSecret}`);
  const res = UrlFetchApp.fetch(INVOX_TOKEN_URL, {
    method: 'post',
    headers: { 'Authorization': `Basic ${basic}` },
    payload: {
      grant_type:    'refresh_token',
      refresh_token: refreshToken,
      client_id:     clientId          // body 側にも必須
    },
    muteHttpExceptions: true
  });

  if (res.getResponseCode() !== 200) {
    throw new Error(`invox トークン更新失敗 (${res.getResponseCode()}): ${res.getContentText()}`);
  }
  return JSON.parse(res.getContentText()).access_token;
}

/**
 * 受取請求書を取得する。next ベースでページングする。
 *
 * @param {Object} filters - 絞り込み条件（任意）
 *   - invoice_date_from / invoice_date_to: 請求日 (YYYY-MM-DD)
 *   - payment_plan_date_from / payment_plan_date_to: 支払予定日
 *   - posting_date_from / posting_date_to: 計上日
 *   - fixed_only: "true" / "false"
 *   - export_status: "exported" / "not_exported" など
 *   - department_code: 部門コード
 *   - include_sub_departments: "true" / "false"
 * @returns {Array} 請求書配列
 */
function fetchInvoxInvoices(filters) {
  const props = PropertiesService.getScriptProperties();
  const companyCode = props.getProperty('INVOX_COMPANY_CODE');
  if (!companyCode) {
    throw new Error('INVOX_COMPANY_CODE が未設定。設定 > 会社 で確認した企業 ID をスクリプトプロパティに登録してください');
  }

  const token = getInvoxAccessToken_();
  const invoices = [];

  const qs = buildQS_({
    invox_company_code: companyCode,   // 必須
    ...(filters || {}),
    page: 1
  });
  let nextUrl = `${INVOX_INVOICE_LIST}?${qs}`;

  let safety = 0;
  while (nextUrl) {
    if (++safety > 1000) {
      throw new Error('ページ数が異常に多い。filters を見直してください');
    }

    const res = UrlFetchApp.fetch(nextUrl, {
      method: 'get',
      headers: { 'Authorization': `Bearer ${token}` },
      muteHttpExceptions: true
    });

    if (res.getResponseCode() !== 200) {
      throw new Error(`invox API エラー (${res.getResponseCode()}): ${res.getContentText()}`);
    }

    const body = JSON.parse(res.getContentText());
    invoices.push(...(body.results || []));
    nextUrl = body.next || null;       // 終端判定: next が null
  }

  return invoices;
}

/**
 * GAS 用クエリ文字列ビルダ（URLSearchParams の代用）。
 */
function buildQS_(params) {
  return Object.entries(params)
    .filter(([_, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&');
}
```

---

## `src/main.js` に統合する例

Kintone と invox を並列に取得して、別々のシートタブに書き込む構成:

```javascript
function main() {
  try {
    const config = getConfig();

    // 1. Kintone から請求案件マスタを取得
    const kintoneRecords = fetchKintoneRecords(config);
    updateSheet(kintoneRecords, config.sheetId, '案件');

    // 2. invox から今月の受取請求書を取得（請求日ベース）
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const tz = 'Asia/Tokyo';
    const invoxInvoices = fetchInvoxInvoices({
      invoice_date_from: Utilities.formatDate(firstDay, tz, 'yyyy-MM-dd'),
      fixed_only:        'true'        // 確定済みのみ
    });
    updateInvoxSheet_(invoxInvoices, config.sheetId, '受領');

    // 3. （オプション）案件↔受領を突合
    reconcileSheets_(config.sheetId);

    notifySlack(`✅ 案件 ${kintoneRecords.length} 件 / 受領 ${invoxInvoices.length} 件 を更新`);
  } catch (e) {
    Logger.log(e.toString());
    notifySlack(`❌ 更新失敗: ${e.message}`);
    throw e;
  }
}
```

---

## `src/sheet.js` に追加: invox 専用の書き込み

レスポンスのフィールド名は契約後に公式 API ドキュメントで確認が必須（下記は推測ベースの雛形）:

```javascript
function updateInvoxSheet_(invoices, sheetId, tabName) {
  const ss = SpreadsheetApp.openById(sheetId);
  const sheet = ss.getSheetByName(tabName) || ss.insertSheet(tabName);

  sheet.clear();

  const headers = ['ID', '請求書番号', '仕入先', '請求額', '請求日', '支払予定日', '状態', '取込日時'];
  sheet.getRange(1, 1, 1, headers.length)
    .setValues([headers])
    .setFontWeight('bold')
    .setBackground('#f4cccc');

  const now = new Date();
  // ⚠️ フィールド名（invoice_id, invoice_number, supplier_name, total_amount,
  //    invoice_date, payment_plan_date, status）は契約後の正式 API ドキュメントで確認すること。
  //    下記は公開情報からの推測値。
  const rows = invoices.map(inv => [
    inv.invoice_id        || inv.id || '',
    inv.invoice_number    || '',
    inv.supplier_name     || '',
    Number(inv.total_amount || 0),
    inv.invoice_date      || '',
    inv.payment_plan_date || '',
    inv.status            || '',
    now
  ]);

  if (rows.length > 0) {
    sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  }
  sheet.getRange(2, 4, Math.max(rows.length, 1), 1).setNumberFormat('¥#,##0');
  sheet.autoResizeColumns(1, headers.length);

  SpreadsheetApp.flush();
}
```

> ⚠️ **本サンプルのフィールド名は公開情報からの推測**。契約後に提供される公式 API ドキュメントで正しい命名に置き換えること。一覧 API のレスポンス構造 `{ count, next, previous, results: [...] }` は確認済みだが、個々のフィールド名は未確認。

---

## 案件 ↔ 受領の突合（オプション）

Kintone「案件」と invox「受領」を案件番号で突合して、第 3 のシート「突合」を作る:

```javascript
function reconcileSheets_(sheetId) {
  const ss = SpreadsheetApp.openById(sheetId);
  const matterSheet = ss.getSheetByName('案件');
  const invoxSheet  = ss.getSheetByName('受領');
  const recSheet    = ss.getSheetByName('突合') || ss.insertSheet('突合');

  const matters = matterSheet.getRange(2, 1, matterSheet.getLastRow() - 1, 8).getValues();
  const invoxes = invoxSheet.getRange(2, 1, invoxSheet.getLastRow() - 1, 8).getValues();

  // 案件番号 -> 受領レコード のマップ
  const invoxByNo = new Map();
  for (const row of invoxes) {
    const no = row[1];   // B列 = 請求書番号
    invoxByNo.set(no, row);
  }

  recSheet.clear();
  const headers = ['案件番号', '取引先', '案件請求額', '受領請求額', '差分', '状態'];
  recSheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');

  const rows = matters.map(m => {
    const no = m[1];
    const v  = invoxByNo.get(no);
    return [
      no,
      m[2],
      m[3],
      v ? v[3] : '',
      v ? (m[3] - v[3]) : '受領なし',
      v ? '突合済' : '未突合'
    ];
  });

  if (rows.length > 0) {
    recSheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  }
  SpreadsheetApp.flush();
}
```

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `401 Unauthorized` | `getInvoxAccessToken_` で再取得（access_token は 10 時間で失効） |
| `403 Forbidden` | プラン要件 / スコープを確認、invox サポートへ |
| `400 Bad Request` で `invox_company_code is required` | 企業 ID（INVOX_COMPANY_CODE）のスクリプトプロパティ登録漏れ |
| `400 Bad Request` で `invalid query parameter` | パラメータ名の誤り（`registered_at_from` ではなく `invoice_date_from` 等） |
| `invalid_client` | Basic ヘッダの認証情報 or body の `client_id` が不一致 |
| ページングが終わらない | `next` フィールドが null になるまでループ。件数比較で終端判定しない |
| GAS 6 分タイムアウト | 月分割で時間トリガーを増やす（毎週月曜・水曜・金曜の朝など） |
| レスポンスフィールド名が違う | invox 正式 API ドキュメントを契約後に取得して調整 |

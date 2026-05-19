---
name: invox-api
description: invox 受取請求書（株式会社Deepwork）の REST API を OAuth 2.0 経由で叩き、受取請求書データを GAS や Node.js から取得・登録するスキル。プロフェッショナルプラン契約済みで client_id / client_secret を取得済みのユーザー向け。「invox」「インボックス」「受取請求書 API」「invox 連携」「invox OAuth」が出てきたら発火する。応用5 ハンズオン本編は Kintone のみで完結するので、未契約者には kintone-api スキルだけで足りる旨を案内すること。
---

# invox-api スキル

invox 受取請求書（株式会社 Deepwork）の REST API を扱うためのスキル。応用5 教材リポジトリの `references/invox-連携ガイド.md` をスキル化したもの。

## 利用条件と前提

**このスキルが役立つのは、以下を全て満たすケースだけ**:

| 条件 | 内容 |
|------|------|
| **プラン** | invox プロフェッショナルプラン契約済み（無料トライアル不可） |
| **クライアント認証情報** | invox サポート経由で `client_id` / `client_secret` 発行済み |
| **接続ユーザー** | invox 上に管理者スタッフが登録済み |

> ⚠️ **未契約のユーザーには使わない**
> 応用5 ハンズオン本編は Kintone のみで完結する。invox 未契約の受講者には「`kintone-api` スキルだけで OK」と案内し、本スキルは触らないこと。

---

## 認証方式: OAuth 2.0（Authorization Code + refresh_token）

invox は OAuth 2.0 の 3 つのエンドポイントを使う:

| エンドポイント | URL | 用途 |
|--------------|-----|------|
| 認可 | `https://api.invox.jp/oauth2/authorize/` | 認可コード取得（1分有効） |
| トークン | `https://api.invox.jp/oauth2/token/` | access_token / refresh_token 取得 |
| 無効化 | `https://api.invox.jp/oauth2/revoke_token/` | トークン取り消し |

- `access_token`: 10 時間有効
- `refresh_token`: 無期限（解約まで）

**Basic 認証**: `Authorization: Basic base64(client_id:client_secret)` をトークンエンドポイントへのヘッダに付ける。

詳細フロー（認可コード取得 → トークン交換）は `references/oauth-setup.md` を参照。

---

## ベース URL とレスポンス

| 項目 | 値 |
|------|----|
| **API ベース URL** | `https://api.invox.jp/api/public/` |
| **エンドポイント命名** | `/{サービス}/{リソース}/{操作}` （例: `invoice_receive/invoice/list`） |
| **API リクエストヘッダ** | `Authorization: Bearer {access_token}` |
| **レスポンス形式** | JSON（一覧系は `{ count, next, previous, results: [...] }`） |
| **HTTP 401** | access_token 期限切れ / 不正 |
| **HTTP 403** | プラン要件未充足 / スコープ不足 |
| **HTTP 500** | invox 側障害（指数バックオフでリトライ） |

### 必須クエリパラメータ

すべての受取請求書 API は **`invox_company_code`**（≤30文字、企業 ID）が **必須**。これが無いと 400 で動かない。設定 > 会社 で確認できる ID を渡す。

### レート制限・サイズ制約

| 項目 | 制限 |
|------|------|
| 1 リクエスト | 50 MB |
| 添付ファイルサイズ | 10 MB（別枠） |
| 仕訳エクスポート | 1 回 100 件 |
| ファイル一括 DL | 1 回 100 件 |

日次の請求書取得程度では絶対に当たらない。

---

## 初回セットアップ（1回だけ手動）

1. ブラウザで認可エンドポイントを開いて invox にログイン
2. 表示された **認可コード**（1 分以内に使う）を取得
3. ターミナルで `curl` を使ってトークンエンドポイントへ交換リクエスト
4. レスポンスの `refresh_token` を控える
5. GAS のスクリプトプロパティに保存:

| キー | 値 |
|------|-----|
| `INVOX_CLIENT_ID` | invox から発行された client_id |
| `INVOX_CLIENT_SECRET` | invox から発行された client_secret |
| `INVOX_REFRESH_TOKEN` | 上で取得した refresh_token |

> ⚠️ `access_token` は **保存しない**（10時間で失効するため、必要時に refresh_token から都度発行する）。

具体的な curl コマンド・ブラウザ URL は `references/oauth-setup.md` を参照。

---

## GAS 実装の核（最小コード）

完全なコードと main() への組み込み例は `references/gas-implementation.md` にある。ここではポイントだけ。

### アクセストークン取得関数

```javascript
function getInvoxAccessToken_() {
  const props = PropertiesService.getScriptProperties();
  const clientId     = props.getProperty('INVOX_CLIENT_ID');
  const clientSecret = props.getProperty('INVOX_CLIENT_SECRET');
  const refreshToken = props.getProperty('INVOX_REFRESH_TOKEN');

  if (!clientId || !clientSecret || !refreshToken) {
    throw new Error('invox 認証情報が不足');
  }

  // 公式仕様: Basic ヘッダに client_id:client_secret、body にも client_id を含める
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

### 受取請求書の取得（ページング込み）

`next` フィールドが null になるまでページング。`per_page` パラメータは無いので **件数比較で終端判定しない**。

```javascript
function fetchInvoxInvoices_(companyCode, filters) {
  const token = getInvoxAccessToken_();
  const baseUrl = 'https://api.invox.jp/api/public/invoice_receive/invoice/list';
  const invoices = [];

  // 1ページ目の URL を組み立て
  const qs = buildQS_({
    invox_company_code: companyCode,   // 必須
    ...(filters || {}),
    page: 1
  });
  let nextUrl = `${baseUrl}?${qs}`;

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
    nextUrl = body.next || null;   // 公式仕様: 終端は next === null
  }
  return invoices;
}

function buildQS_(params) {
  return Object.entries(params)
    .filter(([_, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&');
}
```

> ⚠️ GAS の V8 には `URLSearchParams` がない。`encodeURIComponent` ベースの QS ビルダを使う。

---

## 主要パラメータ

受取請求書一覧 `invoice_receive/invoice/list` の主要クエリパラメータ:

| パラメータ | 必須 | 例 | 説明 |
|----------|:---:|-----|------|
| `invox_company_code` | ✅ | `mycompany123` | 企業 ID（≤30 文字）。**必須** |
| `invoice_date_from` | | `2026-05-01` | 請求日 from |
| `invoice_date_to` | | `2026-05-31` | 請求日 to |
| `payment_plan_date_from` | | | 支払予定日 from |
| `payment_plan_date_to` | | | 支払予定日 to |
| `posting_date_from` | | | 計上日 from |
| `posting_date_to` | | | 計上日 to |
| `fixed_only` | | `true` | 確定済みのみ |
| `export_status` | | `not_exported` | エクスポート状態 |
| `payment_method` | | | 支払方法コード |
| `department_code` | | | 部門コード |
| `include_sub_departments` | | `true` | 子部門も含む |
| `page` | | `1` | ページ番号（1始まり） |

> ⚠️ **公式に `per_page` パラメータは存在しない**。1 ページあたり件数は invox 側固定。終端判定はレスポンスの `next` を見る。
>
> ⚠️ **`status=approved` 等は公開仕様に未確認**。確認できているステータス語彙は `wait_charge` のみ。確定済み絞込みは `fixed_only=true` が事実上の代替。

正式なパラメータ全集合は invox サポートから提供される公式 API ドキュメント（契約後に閲覧可能）を参照。

---

## Critical Rules（必ず守る）

invox API を扱うときに無意識で違反しがちな注意点:

1. **`client_secret` / `refresh_token` をコード本文に書かない**
   必ず PropertiesService。GitHub に push した瞬間に Bot がスキャンする。

2. **`client_secret` をメールで受け取ったら即シークレットマネージャへ**
   メール添付や本文に残したまま放置しない。1Password / Bitwarden 等に移して原本を削除。

3. **`access_token` を保存しない**
   10時間で失効する短命トークン。GAS 実行ごとに `refresh_token` から再発行する。

4. **`refresh_token` 漏洩時は即サポート連絡**
   `https://api.invox.jp/oauth2/revoke_token/` で無効化 + `client_secret` 再発行を依頼。

5. **スコープを最小限に**
   API 経由でできる操作の権限（取得のみ vs 登録・更新も可）は契約時に絞る。

6. **GAS の 6 分タイムアウト**
   月次レコード数千件規模ならまず問題ないが、ファイル一括 DL を含む処理は時間トリガーで分割。

7. **`encodeURIComponent` で QS をエンコード**
   GAS の V8 ランタイムには `URLSearchParams` が完全には実装されていない。手で QS を組み立てる。

---

## トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| `401 Unauthorized` | access_token 失効 | `getInvoxAccessToken_()` で再取得（10時間ごと） |
| `403 Forbidden` | プラン要件不足 / スコープ不足 | 契約状況を確認、scope 見直し |
| `invalid_grant` | refresh_token 失効 / 取り消し済み | 認可フローからやり直し |
| `invalid_client` | client_id/secret 誤り | invox サポートから再受領 |
| `500 Internal Server Error` | invox 側障害 | 指数バックオフで再試行 |
| 認可コードの期限切れ | 1分以内に使い切れず | もう一度ブラウザで認可エンドポイントを開く |

---

## Reference Index

| ファイル | 読むべきタイミング |
|---------|-----------------|
| `references/oauth-setup.md` | 初回 OAuth セットアップ（認可コード取得・curl でトークン交換） |
| `references/gas-implementation.md` | GAS から呼ぶ完全実装（Kintone と並列で main() に統合する例） |

---

## 公式リソース

| トピック | URL |
|---------|-----|
| invox 受取請求書 API（公式案内） | https://invox.jp/receive_api |
| invox API ドキュメント | https://invox.jp/api/ |
| プラン・料金 | https://invox.jp/receive/price |
| サポート問い合わせ | https://invox.jp/contact/ |

> 詳細仕様（全エンドポイント・レスポンス形式・スコープ一覧）は **契約後にサポートから案内される正式 API ドキュメント** を参照すること。本スキル本文・references は公開情報に基づく雛形であり、契約後の最新仕様で必ず確認のうえ実装する。

---

## このスキルの使い方（Claude 向け）

ユーザーから「invox の請求書取ってきて」「インボックス API 叩いて」と依頼されたら:

1. **契約状況を確認** — 「プロフェッショナルプランで invox サポートから client_id 発行を受けていますか?」と尋ねる
2. **未契約なら撤退** — 「無料トライアルでは API が使えないため、Kintone データソースで代替するか、本格運用したい場合は invox プロフェッショナルプランの契約が必要です」と案内し、`kintone-api` スキルへ誘導
3. **契約済みなら**:
   a. 初回なら `references/oauth-setup.md` で OAuth セットアップを案内
   b. 既にセットアップ済みなら `references/gas-implementation.md` の雛形で実装
4. **生成コードは Critical Rules 7 項目に照らしてセルフレビュー**

**禁止事項**:
- ユーザーの `client_secret` / `refresh_token` 実値を含むコードを生成しない
- `setProperties({ INVOX_CLIENT_SECRET: '実値' })` のような書き方を提案しない（手動入力誘導）
- 推測したスコープ名を確定情報のように扱わない（契約後の正式 API ドキュメントが正）
- 未契約者に「とりあえず動かしてみよう」と勧めない（無料トライアルでは絶対に動かない）

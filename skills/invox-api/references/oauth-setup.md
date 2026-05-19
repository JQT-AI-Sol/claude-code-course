# invox OAuth 2.0 初回セットアップ手順

`refresh_token` を 1 回だけ手動で取得するための手順。以後は GAS から `getInvoxAccessToken_()` 経由で `access_token` を自動更新する。

---

## 前提

- invox プロフェッショナルプラン契約済み
- invox サポートから `client_id` と `client_secret` をメール受領済み
- invox 上に管理者スタッフ（メールアドレス）が登録済み

---

## ステップ 1: 認可コードを取得

ブラウザで以下の URL を開く（`{CLIENT_ID}` と `{REDIRECT_URI}` は invox サポートに事前申請したものに置換）:

```
https://api.invox.jp/oauth2/authorize/
  ?client_id={CLIENT_ID}
  &response_type=code
  &redirect_uri={REDIRECT_URI}
  &scope=read+write
```

> ⚠️ **`redirect_uri` は事前申請制**
> invox では redirect_uri をクライアント登録時に申請する必要がある。`urn:ietf:wg:oauth:2.0:oob`（Out-of-Band 認証）が使えるかは公式ドキュメントに明記がなく、サポートに事前確認すること。テスト用の localhost URL（例: `http://localhost:8080/callback`）を申請しておくのが現実的。

> 💡 **scope は `read write`**
> 公式の例示は `scope=read write`（半角スペース or `+` 区切り）。`receive_invoice` 等のサービス名そのものは scope ではない。読み取りのみで運用するなら `scope=read` のみで OK。

invox にログイン → 「許可」をクリックすると、画面に **認可コード**（約 25 文字の英数字列）が表示される。

> ⚠️ **認可コードは 1 分以内に使い切ること**。失効したらもう一度ブラウザで認可エンドポイントを開き直す。

---

## ステップ 2: 認可コードをトークンに交換

ターミナルで以下を実行（`{CLIENT_ID}`、`{CLIENT_SECRET}`、`{AUTH_CODE}` を置換）:

```bash
CLIENT_ID="..."
CLIENT_SECRET="..."
AUTH_CODE="表示された認可コード"
REDIRECT_URI="申請したリダイレクトURL"   # 例: http://localhost:8080/callback

curl -X POST https://api.invox.jp/oauth2/token/ \
  -u "${CLIENT_ID}:${CLIENT_SECRET}" \
  -d "grant_type=authorization_code" \
  -d "code=${AUTH_CODE}" \
  -d "client_id=${CLIENT_ID}" \
  -d "redirect_uri=${REDIRECT_URI}"
```

> ⚠️ Basic ヘッダ（`-u`）と **body の `client_id` 両方** が必要。片方欠けると `invalid_client` で失敗する。

成功レスポンス例:

```json
{
  "access_token":  "eyJhbGciOi...",
  "token_type":    "Bearer",
  "expires_in":    36000,
  "refresh_token": "rt_xxxxxxxxxxxxxxxxxxxx",
  "scope":         "read write"
}
```

**保存すべきは `refresh_token` だけ**。`access_token` は 10 時間で失効するため、GAS が必要時に再発行する。

---

## ステップ 3: GAS のスクリプトプロパティへ保存

1. 対象 GAS プロジェクトをブラウザで開く（`clasp open-script`）
2. 左メニュー ⚙️「プロジェクトの設定」
3. 「スクリプト プロパティ」セクション > 「スクリプト プロパティを追加」
4. 以下の 3 つを順に登録:

| キー | 値 |
|------|-----|
| `INVOX_CLIENT_ID` | invox から発行された client_id |
| `INVOX_CLIENT_SECRET` | invox から発行された client_secret |
| `INVOX_REFRESH_TOKEN` | ステップ 2 で取得した refresh_token |
| `INVOX_COMPANY_CODE` | 企業 ID（設定 > 会社、≤30文字）。すべての API 呼び出しで必須 |

5. 「スクリプト プロパティを保存」をクリック

> ⚠️ **コードで `setProperties` を使って実値を渡さない**。Git に push したらこの行ごと漏洩する。必ず GAS の UI から手入力する。

---

## ステップ 4: 接続テスト

GAS エディタで以下のテスト関数を実行して、トークンが取れるか確認:

```javascript
function testInvoxConnection() {
  const token = getInvoxAccessToken_();
  Logger.log('access_token 取得: ' + token.substring(0, 20) + '...');

  const companyCode = PropertiesService.getScriptProperties()
    .getProperty('INVOX_COMPANY_CODE');   // ← 別途登録が必要
  if (!companyCode) throw new Error('INVOX_COMPANY_CODE を スクリプトプロパティに登録してください');

  const url = `https://api.invox.jp/api/public/invoice_receive/invoice/list`
    + `?invox_company_code=${encodeURIComponent(companyCode)}&page=1`;

  const res = UrlFetchApp.fetch(url, {
    method: 'get',
    headers: { 'Authorization': `Bearer ${token}` },
    muteHttpExceptions: true
  });
  Logger.log('応答コード: ' + res.getResponseCode());
  Logger.log('応答内容: ' + res.getContentText().substring(0, 500));
}
```

> ⚠️ スクリプトプロパティに `INVOX_COMPANY_CODE`（≤30文字、設定 > 会社で確認できる企業 ID）も登録すること。

GAS エディタで関数選択 → ▶ 実行 → 「実行数」ログで 200 と JSON が出れば成功。

---

## トラブルシューティング

| 状況 | 対処 |
|------|------|
| ブラウザで「不正なリクエスト」と出る | `client_id` のスペル確認、URL エンコーディングは不要（そのまま貼る） |
| `invalid_grant` | 認可コードを 1 分以内に使えなかった。やり直し |
| `invalid_client` | `client_id` / `client_secret` のスペル誤り |
| `unauthorized_client` | scope が契約プランの範囲外 | invox サポート確認 |
| HTTP 403 from `/api/public/...` | スコープ不足 / 契約プラン外の API |
| refresh_token がレスポンスに含まれない | scope に `offline_access` 相当が必要かどうか invox サポート確認 |

---

## refresh_token のローテーション

`refresh_token` は無期限だが、以下の場合は再取得が必要:

- ユーザーが invox サポートから revoke 依頼を出した
- `client_secret` を再発行してもらった
- 契約プランを変更した

その場合は、ステップ 1 からやり直し → スクリプトプロパティを上書き。

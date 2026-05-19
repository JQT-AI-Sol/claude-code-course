# Kintone REST API エンドポイント詳細

応用5 ハンズオンで使う範囲（レコード CRUD）の詳細を記載。フォーム情報・アプリ情報・スペースなど他のエンドポイントは公式ドキュメント参照。

## レコード 1 件取得

```
GET /k/v1/record.json?app={APP_ID}&id={RECORD_ID}
```

レスポンス:

```json
{
  "record": {
    "$id":      { "type": "__ID__",         "value": "1" },
    "案件番号":  { "type": "SINGLE_LINE_TEXT","value": "INV-2026-001" },
    "請求額":    { "type": "NUMBER",         "value": "150000" }
  }
}
```

各フィールドが `{ "type": "...", "value": ... }` の形でラップされる点に注意。

## レコード複数取得

```
GET /k/v1/records.json?app={APP_ID}&query={QUERY}&fields[0]={F1}&fields[1]={F2}&totalCount=true
```

レスポンス:

```json
{
  "records": [ /* 上記レコード形式の配列 */ ],
  "totalCount": "3500"
}
```

- `query` 省略時は全件（500件まで）
- `fields` 省略時は全フィールド返却（重い）
- `totalCount=true` で件数も返す（重複カウントなし）

## レコード 1 件登録

```
POST /k/v1/record.json
Content-Type: application/json
{
  "app": "123",
  "record": {
    "案件番号": { "value": "INV-2026-099" },
    "請求額":   { "value": "200000" }
  }
}
```

書き込み時は `type` は不要（`value` だけでよい）。

レスポンス:

```json
{ "id": "42", "revision": "1" }
```

## レコード複数登録（最大100件）

```
POST /k/v1/records.json
{
  "app": "123",
  "records": [
    { "案件番号": { "value": "INV-001" } },
    { "案件番号": { "value": "INV-002" } }
  ]
}
```

レスポンス:

```json
{
  "ids":       ["1","2"],
  "revisions": ["1","1"]
}
```

> ⚠️ 100件超は分割。101件目以降は別リクエストで送る。

## レコード複数更新

`id` または `updateKey` で対象を指定:

```
PUT /k/v1/records.json
{
  "app": "123",
  "records": [
    {
      "id": "42",
      "record": { "状態": { "value": "完了" } }
    },
    {
      "updateKey": { "field": "案件番号", "value": "INV-2026-099" },
      "record": { "請求額": { "value": "250000" } }
    }
  ]
}
```

楽観ロックを使うなら `"revision": "3"` を入れる（revision が一致しないと 409）。

## レコード複数削除

```
DELETE /k/v1/records.json
{
  "app": "123",
  "ids": [1, 2, 3]
}
```

最大100件。revision を指定する場合は `"revisions": [1, 1, 2]` を併記。

## カーソル系（cursor API）

`references/cursor-recipe.md` を参照。

---

## フィールド型と value の関係

書き込み時の `value` の書き方:

| Kintone 型 | value の型 | 例 |
|------------|------------|-----|
| 文字列1行 | string | `"INV-001"` |
| 文字列複数行 | string | `"複数行\nテキスト"` |
| 数値 | string（数字文字列） | `"150000"` |
| 日付 | string（YYYY-MM-DD） | `"2026-05-19"` |
| 日時 | string（ISO8601） | `"2026-05-19T09:00:00+09:00"` または `"2026-05-19T00:00:00Z"`（`+0900` も受理されることが多いが、コロン付きが公式推奨） |
| ドロップダウン | string | `"未払"` |
| チェックボックス | string[] | `["A","B"]` |
| ラジオボタン | string | `"はい"` |
| ユーザー選択 | object[] | `[{"code":"user@example.com"}]` |
| 添付ファイル | object[] | `[{"fileKey": "..."}]`（先に file API でアップロード） |
| テーブル | object[] | `[{"value": { フィールド... }}]` |

読み取り時は `{ "type": "...", "value": ... }` 形式で返ってくる。

---

## トランザクション保証

- **複数登録 / 更新 / 削除は「全件成功 or 全件キャンセル」** の保証あり。1件でも失敗すると、リクエスト内の他のレコードへの変更も適用されない（部分成功は発生しない）。
- 楽観ロックを使うなら `"revision": "3"` を付ける。一致しなければ 409。
- 複数更新（PUT）のレスポンスには更新後の revision 番号配列が返る。

## レート制限と HTTP ステータス

| ステータス | 意味 |
|-----------|------|
| 200 | 成功 |
| 400 | リクエスト不正（query 文法エラー、必須パラメータ欠如） |
| 401 | 認証失敗（API トークン誤り） |
| 403 | 権限不足 |
| 404 | アプリ / レコードが存在しない |
| 409 | revision 不一致（更新衝突） |
| 429 / 520 | レート制限（指数バックオフでリトライ） |
| 5xx | サーバーエラー（リトライ） |

### コース別 1日リクエスト上限

| プラン | 上限 |
|--------|------|
| スタンダード | 10,000 件 / 日 |
| ワイド | 100,000 件 / 日 |

同時接続は **1 ドメインにつき 100 接続まで**。並列実行する場合は注意。

リトライ実装例:

```javascript
function fetchWithRetry_(url, options, maxRetry) {
  let wait = 1000;
  for (let i = 0; i <= maxRetry; i++) {
    const res = UrlFetchApp.fetch(url, options);
    const code = res.getResponseCode();
    if (code < 500 && code !== 429) return res;
    if (i === maxRetry) throw new Error(`Retry exceeded: ${code} ${res.getContentText()}`);
    Utilities.sleep(wait);
    wait *= 2;
  }
}
```

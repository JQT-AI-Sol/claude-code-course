# cursor API による大量レコード取得

`records.json` は1回 500件・offset 10,000件までという制約がある。月次で 1万件を超えるアプリは最初から **cursor API** で取得する。

## cursor API の流れ

```
1. POST /k/v1/records/cursor.json  → cursor ID を取得
2. GET  /k/v1/records/cursor.json  → 500件ずつ繰り返し取得（自動でページング）
3. DELETE /k/v1/records/cursor.json → 使い終わったら明示削除（必須ではないが推奨）
```

cursor は 10 分で自動失効。同時に開ける cursor は **1 ドメインにつき 10 個まで**（ユーザー単位ではない）。

## GAS 実装サンプル

```javascript
/**
 * cursor API で全レコードを取得する。
 * 数万件規模に対応。GAS のタイムアウト（6分）に注意。
 */
function fetchAllWithCursor_() {
  const props = PropertiesService.getScriptProperties();
  const subdomain = props.getProperty('KINTONE_SUBDOMAIN');
  const appId = props.getProperty('KINTONE_APP_ID');
  const token = props.getProperty('KINTONE_TOKEN');

  const baseUrl = `https://${subdomain}.cybozu.com/k/v1/records/cursor.json`;
  const headers = {
    'X-Cybozu-API-Token': token,
    'Content-Type': 'application/json'
  };

  // 1. cursor 作成
  const createRes = UrlFetchApp.fetch(baseUrl, {
    method: 'post',
    headers,
    payload: JSON.stringify({
      app: appId,
      fields: ['$id', '案件番号', '取引先', '請求額', '請求日', '支払期日', '状態'],
      query: 'order by レコード番号 asc',
      size: 500
    }),
    muteHttpExceptions: true
  });

  if (createRes.getResponseCode() !== 200) {
    throw new Error(`cursor 作成失敗: ${createRes.getContentText()}`);
  }

  const cursorId = JSON.parse(createRes.getContentText()).id;
  const records = [];

  try {
    // 2. cursor から繰り返し取得
    while (true) {
      const getRes = UrlFetchApp.fetch(
        `${baseUrl}?id=${cursorId}`,
        { method: 'get', headers, muteHttpExceptions: true }
      );

      if (getRes.getResponseCode() !== 200) {
        throw new Error(`cursor 取得失敗: ${getRes.getContentText()}`);
      }

      const body = JSON.parse(getRes.getContentText());
      records.push(...body.records);

      if (body.next === false) break;  // 終端
    }
  } finally {
    // 3. cursor 削除（途中エラーでも実行）
    UrlFetchApp.fetch(baseUrl, {
      method: 'delete',
      headers,
      payload: JSON.stringify({ id: cursorId }),
      muteHttpExceptions: true
    });
  }

  return records;
}
```

## ポイント

- **`size`** は最大 500
- **`fields`** で必要なフィールドだけ指定するとレスポンスが軽くなる（必須ではない）
- 取得後は **必ず DELETE** で cursor を解放する（10分で勝手に消えるが、行儀よく）
- GAS は 6分のタイムアウトがある。**5万件以上扱うなら、PropertiesService に途中の cursor ID を保存して時間トリガーで分割実行** する設計が必要

## エラー時の挙動

cursor が失効した状態で GET すると:

```json
{ "code": "GAIA_RE03", "message": "指定したカーソルが見つかりません。" }
```

このときは cursor を作り直す。長時間処理では try/catch でリトライ可能にしておく。

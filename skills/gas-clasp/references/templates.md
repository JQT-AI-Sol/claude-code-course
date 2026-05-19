# GAS プロジェクト雛形テンプレート

応用5 ハンズオン用の最小プロジェクト構成。`clasp create-script` の直後にこれをコピーすれば、Claude Code に「中身を書いて」と指示するだけで動くようになる。

## ディレクトリ構成

```
billing-gas/
├── .clasp.json
├── .claspignore
├── src/
│   ├── appsscript.json
│   ├── main.js          # エントリポイント
│   ├── config.js        # スクリプトプロパティ取得
│   ├── kintone.js       # Kintone API ラッパ
│   ├── sheet.js         # スプレッドシート書き込み
│   ├── notify.js        # Slack 通知
│   └── trigger.js       # 時間トリガー設定
└── README.md
```

## `.clasp.json`

`clasp create-script` で自動生成される。中身はこんな感じ:

```json
{
  "scriptId": "1AbCdEfGhIjKlMnOpQrStUvWxYz",
  "rootDir": "./src"
}
```

## `.claspignore`

`clasp push` の対象から除外したいファイルを指定。

```
**/**
!src/**/*.js
!src/appsscript.json
```

これで `src/` 配下の `.js` と `appsscript.json` だけが Google に送られる。

## `src/appsscript.json`

```json
{
  "timeZone": "Asia/Tokyo",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8"
}
```

## `src/main.js`

```javascript
/**
 * 請求ダッシュボード自動更新スクリプト
 * 時間トリガー（毎朝6時）から main() が呼ばれる
 */
function main() {
  try {
    const config = getConfig();
    const records = fetchKintoneRecords(config);
    updateSheet(records, config.sheetId);
    notifySlack(`✅ 請求台帳を更新しました（${records.length} 件）`);
  } catch (e) {
    Logger.log(e.toString());
    notifySlack(`❌ 請求台帳の更新に失敗: ${e.message}`);
    throw e;
  }
}
```

## `src/config.js`

```javascript
function getConfig() {
  const props = PropertiesService.getScriptProperties();
  const required = ['KINTONE_SUBDOMAIN', 'KINTONE_APP_ID', 'KINTONE_TOKEN', 'TARGET_SHEET_ID'];
  const optional = ['SLACK_WEBHOOK', 'USE_MOCK', 'KINTONE_MOCK_FILE_ID'];

  const config = {};
  for (const key of required) {
    config[key] = props.getProperty(key);
    if (!config[key]) {
      throw new Error(`スクリプトプロパティ "${key}" が未設定です`);
    }
  }
  for (const key of optional) {
    config[key] = props.getProperty(key);
  }

  return {
    subdomain: config.KINTONE_SUBDOMAIN,
    appId:     config.KINTONE_APP_ID,
    token:     config.KINTONE_TOKEN,
    sheetId:   config.TARGET_SHEET_ID,
    slackWebhook: config.SLACK_WEBHOOK,
    useMock:   config.USE_MOCK === 'true',
    mockFileId: config.KINTONE_MOCK_FILE_ID
  };
}
```

## `src/kintone.js`

```javascript
function fetchKintoneRecords(config) {
  if (config.useMock) {
    return fetchMockRecords_(config.mockFileId);
  }

  const records = [];
  let offset = 0;
  const limit = 500;

  while (true) {
    const query = `order by レコード番号 asc limit ${limit} offset ${offset}`;
    const url = `https://${config.subdomain}.cybozu.com/k/v1/records.json`
      + `?app=${encodeURIComponent(config.appId)}`
      + `&query=${encodeURIComponent(query)}`;

    const res = UrlFetchApp.fetch(url, {
      method: 'get',
      headers: { 'X-Cybozu-API-Token': config.token },
      muteHttpExceptions: true
    });

    if (res.getResponseCode() !== 200) {
      throw new Error(`Kintone API error: ${res.getResponseCode()} ${res.getContentText()}`);
    }

    const body = JSON.parse(res.getContentText());
    records.push(...body.records);
    if (body.records.length < limit) break;
    offset += limit;
    if (offset >= 10000) {
      throw new Error('offset 10000 超え。cursor API への切替が必要');
    }
  }

  return records;
}

function fetchMockRecords_(fileId) {
  if (!fileId) throw new Error('USE_MOCK=true なのに KINTONE_MOCK_FILE_ID が未設定');
  const json = DriveApp.getFileById(fileId).getBlob().getDataAsString();
  return JSON.parse(json).records;
}
```

## `src/sheet.js`

```javascript
function updateSheet(records, sheetId) {
  const ss = SpreadsheetApp.openById(sheetId);
  const sheet = ss.getSheetByName('案件') || ss.insertSheet('案件');

  sheet.clear();

  const headers = ['ID', '案件番号', '取引先', '請求額', '請求日', '支払期日', '状態', '更新日時'];
  sheet.getRange(1, 1, 1, headers.length)
    .setValues([headers])
    .setFontWeight('bold')
    .setBackground('#9fc5e8');

  const now = new Date();
  const rows = records.map(r => [
    r['$id'].value,
    r['案件番号'] ? r['案件番号'].value : '',
    r['取引先']   ? r['取引先'].value   : '',
    r['請求額']   ? Number(r['請求額'].value) : 0,
    r['請求日']   ? r['請求日'].value   : '',
    r['支払期日'] ? r['支払期日'].value : '',
    r['状態']     ? r['状態'].value     : '',
    now
  ]);

  if (rows.length > 0) {
    sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  }

  // 列幅自動調整
  sheet.autoResizeColumns(1, headers.length);

  // 通貨フォーマット
  sheet.getRange(2, 4, Math.max(rows.length, 1), 1).setNumberFormat('¥#,##0');

  SpreadsheetApp.flush();
}
```

## `src/notify.js`

```javascript
function notifySlack(text) {
  const webhook = PropertiesService.getScriptProperties().getProperty('SLACK_WEBHOOK');
  if (!webhook) {
    Logger.log('SLACK_WEBHOOK 未設定。通知スキップ: ' + text);
    return;
  }
  UrlFetchApp.fetch(webhook, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({ text })
  });
}
```

## `src/trigger.js`

```javascript
function installDailyTrigger() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'main')
    .forEach(t => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger('main')
    .timeBased()
    .atHour(6)
    .everyDays(1)
    .create();

  Logger.log('毎日6時のトリガーを設定しました');
}

function uninstallAllTriggers() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  Logger.log('全トリガーを削除しました');
}
```

## 実装手順（受講者向け）

1. `mkdir billing-gas && cd billing-gas`
2. `clasp create-script --title "請求ダッシュボード自動更新" --type standalone --rootDir ./src`
3. 上記の各ファイルを Claude Code に書かせる（「kintone-api スキルと gas-clasp スキルを参考に書いて」）
4. `clasp push`
5. ブラウザで GAS エディタを開く（`clasp open-script`）
6. スクリプトプロパティに `KINTONE_*` / `TARGET_SHEET_ID` を設定
7. エディタで `main` を選んで実行 → 初回権限承認
8. 動作確認できたら `installDailyTrigger` を1回実行 → 翌朝から自動稼働

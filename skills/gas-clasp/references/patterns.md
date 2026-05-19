# GAS よく使うパターン集（応用5 向け抜粋）

このリポジトリで配布する `gas-clasp` スキルの補助リファレンス。応用5 ハンズオン本編で必要になる範囲を抜粋した。公式 `~/.claude/skills/google-apps-script/references/patterns.md` を持っている環境ではそちらの方が網羅的（サイドバー / モーダル / 高度書式など含む）。

## カスタムメニュー

スプレッドシートを開いたときに「請求台帳」メニューを追加して、手動更新ボタンを置く例。

```javascript
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('請求台帳')
    .addItem('今すぐ更新', 'main')
    .addItem('トリガーを設定', 'installDailyTrigger')
    .addSeparator()
    .addItem('トリガーを全削除', 'uninstallAllTriggers')
    .addItem('ログを見る', 'showLogs')
    .addToUi();
}
```

- `onOpen()` はシートを開く / リロードするたびに走る
- `addItem(label, functionName)` の関数名は **public** な関数（末尾 `_` 無し）に限る
- 絵文字も使える: `.addItem('🔄 今すぐ更新', 'main')`

## Toast（非ブロッキング通知）

処理完了を画面右下に小さく出したいとき:

```javascript
SpreadsheetApp.getActiveSpreadsheet().toast('更新完了', '請求台帳', 5);
// (message, title, durationSec)  duration: -1 で手動消去まで
```

## Alert / Confirm / Prompt

```javascript
const ui = SpreadsheetApp.getUi();

// 単純な通知
ui.alert('処理が完了しました');

// Yes/No 確認
const ans = ui.alert('本当に全削除しますか?', '元に戻せません', ui.ButtonSet.YES_NO);
if (ans === ui.Button.YES) { /* ... */ }

// 入力
const res = ui.prompt('対象日（YYYY-MM-DD）を入力', ui.ButtonSet.OK_CANCEL);
if (res.getSelectedButton() === ui.Button.OK) {
  const date = res.getResponseText();
}
```

> ⚠️ `ui.alert` 系は **Installable Trigger からは使えない**（バックグラウンド実行のため）。`main()` を時間トリガーから呼ぶ場合は alert ではなく Logger / Slack 通知へ。

## Installable Trigger（時間ベース）

応用5 で使う「毎朝 6 時に main を起動」のセットアップ:

```javascript
function installDailyTrigger() {
  // 重複防止: 既存の main トリガーを消す
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'main')
    .forEach(t => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger('main')
    .timeBased()
    .atHour(6)
    .everyDays(1)
    .create();
}
```

その他のスケジュール例:

```javascript
// 毎週月曜の 9 時
ScriptApp.newTrigger('weeklyReport').timeBased()
  .onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(9).create();

// 1 時間ごと
ScriptApp.newTrigger('hourly').timeBased().everyHours(1).create();

// 毎月 1 日 8 時
ScriptApp.newTrigger('monthly').timeBased().onMonthDay(1).atHour(8).create();
```

> ⚠️ **`everyMinutes(n)` は 1 / 5 / 10 / 15 / 30 のみ許容**。`everyMinutes(7)` のような任意値は実行時エラーになる。`everyHours(n)` は 1〜23 で任意。

## Installable Trigger（編集ベース・フォーム送信）

```javascript
// 編集時（フル権限：UrlFetchApp や MailApp 可）
ScriptApp.newTrigger('onEditFull')
  .forSpreadsheet(SpreadsheetApp.getActive())
  .onEdit().create();

// フォーム送信時
ScriptApp.newTrigger('onFormSubmit')
  .forSpreadsheet(SpreadsheetApp.getActive())
  .onFormSubmit().create();
```

## UrlFetchApp テンプレ

応用5 では Kintone と Slack に対して使う。

主要オプション:
- `muteHttpExceptions: true` — 4xx/5xx でも例外を投げない（自分でハンドリング）
- `validateHttpsCertificates: false` — 開発時のみ。本番では使わない
- `followRedirects: false` — リダイレクトを自分で扱いたい場合
- `timeoutSeconds` — UrlFetchApp の **デフォルトタイムアウトは 60 秒**。Kintone カーソルの大量取得など、応答が遅い API では明示する

```javascript
function apiGet_(url, headers) {
  const res = UrlFetchApp.fetch(url, {
    method: 'get',
    headers: headers || {},
    muteHttpExceptions: true   // 4xx/5xx でも例外を投げない
  });
  const code = res.getResponseCode();
  if (code < 200 || code >= 300) {
    throw new Error(`GET ${url} failed (${code}): ${res.getContentText()}`);
  }
  return JSON.parse(res.getContentText());
}

function apiPost_(url, headers, payload) {
  const res = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: headers || {},
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });
  const code = res.getResponseCode();
  if (code < 200 || code >= 300) {
    throw new Error(`POST ${url} failed (${code}): ${res.getContentText()}`);
  }
  return JSON.parse(res.getContentText());
}
```

リトライ（指数バックオフ）付き版:

```javascript
function fetchWithRetry_(url, options, maxRetry) {
  let wait = 1000;
  for (let i = 0; i <= (maxRetry || 3); i++) {
    const res = UrlFetchApp.fetch(url, options);
    const code = res.getResponseCode();
    if (code < 500 && code !== 429) return res;
    if (i === maxRetry) throw new Error(`Retry exceeded: ${code}`);
    Utilities.sleep(wait);
    wait *= 2;
  }
}
```

## Slack Webhook

```javascript
function notifySlack_(text) {
  const webhook = PropertiesService.getScriptProperties().getProperty('SLACK_WEBHOOK');
  if (!webhook) return;
  UrlFetchApp.fetch(webhook, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({ text })
  });
}

// リッチメッセージ
notifySlack_({
  blocks: [
    { type: 'section', text: { type: 'mrkdwn', text: '*✅ 請求台帳更新完了*' } },
    { type: 'context', elements: [{ type: 'mrkdwn', text: `件数: ${count}` }] }
  ]
});
```

## メール送信

```javascript
function emailReport_() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getRange('A2:G20').getDisplayValues();

  let body = '<h2>本日の請求台帳</h2><table border="1" cellpadding="6">';
  body += '<tr><th>案件番号</th><th>取引先</th><th>請求額</th><th>支払期日</th><th>状態</th></tr>';
  for (const r of data) {
    if (!r[0]) continue;
    body += `<tr><td>${r[1]}</td><td>${r[2]}</td><td style="text-align:right">${r[3]}</td><td>${r[5]}</td><td>${r[6]}</td></tr>`;
  }
  body += '</table>';

  MailApp.sendEmail({
    to: 'team@example.com',
    subject: `請求台帳 ${Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd')}`,
    htmlBody: body
  });
}

// 残メール送信可能数を確認
Logger.log('残: ' + MailApp.getRemainingDailyQuota());
```

## PDF エクスポート

スプレッドシートを PDF として出力してメール添付する例。

```javascript
function exportSheetAsPdf_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('案件');

  const url = ss.getUrl().replace(/\/edit.*$/, '')
    + '/export?exportFormat=pdf&format=pdf'
    + '&size=A4&portrait=true&fitw=true'
    + '&sheetnames=false&printtitle=false&gridlines=false'
    + '&gid=' + sheet.getSheetId();

  const token = ScriptApp.getOAuthToken();
  const res = UrlFetchApp.fetch(url, { headers: { Authorization: 'Bearer ' + token } });

  MailApp.sendEmail({
    to: 'boss@example.com',
    subject: '月次請求レポート',
    body: '添付の PDF をご確認ください。',
    attachments: [res.getBlob().setName('billing-report.pdf')]
  });
}
```

## Properties Service

スクリプトプロパティ / ユーザープロパティ / ドキュメントプロパティの 3 階層。

```javascript
// スクリプト全体で共有（API キー等）
const sp = PropertiesService.getScriptProperties();
sp.setProperty('KEY', 'value');
sp.getProperty('KEY');
sp.deleteProperty('KEY');
sp.getProperties();                    // 全件取得
sp.setProperties({ A: '1', B: '2' });  // 一括設定

// ユーザー固有
const up = PropertiesService.getUserProperties();

// ドキュメント単位
const dp = PropertiesService.getDocumentProperties();
```

> ⚠️ 1 プロパティ 9KB、合計 500KB の制限あり。大きな state は Drive ファイルへ。

## 書式・色

```javascript
// 背景・文字色
sheet.getRange('A1:G1').setBackground('#9fc5e8').setFontColor('#ffffff');

// 太字・文字サイズ
sheet.getRange('A1:G1').setFontWeight('bold').setFontSize(12);

// 罫線
sheet.getRange('A1:G100').setBorder(true, true, true, true, true, true);

// 通貨フォーマット
sheet.getRange('D2:D100').setNumberFormat('¥#,##0');

// 日付フォーマット
sheet.getRange('E2:E100').setNumberFormat('yyyy-mm-dd');

// 中央寄せ
sheet.getRange('A1:G1').setHorizontalAlignment('center');

// 条件付き書式（支払期日超過 = 赤）
const rule = SpreadsheetApp.newConditionalFormatRule()
  .whenFormulaSatisfied('=AND($F2<TODAY(), $G2="未払")')
  .setBackground('#ff9999')
  .setRanges([sheet.getRange('A2:G100')])
  .build();
sheet.setConditionalFormatRules([rule]);
```

## 複数シートを扱う

```javascript
const ss = SpreadsheetApp.openById(sheetId);
const target = ss.getSheetByName('案件') || ss.insertSheet('案件');

// 全シート名一覧
const names = ss.getSheets().map(s => s.getName());

// シートの並べ替え
const s = ss.getSheetByName('案件');
ss.setActiveSheet(s);
ss.moveActiveSheet(1);   // 一番左に
```

# モックモード用サンプル JSON

API トークンを当日用意できない受講者向け。本物の Kintone API レスポンスと同じ形のサンプル JSON を返すことで、Step 2 以降を全く同じコードで進められる。

## 使い方

1. 下記 JSON を Google Drive に `kintone-mock.json` で保存
2. 共有設定を「リンクを知っている全員 / 閲覧可」に変更
3. ファイル ID を控える（URL の `/d/{ID}/` の部分）
4. スクリプトプロパティ `KINTONE_MOCK_FILE_ID` にファイル ID を保存
5. GAS コード冒頭で `const USE_MOCK = true;` にする

```javascript
const USE_MOCK = true;

function fetchKintoneRecords_() {
  if (USE_MOCK) {
    const fileId = PropertiesService.getScriptProperties().getProperty('KINTONE_MOCK_FILE_ID');
    const json = DriveApp.getFileById(fileId).getBlob().getDataAsString();
    return JSON.parse(json).records;
  }
  // 本物の処理（このスキルの SKILL.md 参照）
}
```

## サンプル JSON（コピーして Drive に保存）

```json
{
  "records": [
    {
      "$id":      { "type": "__ID__", "value": "1" },
      "案件番号":  { "type": "SINGLE_LINE_TEXT", "value": "INV-2026-001" },
      "取引先":    { "type": "SINGLE_LINE_TEXT", "value": "株式会社サンプル商事" },
      "請求額":    { "type": "NUMBER", "value": "150000" },
      "請求日":    { "type": "DATE", "value": "2026-05-01" },
      "支払期日":  { "type": "DATE", "value": "2026-05-31" },
      "状態":      { "type": "DROP_DOWN", "value": "未払" }
    },
    {
      "$id":      { "type": "__ID__", "value": "2" },
      "案件番号":  { "type": "SINGLE_LINE_TEXT", "value": "INV-2026-002" },
      "取引先":    { "type": "SINGLE_LINE_TEXT", "value": "山田商店株式会社" },
      "請求額":    { "type": "NUMBER", "value": "280000" },
      "請求日":    { "type": "DATE", "value": "2026-05-03" },
      "支払期日":  { "type": "DATE", "value": "2026-06-30" },
      "状態":      { "type": "DROP_DOWN", "value": "未払" }
    },
    {
      "$id":      { "type": "__ID__", "value": "3" },
      "案件番号":  { "type": "SINGLE_LINE_TEXT", "value": "INV-2026-003" },
      "取引先":    { "type": "SINGLE_LINE_TEXT", "value": "ABC コンサルティング合同会社" },
      "請求額":    { "type": "NUMBER", "value": "450000" },
      "請求日":    { "type": "DATE", "value": "2026-04-15" },
      "支払期日":  { "type": "DATE", "value": "2026-05-15" },
      "状態":      { "type": "DROP_DOWN", "value": "完了" }
    },
    {
      "$id":      { "type": "__ID__", "value": "4" },
      "案件番号":  { "type": "SINGLE_LINE_TEXT", "value": "INV-2026-004" },
      "取引先":    { "type": "SINGLE_LINE_TEXT", "value": "テクノロジー株式会社" },
      "請求額":    { "type": "NUMBER", "value": "1200000" },
      "請求日":    { "type": "DATE", "value": "2026-05-10" },
      "支払期日":  { "type": "DATE", "value": "2026-06-10" },
      "状態":      { "type": "DROP_DOWN", "value": "未払" }
    },
    {
      "$id":      { "type": "__ID__", "value": "5" },
      "案件番号":  { "type": "SINGLE_LINE_TEXT", "value": "INV-2026-005" },
      "取引先":    { "type": "SINGLE_LINE_TEXT", "value": "デザインスタジオ合同会社" },
      "請求額":    { "type": "NUMBER", "value": "85000" },
      "請求日":    { "type": "DATE", "value": "2026-03-20" },
      "支払期日":  { "type": "DATE", "value": "2026-04-20" },
      "状態":      { "type": "DROP_DOWN", "value": "未払" }
    },
    {
      "$id":      { "type": "__ID__", "value": "6" },
      "案件番号":  { "type": "SINGLE_LINE_TEXT", "value": "INV-2026-006" },
      "取引先":    { "type": "SINGLE_LINE_TEXT", "value": "山田商店株式会社" },
      "請求額":    { "type": "NUMBER", "value": "320000" },
      "請求日":    { "type": "DATE", "value": "2026-05-15" },
      "支払期日":  { "type": "DATE", "value": "2026-06-15" },
      "状態":      { "type": "DROP_DOWN", "value": "保留" }
    },
    {
      "$id":      { "type": "__ID__", "value": "7" },
      "案件番号":  { "type": "SINGLE_LINE_TEXT", "value": "INV-2026-007" },
      "取引先":    { "type": "SINGLE_LINE_TEXT", "value": "株式会社サンプル商事" },
      "請求額":    { "type": "NUMBER", "value": "175000" },
      "請求日":    { "type": "DATE", "value": "2026-05-18" },
      "支払期日":  { "type": "DATE", "value": "2026-06-18" },
      "状態":      { "type": "DROP_DOWN", "value": "未払" }
    },
    {
      "$id":      { "type": "__ID__", "value": "8" },
      "案件番号":  { "type": "SINGLE_LINE_TEXT", "value": "INV-2026-008" },
      "取引先":    { "type": "SINGLE_LINE_TEXT", "value": "ABC コンサルティング合同会社" },
      "請求額":    { "type": "NUMBER", "value": "560000" },
      "請求日":    { "type": "DATE", "value": "2026-05-01" },
      "支払期日":  { "type": "DATE", "value": "2026-05-31" },
      "状態":      { "type": "DROP_DOWN", "value": "完了" }
    }
  ],
  "totalCount": "8"
}
```

## ダミーアプリのフィールド構成（自分で Kintone に作る場合）

このサンプル JSON と同じ形のデータを Kintone 側に用意したい場合、以下のフィールドで「請求案件」アプリを作る:

| フィールドコード | 型 | 設定 |
|---|---|---|
| `案件番号` | 文字列(1行) | 重複禁止 ON |
| `取引先` | 文字列(1行) | |
| `請求額` | 数値 | 単位 = 円 |
| `請求日` | 日付 | 初期値 = 今日 |
| `支払期日` | 日付 | |
| `状態` | ドロップダウン | 選択肢: 未払, 保留, 完了 |

API トークン発行時の権限は **「レコード閲覧」のみ ON** で十分（書き込みは不要）。

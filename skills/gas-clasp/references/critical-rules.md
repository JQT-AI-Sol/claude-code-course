# Critical Rules（GAS で必ず守るべきこと）

Claude がコード生成時に **無意識で違反しやすい** 重要ルール集。SKILL.md の本文ではサマリーのみ提示し、詳細・コード例・違反時のエラーは本ファイルを参照する。

応用5 のハンズオン中は触れない高度トピックも含むが、生成コードのレビュー観点として常に意識する。

---

## 1. Public / Private 関数の使い分け

末尾に `_`（アンダースコア）が付く関数は **private** 扱いで、以下から呼べない:

- メニュー項目の `addItem('表示名', '関数名')` から
- インストール済みトリガーから
- HTML サイドバーの `google.script.run` から

```javascript
// ❌ トリガー設定で 'main_' を指定するとサイレント失敗
function main_() { ... }

// ✅ トリガー / メニュー / google.script.run から呼ぶ関数は末尾 _ 禁止
function main() { ... }
```

応用5 では `main` / `installDailyTrigger` / `listTriggers` 等の **エントリポイント関数は必ず public**（末尾 _ なし）にする。内部ヘルパーは `fetchKintoneRecords_` のように `_` を付ける。

---

## 2. バッチ操作（Sheets パフォーマンスの肝）

セル単位の読み書きは **70 倍遅い**。必ず範囲一括で扱う。

```javascript
// ❌ 100 行で 70 秒
for (let i = 1; i <= 100; i++) {
  const v = sheet.getRange(i, 1).getValue();
}

// ✅ 100 行で 1 秒
const all = sheet.getRange(1, 1, 100, 1).getValues();
```

書き込みも同じ。`setValues(rows)` で 2 次元配列を一発で渡す。

---

## 3. V8 ランタイム前提（モダン JS は OK だが Web API は無い）

GAS は V8 のみ。`const` / `let` / アロー関数 / `class` / `async` 等は使える。ただし以下は **使えない**:

| ブラウザ / Node の API | GAS での代替 |
|---|---|
| `setTimeout` / `setInterval` | `Utilities.sleep(ms)`（同期ブロッキング） |
| `fetch` | `UrlFetchApp.fetch(url, opts)` |
| `FormData` | payload オブジェクトを手で組む |
| `URL` クラス | 文字列処理で代用 |
| `crypto` | `Utilities.computeDigest()` / `Utilities.getUuid()` |

> 💡 `console.log` は V8 で利用可能（Stackdriver Logging に記録）。`Logger.log` と同等に使える。

---

## 4. トップレベルは `function` 宣言で書く（GAS グローバルスコープ）

GAS は **`function foo() {}` という宣言だけ** をエントリ候補として認識する。`const foo = () => {}` 形式はメニュー / トリガー / `google.script.run` から呼べない。

```javascript
// ❌ GAS から見えない
const main = () => { ... };

// ✅ GAS が認識する
function main() { ... }
```

内部ヘルパーや lib 関数はアロー関数でも問題ないが、**外から呼ばれる関数（main / installDailyTrigger / onOpen 等）は必ず宣言形式**。

---

## 5. シート変更後は `SpreadsheetApp.flush()`

Sheets への書き込みは内部でバッファリングされる。**関数の終端や、HTML ダイアログから呼ばれた処理の return 前** には flush しないと、画面に反映が遅れる / トランザクション境界が曖昧になる。

```javascript
function updateSheet(records, sheetId) {
  // ... setValues(...) など
  SpreadsheetApp.flush();  // ← 必須
}
```

---

## 6. Simple vs Installable トリガーの違い

応用5 では `installDailyTrigger`（Installable）を使う。Simple トリガーは権限が弱く、外部 API も叩けない。

| 機能 | Simple (`onEdit`/`onOpen`) | Installable |
|------|---------------------------|-------------|
| 認可フロー | 不要 | 必要（初回手動実行で承認） |
| メール送信 | ❌ | ✅ |
| 他ファイルアクセス | ❌ | ✅ |
| `UrlFetchApp` | ❌ | ✅ |
| ダイアログ表示 | ❌ | ✅ |
| 実行ユーザー | 編集者 | トリガー作成者 |

> 💡 Kintone API を叩く以上、必ず Installable Trigger（`ScriptApp.newTrigger(...)`）を使う。`onEdit` 関数名で書いて時間ベース起動を期待しても動かない。

---

## 7. シークレットをコード本文に書かない

トークン・API キー・refresh_token は **必ず PropertiesService** へ。GitHub に push した瞬間に Bot がスキャンして数分以内に漏洩する。

```javascript
// ❌ 絶対やらない
const TOKEN = 'xoxb-12345-...';

// ✅ スクリプトプロパティから読む
const token = PropertiesService.getScriptProperties().getProperty('KINTONE_TOKEN');
```

---

## Error Prevention 早見表

Critical Rules を破ったときに出る代表エラーと対処を一覧化:

| ミス | 対処 |
|------|------|
| ダイアログ / トリガーから関数が呼べない | 関数名末尾の `_` を外す |
| 大量データで遅い | `getValues()` / `setValues()` でバッチ化 |
| ダイアログ後の変更が画面に出ない | `SpreadsheetApp.flush()` を return 前に呼ぶ |
| `onEdit` でメール送信できない | Installable Trigger に書き換える |
| カスタム関数がタイムアウト | 30秒制限。重い処理は通常関数に移して `MailApp` で結果通知 |
| `setTimeout is not defined` | `Utilities.sleep(ms)` に置き換える |
| 6 分タイムアウト | 処理を分割し、cursor / state を Properties に保存して時間トリガーで再開 |
| 承認ダイアログが出ない | 「詳細 > プロジェクト名（安全ではないページ）に移動 > 許可」を案内 |
| バンドラが関数をツリーシェイク | `moduleSideEffects: 'no-treeshake'` または副作用 import |
| `export` が出力に残って GAS が壊れる | Rollup プラグインで strip |
| `const fn = () => {}` がメニュー / トリガーから呼べない | `function fn() {}` 宣言形式に書き換える |
| `clasp push` に不要ファイルが含まれる | `.clasp.json` の `rootDir` を `./dist` 等に設定 + `.claspignore` で除外 |

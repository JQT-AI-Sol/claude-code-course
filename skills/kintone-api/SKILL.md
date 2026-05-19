---
name: kintone-api
description: Kintone REST API を Google Apps Script（UrlFetchApp）や Node.js から叩いてレコードの一覧取得・登録・更新・削除を行うときに使うスキル。API トークン認証、query 文法、cursor API による大量データ取得、ページング、エラーハンドリング、スクリプトプロパティでのトークン管理を網羅。「Kintone」「kintone」「サイボウズ」「Kintone API」「kintone レコード取得」が出てきたら発火する。
---

# Kintone REST API スキル

Claude Code から GAS や Node.js で Kintone REST API を扱うための実践知識を提供する。応用5 ハンズオン「請求データ自動収集ダッシュボード」で受講者が使う前提で設計してある。

## このスキルが扱う範囲

- レコードの取得・登録・更新・削除（1件 / 複数件 / cursor）
- API トークン認証（最も簡単・最も推奨）
- query 文法（絞り込み・並び替え・ページング）
- Kintone 特有の落とし穴（500件制限、offset 10000件制限、テーブルフィールド扱い）
- GAS から `UrlFetchApp` で叩くときの完全な実装パターン
- スクリプトプロパティ / 環境変数でのトークン管理

範囲外（このスキルでは扱わない）:
- パスワード認証 / OAuth フロー（API トークンで十分）
- カスタマイズ JavaScript / プラグイン開発
- ファイル添付フィールドのバイナリ取得（必要なら別途調べる）

---

## ベース知識

### 認証: API トークンを使う

**最も簡単で安全な方式**。アプリ単位で発行し、権限を「レコード閲覧のみ」「閲覧 + 編集」のように絞れる。漏れても影響範囲が当該アプリに限定される。

```
リクエストヘッダ: X-Cybozu-API-Token: {API_TOKEN}
```

複数トークンが必要なときはカンマ区切り（複数アプリを横断するクエリ等）。**1リクエストで指定できるのは最大 9 個まで** — 10個以上を指定するとエラーになる:

```
X-Cybozu-API-Token: token_app_a,token_app_b,token_app_c   # 最大 9 個まで
```

> ⚠️ **ゲストスペースでは API トークン認証は使えない**
> ゲストスペース配下のアプリで API を叩くにはセッション認証（パスワード認証 / Basic 認証）が必要。本スキルの想定はゲストスペース外のアプリ。ゲストスペース対応が必要な場合は応用5 のスコープ外で別途設計する。

### ベース URL

```
https://{サブドメイン}.cybozu.com/k/v1/{エンドポイント}
```

ゲストスペースの場合（**API トークン認証は使えない点に注意**、上記参照）:

```
https://{サブドメイン}.cybozu.com/k/guest/{GUEST_SPACE_ID}/v1/{エンドポイント}
```

### Content-Type

書き込み系は必ず `application/json`:

```
Content-Type: application/json
```

---

## エンドポイント早見表

| 操作 | メソッド | URL |
|------|---------|-----|
| 1件取得 | GET | `/k/v1/record.json` |
| 1件登録 | POST | `/k/v1/record.json` |
| 1件更新 | PUT | `/k/v1/record.json` |
| 複数取得 | GET | `/k/v1/records.json` |
| 複数登録 | POST | `/k/v1/records.json` |
| 複数更新 | PUT | `/k/v1/records.json` |
| 複数削除 | DELETE | `/k/v1/records.json` |
| カーソル作成 | POST | `/k/v1/records/cursor.json` |
| カーソル取得 | GET | `/k/v1/records/cursor.json` |
| カーソル削除 | DELETE | `/k/v1/records/cursor.json` |

詳しいパラメータは `references/endpoints.md` を参照。

---

## 重要な制約（必ず守る）

| 制約 | 内容 | 対処 |
|------|------|------|
| **1回の取得上限** | `records.json` は1回 500件まで | ループまたは cursor API を使う |
| **offset 上限** | `offset` は最大 10,000 | 10,000 超えるなら cursor API を使う |
| **fields 上限** | リクエストボディ指定で1,000件 / クエリで添字 0〜99（=最大100件） | テーブル内フィールドは指定不可 |
| **like 検索の打切** | 100,000件到達で停止 | 検索条件を絞る |
| **同時接続** | **1ドメインにつき 100 接続まで** | 並列リクエスト数を制御 |
| **1日リクエスト数** | コース別: スタンダード **10,000件/日** / ワイド **100,000件/日** | 超過時は 520 系または `CB_NO04` |
| **タイムアウト** | GAS の `UrlFetchApp` は 6 分（GAS 実行自体も 6 分） | 重い処理は分割 |

> ⚠️ **500件 / 10,000件問題**
> 月次でレコード数が万件を超える可能性があるなら、**最初から cursor API で書く**。後から書き直すコストが大きい。詳細レシピは `references/cursor-recipe.md` を参照。

---

## GAS から呼び出すミニマム実装

このスニペットは応用5 で受講者が実際に使う形。コピーすればそのまま動く（トークンとサブドメインは置き換え必要）。

```javascript
/**
 * Kintone から請求案件レコードを全件取得する。
 * トークンはスクリプトプロパティ KINTONE_TOKEN に保存しておくこと。
 */
function fetchKintoneRecords_() {
  const props = PropertiesService.getScriptProperties();
  const subdomain = props.getProperty('KINTONE_SUBDOMAIN'); // 例: "your-tenant"
  const appId = props.getProperty('KINTONE_APP_ID');         // 例: "123"
  const token = props.getProperty('KINTONE_TOKEN');

  if (!subdomain || !appId || !token) {
    throw new Error('Kintone の設定が不足: KINTONE_SUBDOMAIN / KINTONE_APP_ID / KINTONE_TOKEN');
  }

  const records = [];
  let offset = 0;
  const limit = 500;

  // 500件ずつページング（小〜中規模アプリ向け。1万件超なら cursor API へ切替）
  while (true) {
    const url = `https://${subdomain}.cybozu.com/k/v1/records.json`
      + `?app=${encodeURIComponent(appId)}`
      + `&query=${encodeURIComponent(`order by レコード番号 asc limit ${limit} offset ${offset}`)}`;

    const res = UrlFetchApp.fetch(url, {
      method: 'get',
      headers: { 'X-Cybozu-API-Token': token },
      muteHttpExceptions: true
    });

    const code = res.getResponseCode();
    if (code !== 200) {
      throw new Error(`Kintone API エラー (${code}): ${res.getContentText()}`);
    }

    const body = JSON.parse(res.getContentText());
    records.push(...body.records);

    if (body.records.length < limit) break;  // 終端
    offset += limit;
    if (offset >= 10000) {
      throw new Error('offset が 10000 に到達。cursor API へ切替が必要です。');
    }
  }

  return records;
}
```

### スクリプトプロパティへの保存方法

GAS エディタ > 左メニュー「プロジェクトの設定」⚙ > 「スクリプト プロパティ」 > 「スクリプト プロパティを追加」で以下を登録:

| プロパティ名 | 値 |
|---|---|
| `KINTONE_SUBDOMAIN` | `your-tenant`（`.cybozu.com` の前部分） |
| `KINTONE_APP_ID` | アプリ URL の `k/{数値}/` の数値 |
| `KINTONE_TOKEN` | 発行した API トークン |

**注意**: コード本文に直書きしない。GitHub に push したら即漏洩する。

---

## query 文法 早見

```
field = "値"              -- 完全一致（数値・文字列）
field != "値"             -- 不一致
field in ("A", "B")       -- IN
field not in ("A", "B")   -- NOT IN
field like "*社"           -- 部分一致（テキスト・前後ワイルドカード可）
field > 100               -- 比較演算子（数値・日付）

-- 日付関数
作成日時 > FROM_TODAY(-7, DAYS)   -- 7日前以降
更新日時 = TODAY()                -- 今日
請求日 = LAST_MONTH()             -- 先月

-- 結合
status = "未払" and 請求額 > 100000

-- 並び替え（query の末尾）
order by 請求日 desc, レコード番号 asc

-- ページング（query の末尾）
limit 500 offset 1000
```

詳細は `references/query-syntax.md`。

---

## エラーレスポンス対処

```json
{
  "code": "GAIA_AP01",
  "message": "指定したアプリが見つかりません。アプリの削除またはアクセス権がない可能性があります。",
  "id": "xxxxxxxx"
}
```

主要なエラーコード（実観測値ベース・公式仕様の最新は cybozu.dev で確認）:

| コード | 意味 | 対処 |
|--------|-----|------|
| `CB_AU01` | 認証失敗 | API トークン誤り / 期限切れ |
| `CB_NO02` | パーミッション不足 | アプリのレコード閲覧権を確認 |
| `GAIA_AP01` | アプリが見つからない | app ID が間違い / アクセス権なし |
| `GAIA_IQ11` | クエリ文法エラー | query パラメータ確認 |
| `GAIA_RE01` | レコード数上限超過 | offset 10000 問題、cursor へ |
| `GAIA_RE03` | cursor が見つからない | 10 分失効。cursor 再作成 |
| `CB_NO04` / HTTP 520 | レート制限・短時間集中 | 指数バックオフして再試行 |

> HTTP ステータスと併用される。本番運用ではステータスコード（401/403/404/409/429/5xx）と body の `code` フィールド両方を見るのが安全。

---

## モックモード（受講者向け）

API トークンを当日用意できない受講者は、以下の関数で代替できる:

```javascript
const USE_MOCK = true;  // ← 当日 false に切り替え

function fetchKintoneRecords_() {
  if (USE_MOCK) {
    return JSON.parse(
      DriveApp.getFileById('SAMPLE_FILE_ID').getBlob().getDataAsString()
    ).records;
  }
  // 本物の処理...
}
```

サンプル JSON のスキーマは `references/mock-sample.md` を参照。

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| 401 が返る | API トークン誤り | スクリプトプロパティを再確認、トークンを再発行 |
| 403 が返る | アプリの「レコード閲覧」権限なし | Kintone 管理者にアプリ権限設定を依頼 |
| 5XX が返る | Kintone 側障害 / リクエスト過多 | リトライ（指数バックオフ） |
| `getContentText()` が文字化け | エンコーディング | `UrlFetchApp` は UTF-8 デフォルト。サブドメインの確認 |
| GAS タイムアウト（6分） | 大量レコード | cursor API + 6分ごとに状態保存して再開 |

---

## 参考リンク

| トピック | URL |
|----------|-----|
| Kintone 公式 REST API リファレンス | https://cybozu.dev/ja/kintone/docs/rest-api/ |
| REST API 共通仕様（レート制限・認証・エラー） | https://cybozu.dev/ja/kintone/docs/rest-api/overview/kintone-rest-api-overview/ |
| レコード取得 API | https://cybozu.dev/ja/kintone/docs/rest-api/records/get-records/ |
| cursor 作成 API（同時数・size 上限などの記載） | https://cybozu.dev/ja/kintone/docs/rest-api/records/add-cursor/ |
| cursor 取得 API | https://cybozu.dev/ja/kintone/docs/rest-api/records/get-cursor/ |
| 検索クエリ文法 | https://cybozu.dev/ja/kintone/docs/overview/query/ |
| API トークン発行手順（公式ヘルプ） | https://jp.cybozu.help/k/ja/id/040835.html |

---

## このスキルの使い方（Claude 向け）

ユーザーから「Kintone から〇〇を取ってきて」「kintone REST 叩く GAS 書いて」と依頼されたら:

1. **対象アプリ**: アプリ ID とサブドメインを聞く（持ってなければ取得手順を案内）
2. **API トークン**: 発行済みか確認。なければ Kintone アプリ設定 > API トークン から発行手順を案内
3. **取得条件**: query を組み立てる（このスキル本文の文法を参照）
4. **件数規模**: 1万件超なら最初から cursor API を提案
5. **保存先**: スクリプトプロパティに `KINTONE_SUBDOMAIN` / `KINTONE_APP_ID` / `KINTONE_TOKEN` を保存する案内を必ず入れる
6. **コード生成**: 上記ミニマム実装を雛形に、ユーザーの要件に合わせて書く

**禁止事項**:
- API トークンを `.gs` ファイル本文に直書きするコードを生成しない
- README やドキュメントにトークンの実値を書かない

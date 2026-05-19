# Kintone query 文法 詳細リファレンス

レコード取得 API（`records.json`）の `query` パラメータで使える文法をまとめる。

## 基本構造

```
[絞り込み条件] [order by] [limit] [offset]
```

すべて省略可能。何も書かなければ「全件・登録順」になる。

## 比較演算子

| 演算子 | 例 | 説明 |
|--------|-----|------|
| `=` | `状態 = "未払"` | 完全一致 |
| `!=` | `状態 != "完了"` | 不一致 |
| `>` `<` | `金額 > 100000` | 大なり / 小なり |
| `>=` `<=` | `金額 >= 100000` | 以上 / 以下 |
| `in` | `状態 in ("未払", "保留")` | リスト一致 |
| `not in` | `状態 not in ("完了")` | リスト不一致 |
| `like` | `取引先 like "*商事*"` | 部分一致（`*` ワイルドカード） |
| `not like` | `取引先 not like "テスト*"` | 部分不一致 |

## 論理演算子

```
状態 = "未払" and 請求額 > 100000
状態 = "未払" or 状態 = "保留"
(状態 = "未払" or 状態 = "保留") and 請求額 > 100000
```

`and` と `or` を混在させるときは括弧を使う。

## 日付関数

| 関数 | 例 | 説明 |
|------|-----|------|
| `TODAY()` | `請求日 = TODAY()` | 今日 |
| `YESTERDAY()` | `請求日 = YESTERDAY()` | 昨日 |
| `TOMORROW()` | `支払期日 = TOMORROW()` | 明日 |
| `FROM_TODAY(n, UNIT)` | `更新日時 > FROM_TODAY(-7, DAYS)` | 今日基準で n 単位（`DAYS` / `WEEKS` / `MONTHS` / `YEARS`） |
| `THIS_WEEK()` | `請求日 in (THIS_WEEK())` | 今週（月〜日） |
| `LAST_WEEK()` | `請求日 in (LAST_WEEK())` | 先週 |
| `THIS_MONTH()` | `請求日 in (THIS_MONTH())` | 今月 |
| `LAST_MONTH()` | `請求日 in (LAST_MONTH())` | 先月 |
| `THIS_YEAR()` | `請求日 in (THIS_YEAR())` | 今年 |
| `NEXT_WEEK()` / `NEXT_MONTH()` / `NEXT_YEAR()` | `請求日 in (NEXT_MONTH())` | 翌週 / 翌月 / 翌年 |
| `NOW()` | `更新日時 > NOW()` | 現在日時 |

ISO8601 リテラルも使える:

```
作成日時 > "2026-04-01T00:00:00+0900"
請求日 = "2026-05-01"
```

## ユーザー関連関数

```
作成者 in (LOGINUSER())        -- 自分が作ったレコード
担当者 in (LOGINUSER())         -- 自分が担当
更新者 in ("user@example.com")  -- メアド指定
```

## 並び替え

```
order by 請求日 desc
order by 請求日 desc, レコード番号 asc
```

複数キーはカンマで連結。

## ページング

```
limit 500 offset 0
limit 500 offset 500
```

- `limit` 最大 500
- `offset` 最大 10,000（超えるなら cursor API へ）

## 文字列内のエスケープ

ダブルクォート（`"`）を含めたいときはバックスラッシュ:

```
取引先 = "山田 \"商店\" 株式会社"
```

シングルクォート（`'`）は GAS の `encodeURIComponent` 後にそのまま渡せる。

## URL エンコード（GAS から叩くとき）

`query` パラメータは URL エンコードが必要:

```javascript
const query = '状態 = "未払" and 請求額 > 100000 order by 請求日 desc limit 500';
const url = `https://${subdomain}.cybozu.com/k/v1/records.json`
  + `?app=${appId}&query=${encodeURIComponent(query)}`;
```

## よく使うパターン

### 「今月の未払請求案件」

```
状態 = "未払" and 請求日 in (THIS_MONTH()) order by 支払期日 asc
```

### 「支払期日を過ぎても未払の案件」

```
状態 = "未払" and 支払期日 < TODAY() order by 支払期日 asc
```

### 「先月作成された全レコード」

```
作成日時 in (LAST_MONTH()) order by 作成日時 asc
```

### 「金額帯で絞り込み + 並び替え」

```
請求額 >= 100000 and 請求額 < 1000000 order by 請求額 desc limit 100
```

### 「テキスト部分一致 + 状態フィルタ」

```
取引先 like "*商事*" and 状態 in ("未払", "保留")
```

## 注意点

- フィールド名は **Kintone の「フィールドコード」** を使う（ラベルではない）。アプリ設定の各フィールド > 「フィールドコード」で確認。
- スペース・記号を含むフィールドコードは引用符で囲む: `"取引先 名"`
- `*` を含む文字列を完全一致で検索したいときは `like` で `\*` とエスケープ

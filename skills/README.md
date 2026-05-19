# 応用5 配布スキル

応用5「Claude Code で作る請求データ自動収集 × Live Artifact ダッシュボード」の受講者向けに配布するスキル集です。Claude Code から `Skill` ツール経由で自動的に発火し、ハンズオン中に必要な仕様・コマンドを Claude に思い出させます。

## 同梱スキル

| スキル | 用途 | 必要な前提 |
|--------|------|----------|
| `kintone-api` | Kintone REST API（レコード取得・query 文法・ページング・API トークン認証）の知識を Claude に与える | Kintone トライアル可 |
| `gas-clasp` | Clasp 環境のチェック → 無ければインストール案内 → GAS プロジェクト作成 → スクリプトプロパティへの API キー保存 → 時間トリガー設定までを案内 | 個人 Google アカウント |
| `invox-api` | invox 受取請求書 API（OAuth 2.0 + refresh_token）の操作知識 ／ Kintone と並列で受取請求書を Sheets に取り込みたい契約者向け | **invox プロフェッショナルプラン契約済み** |

> 💡 **invox スキルは「応用5 本編スコープ外」**
> 応用5 のハンズオン本編は **`kintone-api` + `gas-clasp` の 2 つだけ** で完結します。`invox-api` は **invox プロフェッショナルプラン契約済み** で API 利用申請（client_id 発行）を済ませた受講者向けのオプション。未契約者は触らなくて OK です。本格運用したい場合のフォローアップ用に同梱しています。参考資料版の解説は `references/invox-連携ガイド.md` を参照。

## インストール手順

### 方法 A: 自動インストール（推奨）

```bash
cd /path/to/ClaudeCode_handson
./skills/install.sh
```

`~/.claude/skills/` に各スキルがコピーされます。既に同名スキルがある場合はバックアップを取ったうえで上書きします。

### 方法 B: 手動コピー

```bash
cp -R skills/kintone-api ~/.claude/skills/
cp -R skills/gas-clasp ~/.claude/skills/
cp -R skills/invox-api ~/.claude/skills/    # 契約者のみ任意
```

### 方法 C: シンボリックリンク（開発者向け）

リポジトリの更新をそのまま反映したい場合:

```bash
ln -s "$(pwd)/skills/kintone-api" ~/.claude/skills/kintone-api
ln -s "$(pwd)/skills/gas-clasp" ~/.claude/skills/gas-clasp
ln -s "$(pwd)/skills/invox-api" ~/.claude/skills/invox-api
```

## 動作確認

Claude Code を起動して以下のように聞くと、スキルが発火するか確認できます。

```
> Kintone REST API のレコード取得ってどう書く?
→ kintone-api スキルが発火

> Clasp の環境セットアップして
→ gas-clasp スキルが発火

> invox の受取請求書 API を GAS から叩きたい
→ invox-api スキルが発火（契約済みのときだけ実用）
```

スキルが発火しない場合は `~/.claude/skills/` 配下にディレクトリが正しくコピーされているか確認してください。各スキルのトップに `SKILL.md` がある構造が必要です。

## アンインストール

```bash
rm -rf ~/.claude/skills/kintone-api
rm -rf ~/.claude/skills/gas-clasp
rm -rf ~/.claude/skills/invox-api
```

## ライセンス

教材付属のサンプルとして MIT ライセンスで配布します。商用利用・改変・再配布可。ただし API キーや API トークンは受講者自身で管理してください。

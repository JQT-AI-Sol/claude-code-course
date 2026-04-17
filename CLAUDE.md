# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## リポジトリ概要

非エンジニア向け「Claude Code 活用術」講座の教材リポジトリ。全4回のハンズオン講座資料（Markdown）、Notion配信用スクリプト、スクリーンショット・図版を管理する。

## 構成

- `curriculum.md` — 講座全体のカリキュラム設計（商品ラインナップ、導線設計、MENTA伴走プラン等）
- `00_事前準備.md` 〜 `04_第4回_Vercelデプロイ.md` — 各回の教材本体（講義＋ハンズオン手順）
- `push-to-notion.py` — 教材MarkdownをNotion APIで配信するPythonスクリプト（環境変数 `NOTION_TOKEN` が必要）
- `images/` — 教材内で参照する概念図・フロー図（PNG）
- `screenshots/` — 各サービスのUI操作スクリーンショット（PNG）

## Notion配信スクリプト

```bash
# 実行前に環境変数を設定
export NOTION_TOKEN="your-token"
python3 push-to-notion.py
```

Markdownのインライン書式（太字、コード、リンク）をNotionのrich_textブロックに変換し、100ブロック単位で分割送信する。画像はGitHub raw URLを参照する設計。

## 教材編集時の注意

- 画像参照は `images/` と `screenshots/` の相対パスで統一されている
- スクリーンショットにAPIキー等が含まれる場合は黒塗り加工済みであること（コミット `1f03544` 参照）
- 教材の対象読者はプログラミング未経験者。専門用語には必ず平易な説明を添える
- 技術スタック前提: Node.js / Next.js / Supabase / GitHub / Vercel

## Google Drive 利用ルール

- Google Drive からの読み取りのみ許可
- ファイルの削除・移動は禁止
- 読み取ったデータを外部サービスに送信しない
- 社外秘フォルダ（名前に「confidential」を含む）にはアクセスしない

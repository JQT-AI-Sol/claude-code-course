"""
Claude Code講座のMarkdownファイルをNotionにプッシュするスクリプト
Usage: python3 push-to-notion.py
"""
import json
import re
import requests
import sys
import os

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}
API_BASE = "https://api.notion.com/v1"

# ファイル一覧（順番通り）
FILES = [
    ("00_事前準備.md", "事前準備 — 受講前にやっておくこと"),
    ("01_第1回_導入と基本操作.md", "第1回: 導入と基本操作"),
    ("02_第2回_ローカルアプリ開発.md", "第2回: ローカルアプリ開発"),
    ("03_第3回_Supabase_GitHub.md", "第3回: Supabase + GitHub"),
    ("04_第4回_Vercelデプロイ.md", "第4回: Vercel デプロイ"),
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def md_to_notion_blocks(md_text: str) -> list:
    """MarkdownをNotionブロックに変換する（簡易版）"""
    blocks = []
    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_content = []
    code_lang = ""

    while i < len(lines):
        line = lines[i]

        # コードブロック
        if line.startswith("```"):
            if in_code_block:
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": "\n".join(code_content)[:2000]}}],
                        "language": code_lang or "plain text",
                    }
                })
                code_content = []
                in_code_block = False
            else:
                in_code_block = True
                code_lang = line[3:].strip()
                lang_map = {
                    "bash": "bash", "sh": "bash", "shell": "bash",
                    "python": "python", "python3": "python",
                    "js": "javascript", "javascript": "javascript",
                    "ts": "typescript", "typescript": "typescript",
                    "json": "json", "yaml": "yaml", "sql": "sql",
                    "html": "html", "css": "css",
                }
                code_lang = lang_map.get(code_lang, "plain text")
            i += 1
            continue

        if in_code_block:
            code_content.append(line)
            i += 1
            continue

        # 見出し
        if line.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:].strip()[:2000]}}]}
            })
        elif line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:].strip()[:2000]}}]}
            })
        elif line.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:].strip()[:2000]}}]}
            })

        # コールアウト（> 💡 で始まる行）
        elif line.startswith("> 💡") or line.startswith("> **"):
            callout_lines = [line.lstrip("> ").strip()]
            j = i + 1
            while j < len(lines) and lines[j].startswith(">"):
                callout_lines.append(lines[j].lstrip("> ").strip())
                j += 1
            content = "\n".join(callout_lines)
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": content[:2000]}}],
                    "icon": {"type": "emoji", "emoji": "💡"},
                }
            })
            i = j
            continue

        # セキュリティコールアウト（> 🔒）
        elif line.startswith("> 🔒"):
            callout_lines = [line.lstrip("> ").strip()]
            j = i + 1
            while j < len(lines) and lines[j].startswith(">"):
                callout_lines.append(lines[j].lstrip("> ").strip())
                j += 1
            content = "\n".join(callout_lines)
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": content[:2000]}}],
                    "icon": {"type": "emoji", "emoji": "🔒"},
                }
            })
            i = j
            continue

        # 参考リンク（> 📎）
        elif line.startswith("> 📎"):
            callout_lines = [line.lstrip("> ").strip()]
            j = i + 1
            while j < len(lines) and lines[j].startswith(">"):
                callout_lines.append(lines[j].lstrip("> ").strip())
                j += 1
            content = "\n".join(callout_lines)
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": content[:2000]}}],
                    "icon": {"type": "emoji", "emoji": "📎"},
                }
            })
            i = j
            continue

        # 通常の引用（> で始まるがコールアウトでない）
        elif line.startswith("> "):
            quote_lines = [line[2:].strip()]
            j = i + 1
            while j < len(lines) and lines[j].startswith(">"):
                quote_lines.append(lines[j].lstrip("> ").strip())
                j += 1
            content = "\n".join(quote_lines)
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": content[:2000]}}],
                    "icon": {"type": "emoji", "emoji": "💡"},
                }
            })
            i = j
            continue

        # チェックリスト
        elif line.startswith("- [ ] ") or line.startswith("- [x] "):
            checked = line.startswith("- [x] ")
            text = line[6:].strip()
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                    "checked": checked,
                }
            })

        # 箇条書き
        elif line.startswith("- "):
            text = line[2:].strip()
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                }
            })

        # 番号付きリスト
        elif re.match(r"^\d+\. ", line):
            text = re.sub(r"^\d+\. ", "", line).strip()
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                }
            })

        # 区切り線
        elif line.strip() == "---":
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {},
            })

        # 画像
        elif line.startswith("!["):
            # ![alt](path) 形式 — ローカル画像はスキップ
            pass

        # イタリック（キャプション）
        elif line.startswith("*") and line.endswith("*") and not line.startswith("**"):
            text = line.strip("*").strip()
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": text[:2000]}, "annotations": {"italic": True}}],
                }
            })

        # テーブル（簡易：| で始まる行はパラグラフとして扱う）
        elif line.startswith("|"):
            # テーブルヘッダーの区切り行はスキップ
            if re.match(r"^\|[-\s|:]+\|$", line):
                i += 1
                continue
            text = line.strip()
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                }
            })

        # 空行はスキップ
        elif line.strip() == "":
            pass

        # 通常のパラグラフ
        else:
            text = line.strip()
            if text:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                    }
                })

        i += 1

    return blocks


def create_page(parent_id: str, title: str, blocks: list) -> str:
    """Notionにページを作成する"""
    # Notion APIは1回のリクエストで100ブロックまで
    first_batch = blocks[:100]

    payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": [{"type": "text", "text": {"content": title}}]
        },
        "children": first_batch,
    }

    resp = requests.post(f"{API_BASE}/pages", headers=HEADERS, json=payload)
    if resp.status_code != 200:
        print(f"  Error creating page: {resp.status_code}")
        print(f"  {resp.text[:500]}")
        return ""

    page_id = resp.json()["id"]
    print(f"  Created: {title} ({page_id})")

    # 残りのブロックを追加（100個ずつ）
    remaining = blocks[100:]
    batch_num = 1
    while remaining:
        batch = remaining[:100]
        remaining = remaining[100:]
        batch_num += 1

        resp = requests.patch(
            f"{API_BASE}/blocks/{page_id}/children",
            headers=HEADERS,
            json={"children": batch},
        )
        if resp.status_code != 200:
            print(f"  Error appending batch {batch_num}: {resp.status_code}")
            print(f"  {resp.text[:300]}")
        else:
            print(f"  Appended batch {batch_num} ({len(batch)} blocks)")

    return page_id


def main():
    if not NOTION_TOKEN:
        print("Error: NOTION_TOKEN environment variable not set")
        sys.exit(1)

    # 親ページIDが引数で渡された場合
    if len(sys.argv) > 1:
        parent_id = sys.argv[1]
    else:
        # 親ページを新規作成（ワークスペースのトップレベル）
        # まずワークスペースを検索
        resp = requests.post(
            f"{API_BASE}/search",
            headers=HEADERS,
            json={"query": "", "page_size": 1},
        )
        print("Searching for existing pages...")
        print(f"Found {len(resp.json().get('results', []))} pages")
        print()
        print("Usage: python3 push-to-notion.py <parent_page_id>")
        print()
        print("1. Notionで講座教材を置くページを作成")
        print("2. そのページのURLからIDを取得")
        print("   例: https://notion.so/My-Page-abc123def456")
        print("   → parent_page_id = abc123def456")
        print("3. そのページで Integration を接続（... → コネクション → 追加）")
        print("4. python3 push-to-notion.py abc123def456")
        sys.exit(0)

    print(f"Parent page: {parent_id}")
    print(f"Pushing {len(FILES)} files to Notion...")
    print()

    for filename, title in FILES:
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  Skipping {filename} (not found)")
            continue

        print(f"Processing: {filename}")
        with open(filepath, "r") as f:
            md_content = f.read()

        blocks = md_to_notion_blocks(md_content)
        print(f"  Converted to {len(blocks)} blocks")

        page_id = create_page(parent_id, title, blocks)
        if page_id:
            print(f"  Done!")
        print()

    print("All files pushed to Notion!")


if __name__ == "__main__":
    main()

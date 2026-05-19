#!/usr/bin/env bash
# 応用5 配布スキル インストーラー
# 使い方: ./skills/install.sh
#
# ~/.claude/skills/ に各スキルをコピーします。
# 同名スキルが既にある場合は、~/.claude/skills/.backup-YYYYMMDDHHMMSS/ に退避します。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.claude/skills"
SKILLS=("kintone-api" "gas-clasp" "invox-api")

echo "==> 応用5 配布スキル インストーラー"
echo

# ~/.claude/skills/ が無ければ作る
if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "  [info] ${TARGET_DIR} が無いので作成します"
  mkdir -p "${TARGET_DIR}"
fi

# バックアップ用ディレクトリ
BACKUP_DIR="${TARGET_DIR}/.backup-$(date +%Y%m%d%H%M%S)"
NEEDS_BACKUP=0

for skill in "${SKILLS[@]}"; do
  if [[ -e "${TARGET_DIR}/${skill}" ]]; then
    NEEDS_BACKUP=1
    break
  fi
done

if [[ "${NEEDS_BACKUP}" -eq 1 ]]; then
  echo "  [info] 既存スキルをバックアップ: ${BACKUP_DIR}"
  mkdir -p "${BACKUP_DIR}"
fi

# 各スキルをコピー
for skill in "${SKILLS[@]}"; do
  src="${SCRIPT_DIR}/${skill}"
  dest="${TARGET_DIR}/${skill}"

  if [[ ! -d "${src}" ]]; then
    echo "  [warn] ${src} が見つかりません。スキップします。"
    continue
  fi

  if [[ -e "${dest}" ]]; then
    echo "  [info] 既存の ${skill} をバックアップに退避"
    mv "${dest}" "${BACKUP_DIR}/"
  fi

  cp -R "${src}" "${dest}"
  echo "  [ok]   ${skill} をインストール"
done

echo
echo "==> 完了"
echo
echo "確認:"
ls -1 "${TARGET_DIR}" | grep -v '^\.backup-' | sed 's/^/  - /'
echo
echo "Claude Code を再起動するとスキルが認識されます。"

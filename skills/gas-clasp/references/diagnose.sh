#!/usr/bin/env bash
# gas-clasp スキル付属の環境診断スクリプト
# 使い方: ./diagnose.sh
#
# Node.js / npm / Clasp / Apps Script API 設定を一括チェックして
# 不足分を画面に表示します。

set +e   # 個別チェック失敗で全体を止めない

echo "==> GAS × Clasp 環境診断"
echo

PASS_MARK="✅"
FAIL_MARK="❌"
WARN_MARK="⚠️ "

check() {
  local name="$1"
  local cmd="$2"
  local expected="$3"
  local fix_hint="$4"

  local version
  version="$(eval "${cmd}" 2>/dev/null | head -n1 || echo "")"

  if [[ -z "${version}" ]]; then
    echo "  ${FAIL_MARK} ${name}: 未インストール"
    echo "         → ${fix_hint}"
    return 1
  fi

  echo "  ${PASS_MARK} ${name}: ${version}"
  if [[ -n "${expected}" ]] && ! echo "${version}" | grep -qE "${expected}"; then
    echo "  ${WARN_MARK} ${name} のバージョンが想定外。${fix_hint}"
  fi
  return 0
}

# 1. Node.js
check "Node.js" "node -v" "v(2[0-9]|[3-9][0-9])\." \
  "Node.js 20 以上が必要（推奨 22 LTS）。Mac: 'brew install node@22' / Windows: https://nodejs.org/ から 22 LTS をインストール"

# 2. npm
check "npm    " "npm -v" "" \
  "Node.js を入れ直すと一緒に入ります"

# 3. Clasp
check "Clasp  " "clasp --version" "^3\." \
  "Clasp v3 が必要。'npm install -g @google/clasp@latest' を実行"

echo
echo "==> 補助チェック"

# 4. Clasp ログイン状態
if clasp --version >/dev/null 2>&1; then
  if clasp list-scripts >/dev/null 2>&1; then
    echo "  ${PASS_MARK} Clasp 認証済み"
  else
    echo "  ${WARN_MARK} Clasp 未ログイン → 'clasp login' を実行してください"
  fi
fi

# 5. Apps Script API 有効化リマインダ
echo "  ${WARN_MARK} Apps Script API の有効化は手動確認が必要:"
echo "         https://script.google.com/home/usersettings"
echo "         （ブラウザで開いてトグルが ON になっているか確認）"

echo
echo "==> 診断完了"

#!/usr/bin/env bash
#
# Ralph Loop verify.sh template.
#
# Usage:
#   cp ralph/references/verify-template.sh verify.sh
#   chmod +x verify.sh
#   edit verify.sh and replace the placeholder checks
#   ./verify.sh
#
# Contract: final output is one JSON object; exit 0=pass, 1=fail.
# Score: lower is better (0=perfect, like loss). PASS=0, FAIL=1 for discrete tasks.

set -euo pipefail

# macOS-compatible SHA-256 helper. Keep in sync with Ralph v3 runner.
file_hash() {
  if command -v sha256sum &>/dev/null; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

json_escape() {
  local value=${1:-}
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  value=${value//$'\n'/ }
  value=${value//$'\r'/ }
  printf '%s' "$value"
}

emit_result() {
  local status=$1
  local score=$2
  local details=$3
  printf '{"status":"%s","score":%s,"details":"%s"}\n' \
    "$status" "$score" "$(json_escape "$details")"
}

fail() {
  emit_result "FAIL" "${2:-1}" "$1"
  exit 1
}

VERIFY_HASH=$(file_hash "$0")

# Replace the examples below with project-specific validation.
# Keep checks deterministic and machine-verifiable.

# Example: required file exists.
[[ -f "README.md" ]] || fail "README.md is missing; verify_hash=$VERIFY_HASH"

# Example: run tests if the project has a package.json.
if [[ -f "package.json" ]]; then
  npm test >/tmp/ralph-verify-npm-test.log 2>&1 \
    || fail "npm test failed; see /tmp/ralph-verify-npm-test.log"
fi

# Example: compute a placeholder score. Replace with real metrics.
SCORE=0
DETAILS="placeholder checks passed; replace verify-template.sh logic"

emit_result "PASS" "$SCORE" "$DETAILS"

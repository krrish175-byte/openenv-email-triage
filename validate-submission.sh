#!/usr/bin/env bash
set -uo pipefail

PING_URL="${1:-}"
REPO_DIR="${2:-.}"

if [ -z "$PING_URL" ]; then
  echo "Usage: $0 <ping_url> [repo_dir]"
  exit 1
fi

PING_URL="${PING_URL%/}"
PASS=0

echo "========================================"
echo "OpenEnv Submission Validator"
echo "========================================"
echo "Repo: $REPO_DIR"
echo "Ping URL: $PING_URL"
echo ""

# Step 1: Ping HF Space
echo "[Step 1/3] Pinging $PING_URL/reset ..."
HTTP_CODE=$(curl -s -o /tmp/curl_out -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" -d '{}' \
  "$PING_URL/reset" --max-time 30 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
  echo "PASSED -- HF Space is live and responds to /reset"
  PASS=$((PASS + 1))
else
  echo "FAILED -- HF Space /reset returned HTTP $HTTP_CODE"
  exit 1
fi

# Step 2: Docker build
echo ""
echo "[Step 2/3] Running docker build ..."
if ! command -v docker &>/dev/null; then
  echo "FAILED -- docker not found"
  exit 1
fi

if docker build "$REPO_DIR" 2>&1 | tail -5; then
  echo "PASSED -- Docker build succeeded"
  PASS=$((PASS + 1))
else
  echo "FAILED -- Docker build failed"
  exit 1
fi

# Step 3: openenv validate
echo ""
echo "[Step 3/3] Running openenv validate ..."
if ! command -v openenv &>/dev/null; then
  echo "FAILED -- openenv not found. Run: pip install openenv-core"
  exit 1
fi

if (cd "$REPO_DIR" && openenv validate 2>&1); then
  echo "PASSED -- openenv validate passed"
  PASS=$((PASS + 1))
else
  echo "FAILED -- openenv validate failed"
  exit 1
fi

echo ""
echo "========================================"
echo "All $PASS/3 checks passed!"
echo "Your submission is ready to submit."
echo "========================================"

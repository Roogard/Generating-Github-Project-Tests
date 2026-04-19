#!/usr/bin/env bash
# Three-run memory ablation experiment.
#
# Run 1: use_rag=false, save_to_rag=false  (baseline)
# Run 2: use_rag=false, save_to_rag=true   (populate memory)
# Run 3: use_rag=true,  save_to_rag=false  (with memory)
#
# Prereqs: backend running on localhost:8000, ChromaDB wiped before Run 1.
#
# Usage:  scripts/memory_ablation.sh <phase>
#   phase = 1 | 2 | 3   (baseline / populate / with-memory)

set -euo pipefail

PHASE="${1:-}"
PROVIDER="${PROVIDER:-anthropic}"
PRESET="${PRESET:-default}"
LIMIT="${LIMIT:-15}"
API="http://127.0.0.1:8000/api"

REPOS=(
  "https://github.com/tqdm/tqdm"
  "https://github.com/cookiecutter/cookiecutter"
  "https://github.com/psf/black"
)

case "$PHASE" in
  1) USE_RAG=false; SAVE_TO_RAG=false; LABEL="baseline" ;;
  2) USE_RAG=false; SAVE_TO_RAG=true;  LABEL="populate" ;;
  3) USE_RAG=true;  SAVE_TO_RAG=false; LABEL="with-memory" ;;
  *) echo "usage: $0 {1|2|3}"; exit 1 ;;
esac

echo "=== Run phase $PHASE ($LABEL) ==="
echo "use_rag=$USE_RAG  save_to_rag=$SAVE_TO_RAG  limit=$LIMIT  preset=$PRESET"
echo

RUN_IDS=()
for repo in "${REPOS[@]}"; do
  body=$(cat <<EOF
{
  "repo_url": "$repo",
  "provider": "$PROVIDER",
  "preset": "$PRESET",
  "function_limit": $LIMIT,
  "install_deps": true,
  "fix_pass": false,
  "save_to_db": true,
  "save_to_rag": $SAVE_TO_RAG,
  "rag_success_only": true,
  "use_rag": $USE_RAG
}
EOF
)
  resp=$(curl -s -X POST "$API/runs/" -H "Content-Type: application/json" -d "$body")
  id=$(echo "$resp" | python -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
  echo "  queued run $id for $repo"
  RUN_IDS+=("$id")
done

echo
echo "Polling ${#RUN_IDS[@]} runs..."
while true; do
  all_done=true
  for id in "${RUN_IDS[@]}"; do
    s=$(curl -s "$API/runs/$id/status" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''), d.get('progress_current',0), d.get('progress_total',0))")
    echo "  run $id: $s"
    status=$(echo "$s" | awk '{print $1}')
    [ "$status" != "done" ] && [ "$status" != "error" ] && all_done=false
  done
  $all_done && break
  echo "  ---"
  sleep 30
done

echo
echo "Phase $PHASE ($LABEL) complete."
curl -s "$API/vectordb/stats"
echo
curl -s "$API/analytics/summary" | python -m json.tool

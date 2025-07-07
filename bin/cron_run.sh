#!/usr/bin/env bash

set -euo pipefail

print_help() {
  cat <<EOF
Usage: $(basename "$0") <script>

Run a Python script from the current git repo root with virtualenv activation and logging.

Arguments:
  <script>        Path to the Python script relative to repo root (e.g., scripts/uptime_check.py)

Environment:
  Assumes virtualenv at: <repo_root>/.venv
  Logs status to: logs/cron_<script>.status (slashes converted to underscores)

Setup:
  git clone --single-branch --depth 1 --branch live git@github.com:user_name/repo_name.git
  cd repo_name
  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
EOF
}

if [[ $# -ne 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  print_help
  exit 0
fi

SCRIPT_REL="$1"
REPO_ROOT=$(git rev-parse --show-toplevel)
SCRIPT_PATH="$REPO_ROOT/$SCRIPT_REL"
SCRIPT_KEY="${SCRIPT_REL//\//_}"
LOG_FILE="$REPO_ROOT/logs/cron_${SCRIPT_KEY%.*}.status"
VENV_DIR="$REPO_ROOT/.venv"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

mkdir -p "$REPO_ROOT/logs"

{
  cd "$REPO_ROOT"
  git pull --rebase || true
  source "$VENV_DIR/bin/activate"
  python "$SCRIPT_PATH"
  echo "$TIMESTAMP SUCCESS" >>"$LOG_FILE"
} || {
  echo "$TIMESTAMP FAIL" >>"$LOG_FILE"
  exit 1
}

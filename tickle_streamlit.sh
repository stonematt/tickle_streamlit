#!/usr/bin/env bash

# tickle_streamlit - Bash wrapper for the tickle_streamlit CLI
# Provides convenient access to the Python CLI with bash-style help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="python3"

print_help() {
    cat <<EOF
tickle_streamlit - Streamlit uptime monitoring CLI

USAGE:
    $(basename "$0") <command> [options]

COMMANDS:
    list                    List all configured sites
    check                   Check site uptime
    help                    Show this help message

CHECK OPTIONS:
    --dry-run              Only check content, do not restart
    --site <name>          Only check the specified site by name
    --config <path>        Path to sites configuration file

EXAMPLES:
    $(basename "$0") list                           # List all configured sites
    $(basename "$0") check                          # Check all sites
    $(basename "$0") check --dry-run                # Check without restarting
    $(basename "$0") check --site lookout           # Check specific site
    $(basename "$0") check --site lookout --dry-run # Check specific site safely

For more detailed help, run:
    $(basename "$0") <command> --help

EOF
}

# Check if python3 is available
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required but not found in PATH" >&2
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "$SCRIPT_DIR/tickle_streamlit/__main__.py" ]]; then
    echo "Error: tickle_streamlit package not found in script directory" >&2
    exit 1
fi

# Handle help command or no arguments
if [[ $# -eq 0 ]] || [[ "$1" == "help" ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    print_help
    exit 0
fi

# Pass all arguments to the Python CLI
cd "$SCRIPT_DIR"
exec "$PYTHON_CMD" -m tickle_streamlit "$@"
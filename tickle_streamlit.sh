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
    $(basename "$0") [command] [options]

COMMANDS:
    list                    List all configured sites
    check                   Check site uptime
    add                     Add a new site to configuration
    remove                  Remove a site from configuration
    validate                Validate configuration file
    help                    Show this help message

CHECK OPTIONS:
    [site]                 Check specific site by name
    --dry-run              Only check content, do not restart
    --site <name>          Only check the specified site by name (legacy)
    --config <path>        Path to sites configuration file

ADD OPTIONS:
    <name> <url> <must_contain>    Site details (required)
    --streamlit                    Site is a Streamlit app
    --debug                        Enable debug logging
    --selector <css>               Custom CSS selector
    --dry-run                      Preview without adding
    --interactive, -i              Interactive guided addition

REMOVE OPTIONS:
    <name>                         Site name to remove

EXAMPLES:
    $(basename "$0")                                 # Check all sites (default)
    $(basename "$0") --dry-run                      # Check without restarting
    $(basename "$0") check lookout                  # Check specific site
    $(basename "$0") --site lookout                 # Check specific site (legacy)
    $(basename "$0") list                            # List all configured sites
    $(basename "$0") check lookout --dry-run        # Check specific site safely
    $(basename "$0") add mysite https://example.com "Welcome" --streamlit
    $(basename "$0") add --interactive              # Interactive guided addition
    $(basename "$0") add mysite https://example.com "Welcome" --dry-run  # Preview before adding
    $(basename "$0") remove mysite                   # Remove site from config
    $(basename "$0") validate                        # Validate configuration

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
if [[ $# -eq 0 ]]; then
    # Default action: check all sites
    cd "$SCRIPT_DIR"
    exec "$PYTHON_CMD" -m tickle_streamlit check
elif [[ "$1" == "help" ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    print_help
    exit 0
elif [[ "$1" != "list" && "$1" != "check" && "$1" != "add" && "$1" != "remove" && "$1" != "validate" ]]; then
    # If first arg is not a command, assume it's an option for 'check'
    cd "$SCRIPT_DIR"
    exec "$PYTHON_CMD" -m tickle_streamlit check "$@"
fi

# Pass all arguments to the Python CLI
cd "$SCRIPT_DIR"
exec "$PYTHON_CMD" -m tickle_streamlit "$@"
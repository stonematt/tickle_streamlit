# Agent Guidelines for tickle_streamlit

## Branch Management
- **Prefer to work on feature/fix branches** rather than main
- **Create branches**: `git checkout -b feature/cli-management` or `git checkout -b fix/config-validation`
- **Test thoroughly** before merging back to main
- **Code is running remotely** - maintain backward compatibility

## Commands
- **New CLI**: `python3 -m tickle_streamlit [list|check] [--dry-run] [--site <name>]`
- **Legacy script**: `python uptime_check.py [--dry-run] [--site <name>]` (maintained for compatibility)
- **Install dependencies**: `pip install -r requirements.txt && playwright install`
- **No test framework**: Manual testing via --dry-run and --site flags

## Code Style
- **Imports**: Standard library first, then third-party, then local modules
- **Type hints**: Use for function parameters and returns (str, bool, dict, None)
- **Naming**: snake_case for variables/functions, UPPER_CASE for constants
- **Error handling**: Try/except with specific exception types, log first line of error
- **Logging**: Use `log_site()` for site-context messages, `app_logger()` for module loggers
- **Async**: Use async/await for Playwright operations, `asyncio.gather()` for concurrency
- **Docstrings**: Triple quotes with param/return descriptions
- **File structure**: Main script in root, utilities in utils/ directory, CLI in tickle_streamlit/ package

## CLI Development
- **Subcommands**: Use argparse subparsers for multi-command interface
- **Help text**: Provide comprehensive help with examples
- **Exit codes**: Return 0 for success, 1 for errors
- **Visual feedback**: Use emojis/status indicators for user-friendly output
- **Backward compatibility**: Never break existing uptime_check.py functionality
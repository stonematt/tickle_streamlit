# Agent Guidelines for tickle_streamlit

## Commands
- **Run main script**: `python uptime_check.py [--dry-run] [--site <name>]`
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
- **File structure**: Main script in root, utilities in utils/ directory
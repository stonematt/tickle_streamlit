# Agent Guidelines for tickle_streamlit

## Branch Management
- **Prefer to work on feature/fix branches** rather than main
- **Create branches**: `git checkout -b feature/cli-management` or `git checkout -b fix/config-validation`
- **Test thoroughly** before merging back to main
- **Code is running remotely** - maintain backward compatibility

## Commands
- **New CLI**: `python3 -m tickle_streamlit [list|check|add|remove|validate] [options]`
- **Bash wrapper**: `./tickle_streamlit.sh [command] [options]` (defaults to 'check')
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
- **Positional arguments**: Support intuitive syntax like `check <site-name>` alongside flag-based options

## Agent Workflow Hints

### Pre-Task Commit Check
**ALWAYS check git status before starting new work:**
- Run `git status` to check for uncommitted changes
- If uncommitted work exists, ask user: "I see uncommitted changes. Should I commit them before starting this new task?"
- This prevents mixing unrelated changes and maintains clean commit history
- Exception: User explicitly asks to continue without committing

### When to Commit
**DO commit when:**
- User explicitly requests: "commit", "commit this", "commit it"
- Switching topics with uncommitted changes (ask first)
- Completing a validated, working feature milestone
- Before starting risky or experimental work (create checkpoint)

**DON'T commit when:**
- Iterating on fixes or refinements (wait for validation)
- During active debugging sessions
- Making incremental improvements
- User explicitly says "don't commit until verified"

### Commit Message Format
```
Summary line (imperative mood, 50-70 characters)

Category changes:
- Specific change description using bullet points
- Group related changes together
- Use clear, concise language

Rationale: Brief explanation of technical decisions and approach.
```

### Focus Areas
- "Why" and architectural choices
- Scannable bullet points for human review
- Clean, focused commits on delivered functionality
- Avoid test results, code snippets, line-by-line descriptions
# tickle_streamlit

**tickle_streamlit** is a lightweight monitoring utility designed to keep Streamlit-hosted (and other) web apps responsive by checking for expected content and optionally triggering wake-up mechanisms.

## Features

- ✅ Playwright-based uptime checker
- ✅ Config-driven site list (`config/sites.json`)
- ✅ Detects if page content is missing
- ✅ Wakes sleeping Streamlit apps via the "Yes, get this app back up!" button
- ✅ Supports `--dry-run` and per-site `log_raw` inspection
- ✅ Smart logging with file+console output

## Usage

```bash
python uptime_check.py [--dry-run]
```

- `--dry-run` skips the wake-up click but still logs checks
- Sites must be configured in `config/sites.json`

## Configuration

Each site in `config/sites.json` should be defined like:

```json
{
  "name": "lookout",
  "url": "https://stonematt-lookout.streamlit.app/",
  "is_streamlit": true,
  "must_contain": "lookout post",
  "log_raw": true
}
```

### Keys

- `name`: A short name for logging
- `url`: Full site URL
- `is_streamlit`: Enable Streamlit-specific restart logic
- `must_contain`: Substring to verify site is live
- `log_raw` _(optional)_: If `true`, dumps raw HTML for inspection

## Logs

All logs are written to `logs/uptime.log` and follow this format:

```
2025-07-07 09:01:58 - INFO - log_util: lookout: Checking lookout at https://...
```

Raw HTML (if enabled) is saved as:

```
logs/{site_name}_raw.html
```

## Dependencies

Install via pip:

```bash
pip install -r requirements.txt
playwright install
```

Or use the Conda environment:

```bash
conda env create -f tickle_streamlit_env.yml
conda activate tickle_streamlit
```

## Cron Example

Run every 8 hours:

```bash
0 */8 * * * /path/to/uptime_check.py >> /path/to/cron.log 2>&1
```

---

© 2025 Matt Stone — Streamlit uptime monitoring made minimal.

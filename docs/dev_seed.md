# Dev Seed Script

This script creates a minimal set of development data (country, payment provider, their link, a company and a channel) useful for local testing.

Run from the project root. Example (PowerShell on Windows, using SQLite `dev.db` in project folder):

```bash
# على ويندوز PowerShell مع SQLite dev.db في نفس مجلد المشروع:
$env:DATABASE_URL = "sqlite:///./dev.db"
.\venv\Scripts\python.exe .\scripts\dev_seed.py
```

After running, you can use the following credentials in requests:

- `X-API-Key: dev-api-key`
- `channel_api_key: dev-channel-key`

# Fiverr Automation Agent

A local-first automation agent for managing Fiverr gigs, orders, and messages, with a FastAPI backend, a React dashboard, NVIDIA Nemotron for LLM generation, and Google Sheets integration.

## Quick Start

1. Clone the repository:

```bash
git clone <repository-url>
cd fiverr-agent
```

2. Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your Fiverr credentials, Google Sheets settings, and other configuration (see [Configuration](#configuration)).

3. Configure NVIDIA API (required for LLM content generation):

   Add your NVIDIA API key and model to `.env`:

   ```
   NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
   NVIDIA_API_KEY=your-api-key-here
   NVIDIA_MODEL=nemotron-3.5-super-vl-120b-a12b
   ```

4. Start all services with Docker Compose:

```bash
docker compose up --build
```

5. Open the dashboard:

   - Dashboard (frontend): http://localhost:5173
   - API (backend): http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs

6. Initialize the database (one time):

```bash
python scripts/init_db.py
```

## Configuration

Copy `.env.example` to `.env` and set the following variables:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `FIVERR_EMAIL` | Fiverr account email | Yes | you@example.com |
| `FIVERR_PASSWORD` | Fiverr account password | Yes | |
| `FIVERR_2FA_SECRET` | Two-factor authentication secret | No | JBSWY3DPEHPK3PXP |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Google service account credentials JSON | No | `{"type": "service_account", ...}` |
| `GOOGLE_SHEET_ID` | Target Google Sheet ID | No | `1BxiMVs0X...` |
| `NVIDIA_BASE_URL` | NVIDIA API base URL | Yes | https://integrate.api.nvidia.com/v1 |
| `NVIDIA_API_KEY` | NVIDIA API key | Yes | |
| `NVIDIA_MODEL` | NVIDIA model name | Yes | nemotron-3.5-super-vl-120b-a12b |
| `DATABASE_URL` | Database connection URL | Yes | sqlite+aiosqlite:///./test.db |
| `REDIS_URL` | Redis connection URL | No | redis://localhost:6379/0 |
| `DISCORD_WEBHOOK_URL` | Discord notifications webhook | No | |
| `SLACK_WEBHOOK_URL` | Slack notifications webhook | No | |
| `SMTP_HOST` | SMTP host for email notifications | No | |
| `SMTP_PORT` | SMTP port | No | 587 |
| `SMTP_USER` | SMTP username | No | |
| `SMTP_PASSWORD` | SMTP password | No | |
| `PROXY_API_URLS` | Proxy list API URLs | No | |
| `RATE_LIMIT_PER_HOUR` | Actions per hour limit | No | 3 |
| `MAX_GIGS_PER_RUN` | Max gigs per automation run | No | 2 |
| `SECRET_KEY` | Application secret key | Yes | change-this-in-production |

## Google Sheets Setup

1. Create a Google Cloud Platform project and enable the Google Sheets API.
2. Create a service account and download its JSON key file.
3. Share your target Google Sheet with the service account email (Editor access).
4. Paste the service account JSON into `GOOGLE_SHEETS_CREDENTIALS_JSON` in `.env`.
5. Set `GOOGLE_SHEET_ID` to the ID found in your sheet's URL.

The agent uses the sheet to log gigs, orders, and automation activity.

## Compliance

This tool is intended for personal productivity and account management on your own Fiverr account. Automating interactions with third-party platforms may be subject to that platform's Terms of Service. Use responsibly:

- Do not scrape or automate activity on accounts you do not own.
- Respect Fiverr's rate limits and terms of service.
- Store credentials securely; never commit `.env` or service account keys to version control.
- Review and approve AI-generated content before publishing.

## Services

| Service | Port | Description |
|---------|------|-------------|
| `app` | 8000 | FastAPI backend API |
| `redis` | 6379 | Redis cache / job queue |
| `nvidia` | NVIDIA API | LLM inference endpoint |
| `frontend` | 5173 | React dashboard (served via nginx) |

## Development

Run the backend locally:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run the frontend locally:

```bash
cd frontend
npm install
npm run dev
```

Run the test suite:

```bash
pytest
```

## Next Steps

After you have the stack deployed, follow these steps to start using the agent:

1. **Configure `.env`** — fill in `FIVERR_EMAIL`, `FIVERR_PASSWORD`, and (optionally) `FIVERR_2FA_SECRET`. See [Configuration](#configuration) and [Fiverr 2FA Setup](#fiverr-2fa-setup).
2. **Configure NVIDIA API** — set `NVIDIA_BASE_URL`, `NVIDIA_API_KEY`, and `NVIDIA_MODEL` in `.env` (see [Configuration](#configuration)).
3. **Start all services:**
   ```bash
   docker compose up --build
   ```
4. **Initialize the database (one time):**
   ```bash
   python scripts/init_db.py
   ```
5. **Seed Google Sheets** (if using Sheets integration):
   ```bash
   python scripts/seed_sheets.py
   ```
   Make sure `GOOGLE_SHEETS_CREDENTIALS_JSON` and `GOOGLE_SHEET_ID` are set and the sheet is shared with the service account email.
6. **Open the dashboard** at http://localhost:5173 and review the overview, gigs, orders, messages, analytics, settings, logs, and proxies pages.
7. **Add gigs to Google Sheets** with a `Status` of `pending` (or `draft`), then run the gig creation cycle from the dashboard or via the API.
8. **Review AI-generated content** before publishing — see the [Compliance](#compliance) note.
9. **Monitor logs and analytics** in the dashboard to track published gigs, synced orders, and revenue.

## Troubleshooting

| Issue | Likely cause | Fix |
|-------|--------------|-----|
| NVIDIA connection refused | NVIDIA API not reachable or wrong base URL | Confirm `NVIDIA_BASE_URL` in `.env`, check your `NVIDIA_API_KEY` is valid, and verify network access to the NVIDIA API endpoint. |
| Database connection error | Wrong `DATABASE_URL` or DB not initialized | Verify `DATABASE_URL` in `.env` and run `python scripts/init_db.py`. |
| 2FA prompt blocks login | Missing or invalid `FIVERR_2FA_SECRET` | Get a valid TOTP secret from Fiverr and set it in `.env`. See [Fiverr 2FA Setup](#fiverr-2fa-setup). |
| Google Sheets read fails | Invalid credentials JSON or sheet not shared | Validate `GOOGLE_SHEETS_CREDENTIALS_JSON`, set `GOOGLE_SHEET_ID`, and share the sheet with the service account email (Editor access). |
| No proxies returned | `PROXY_API_URLS` empty or source down | Set `PROXY_API_URLS` to one or more working proxy list URLs (see [Proxy Sources](#proxy-sources)) and run proxy validation from the dashboard. |
| Gig publish fails | Fiverr markup changed or rate limited | The agent logs the error; check the Logs page. Add a delay between gigs (`GIG_DELAY_SECONDS`) and lower `MAX_GIGS_PER_RUN`. |
| Tests fail | Missing Playwright browsers or env | Run `pip install -r requirements.txt`, `playwright install`, then `pytest tests/ -v`. |
| Frontend won't load | `node_modules` missing or dev server down | `cd frontend && npm install && npm run dev`, or use the Docker Compose `frontend` service (port 5173). |

## Fiverr 2FA Setup

The agent supports time-based one-time password (TOTP) two-factor authentication for Fiverr logins. When Fiverr prompts for a 2FA code during login, the agent reads `FIVERR_2FA_SECRET` from `.env` to generate the code.

1. Log in to your Fiverr account in a browser.
2. Go to **Account Settings** → **Security** → **Two-Factor Authentication**.
3. Enable 2FA using an authenticator app (e.g., Google Authenticator, Authy, 1Password).
4. Fiverr will display a QR code and/or a secret key. Copy the **secret key** (a base32 string such as `JBSWY3DPEHPK3PXP`).
5. Paste the secret key into `FIVERR_2FA_SECRET` in your `.env` file:
   ```
   FIVERR_2FA_SECRET=JBSWY3DPEHPK3PXP
   ```
6. Restart the agent so it picks up the new value.

> **Tip:** If you scan the QR code with your authenticator app, the app will reveal the underlying secret key you can copy into `.env`.

## Proxy Sources

Set `PROXY_API_URLS` in `.env` to a comma-separated list of proxy list API URLs. The agent fetches proxies from these URLs, validates them (example.com check), and rotates them round-robin for browser automation.

Example (already in `.env.example`):
```
PROXY_API_URLS=https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=3000&country=all
```

Free proxy list sources you can add (comma-separated):

- https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=3000&country=all
- https://www.proxy-list.download/api/v1/get?type=http
- https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt
- https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt

> **Note:** Free proxies are often unreliable and short-lived. Validate proxies from the dashboard before use, and consider residential or paid proxies for stable Fiverr automation. Rotate proxies responsibly to respect Fiverr's rate limits.

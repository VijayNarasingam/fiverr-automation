# Fiverr Automation Agent

A local-first automation agent for managing Fiverr gigs, orders, and messages, with a FastAPI backend, a React dashboard, Ollama for local LLM generation, and Google Sheets integration.

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

3. Start Ollama (required for the local LLM):

```bash
# With Docker Compose (ollama service is included):
docker compose up -d ollama

# Or install Ollama locally and run `ollama serve` + pull a model:
# ollama pull llama3
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
| `OLLAMA_BASE_URL` | Ollama API base URL | No | http://localhost:11434/v1 |
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
| `ollama` | 11434 | Local LLM server |
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

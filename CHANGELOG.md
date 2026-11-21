# Changelog

## 0.1.0 - 2026-11-21

Initial release of the Fiverr Automation Agent — a local-first automation agent for managing Fiverr gigs, orders, and messages.

### Core platform
- FastAPI backend with async SQLAlchemy (SQLite/PostgreSQL) and Alembic database migrations
- React dashboard served via nginx, with Vite dev server for local development
- Ollama integration for local LLM content generation (OpenAI-compatible `/chat/completions`)
- Docker Compose deployment (app, redis, ollama, frontend services)
- Pydantic Settings configuration via `.env` (Fiverr credentials, Google Sheets, Ollama, DB, Redis, notifications, proxies, rate limits)
- Application secret key (`SECRET_KEY`) for session/security signing

### Database models
- `Gig` model with status (pending/published/failed), packages (basic/standard/premium), price/days/revisions, features, tags, FAQs, images, gig ID/URL, error message
- `Order` model with buyer, amount, status, deadline, sync tracking
- `Message` model for inbound/outbound message history and auto-reply tracking
- `AuditLog` model for audit trail of automation actions
- `Session` model for persistent Fiverr login session cookies

### Google Sheets integration
- `SheetsService` using a Google service account to read gig rows and update gig status (status, gig ID, gig URL, error message)
- Column mapping: Status (S), Gig ID (T), Gig URL (U), Error (V)
- `scripts/seed_sheets.py` to seed the sheet header and sample gig rows

### Gig publishing (browser automation)
- `BrowserService` with Playwright, stealth mode, persistent browser context, session save/load
- `StealthManager` to reduce automation detection
- `GigPublisher` automates Fiverr login (email + password + optional 2FA TOTP), navigates to the gig creation form, and fills out title, category, description, packages, tags, FAQs, and images
- Content enhancement via `ContentEngine` (Jinja2 templates + Ollama LLM fallback to template-only output)
- Gig templates: `gig_description.j2`, `gig_faq.j2`
- Result persisted to database and Google Sheets; success/failure status tracked

### Order management
- `OrderManager` to sync orders from Fiverr and update order status
- Order models with `OrderStatus` (pending, active, delivered, completed, cancelled)

### Message handling
- `MessageHandler` with rule-based auto-replies (requirements, deadline, revision keywords)
- Spam keyword filtering (click here, win money, free bitcoin)
- Ollama LLM fallback for AI-generated replies

### Orchestration & scheduling
- `Orchestrator` coordinating gig creation cycle, order sync cycle, and message cycle
- Rate limiting: `MAX_GIGS_PER_RUN` and delay between gigs to respect Fiverr rate limits
- `Scheduler` for automated recurring cycles

### Proxies
- `ProxyManager` to fetch proxies from `PROXY_API_URLS`, validate them (example.com check), and rotate round-robin
- Proxy API and validation endpoints in the dashboard

### Notifications
- `NotificationService` supporting Discord webhook, Slack webhook, and SMTP email notifications

### Analytics
- `AnalyticsService` computing overview stats (total/published gigs, total/completed orders, revenue), gig performance, and A/B test analysis

### API
- REST routers: health, gigs, orders, messages, analytics, settings, logs, SSE (server-sent events), proxies
- Interactive API docs at `/docs`
- SSE endpoint for real-time dashboard updates

### Compliance
- Intended for personal productivity/account management on your own Fiverr account only
- Reminders to respect Fiverr's Terms of Service and rate limits, never commit `.env` or service account keys, and review AI-generated content before publishing

### Testing
- Test suite with `pytest`: API, models, gig publisher, message handler, order manager, proxy manager, proxy validation, sheets, analytics, notifications, ollama, orchestrator, and end-to-end gig/order flow tests
- Playwright browsers required for browser automation tests

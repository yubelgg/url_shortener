# URL Shortener — Production Engineering Hackathon

API-first URL shortener built on the MLH PE stack. Team submission for **Reliability Engineering**: tests in CI, health checks, structured JSON errors, Docker restart policy, and documented failure modes.

**Stack:** Flask · Peewee ORM · PostgreSQL · uv · Gunicorn · Docker · GitHub Actions

## Reliability (quest highlights)

- **pytest** integration tests under `tests/` hitting the HTTP API  
- **GitHub Actions** runs tests + Postgres on every push/PR to `main`  
- **`GET /health`** — always JSON; includes DB check (`ok` / `degraded`)  
- **pytest-cov** on `app` with **`--cov-fail-under=70`** in CI  
- **Graceful errors** — 4xx/5xx return JSON (see `app/errors.py`)  
- **Docker Compose** — `restart: always` on `app` and `db` for chaos-style demos  
- **Failure modes** — [FAILURE_MODES.md](FAILURE_MODES.md)  
- **API manual tests** — [TESTING.md](TESTING.md)

## Quick start (local)

```bash
git clone https://github.com/yubelgg/url_shortener.git && cd url_shortener
uv sync
createdb hackathon_db   # or your Postgres admin tool
cp .env.example .env    # match your DB user/password/name
uv run python seed.py   # optional: load CSV seed data
uv run run.py
```

Dev server uses **port 5001**:

```bash
curl -s http://localhost:5001/health
```

## Docker Compose

```bash
cp .env.example .env   # DATABASE_* must match between db and app
docker compose up --build
```

App on **http://localhost:5001** (host) → container **8080**. Postgres is reachable inside Compose as host **`db`**.

## Live deployment (DigitalOcean)

**Base URL:** [https://urlshortener-rp6zs.ondigitalocean.app](https://urlshortener-rp6zs.ondigitalocean.app)

The app is wired for **continuous deployment**: new commits pushed to the connected branch (typically **`main`**) trigger an automatic redeploy on DigitalOcean App Platform.

Quick checks (use **`https`**):

```bash
curl -sS "https://urlshortener-rp6zs.ondigitalocean.app/health"
```

Keep **local** URLs (`localhost:5001`, Docker Compose) for development; use the **deployed URL** above for demos and judges hitting production.

## Tests & coverage

```bash
uv sync --group dev
uv run pytest tests/ -v
uv run pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=70
```

## API overview

| Area | Routes |
|------|--------|
| Health | `GET /health` |
| Users | `GET/POST /users`, `GET/PUT /users/:id`, `POST /users/bulk` |
| URLs | `GET/POST /urls`, `GET/PUT /urls/:id` (inactive URLs hidden from public `GET`) |
| Redirect | `GET /r/:short_code` → 302 + `clicked` event |
| Events | `GET /events` |
| Seed (ops) | `GET /seed` — loads CSVs (protect/remove in real production) |

Full `curl` examples: [TESTING.md](TESTING.md).

## MLH platform & seed data

Use the seed CSVs and platform guidance from [MLH PE Hackathon](https://mlh-pe-hackathon.com) for judging and schema expectations.

## Project layout

```
app/
  __init__.py       # app factory, /health, /seed
  database.py       # Peewee + connection lifecycle
  errors.py         # JSON error handlers
  health.py         # health check logic
  models/           # User, Url, Event
  routes/           # users, urls, events, redirect
tests/              # pytest API + error coverage
.github/workflows/ # CI
```

## License / template

Generated from the MLH PE Hackathon template; extended for reliability and URL-shortener behavior.

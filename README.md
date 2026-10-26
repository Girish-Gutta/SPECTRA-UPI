# SPECTRA-UPI

**A free, open-source community lookup for UPI scam identifiers.**

SPECTRA-UPI lets anyone check a UPI ID, payment link, phone number or UPI QR
payload against community reports — without an account, an API key or a paid
service. It began as an ML-based transaction risk analyzer and now includes a
public scam lookup, anonymous reporting, moderation, disputes, a developer API
and a browser-only QR scanner.

> **No report found does not guarantee safety. Verify before paying.**
> A report is one person's allegation, not a court finding. Always confirm the
> payee and use official channels before sending money.

---

## The three outcomes

The public lookup never says "SAFE". There are exactly three verdicts:

| Verdict | Meaning | What produces it |
| --- | --- | --- |
| **HIGH RISK / REPORTED** | Moderator-verified community reports exist. | At least one `verified` report. |
| **SUSPICIOUS** | Something warrants caution, but nothing is verified. | Pending reports, URL/keyword heuristics, optional link-reputation signals, or the transaction model. |
| **NO REPORTS FOUND** | Nothing matches in the community database. | No reports and no risk signal. **Still not proof of safety.** |

Only `verified` reports can produce HIGH RISK. `pending` reports contribute at
most SUSPICIOUS and are never published as fact. Rejected reports contribute
nothing.

---

## Features

- Public lookup for UPI IDs, URLs, phone numbers and UPI QR payloads.
- Anonymous reports and listing disputes with optional Cloudflare Turnstile.
- Moderator queue with verify/reject actions, moderation log and automatic
  entity recalculation.
- Three-outcome verdicts with template-based explanations (no LLM calls).
- Scam-type catalogue, relevant law references, helplines and prevention steps.
- Browser-only QR scanning via `jsqr`; **no image ever leaves the browser**.
- Optional link reputation checks (Safe Browsing, VirusTotal, OpenPhish,
  PhishTank) with a 24-hour database cache. The core works with none of them.
- Personal developer API keys with hashed storage and a rate-limited
  `GET /api/v1/lookup`.
- Existing JWT transaction analyzer, history, statistics and CSV export remain
  available to signed-in users.
- SQLite by default, PostgreSQL via `DATABASE_URL`; additive migrations only.
- Docker Compose, GitHub Actions CI and no paid dependencies required.

---

## Repository structure

```text
SPECTRA-UPI/
├── backend/
│   ├── api/                 # FastAPI routers (auth, transactions, public, admin, keys, dev)
│   ├── db/                  # SQLAlchemy models, engine, idempotent seed data
│   ├── services/            # normalize, verdict, explain, lookup, linkcheck, captcha, security
│   ├── alembic/             # Additive schema migration (0001_public_lookup)
│   ├── data/                # Scam-type catalogue, laws, helplines, demo seeds
│   ├── ml/                  # Dataset generation and model training scripts
│   ├── models/              # Model artifacts + pure-NumPy scaler JSON
│   ├── scripts/             # create_admin.py and maintenance helpers
│   └── tests/               # pytest suite (API, verdict, normalization, moderation)
├── frontend/
│   └── src/
│       ├── pages/           # Landing, LookupResult, Report, Dispute, Admin, API keys, app pages
│       ├── components/      # Layout, PublicLayout, LookupBadge, QrScanner, TurnstileWidget
│       ├── context/         # AuthContext
│       └── lib/api.js       # API clients
├── docs/                    # Data policy, demo checklist, legacy frontend snapshots
├── docker-compose.yml
├── LICENSE                  # MIT
└── README.md
```

---

## Quick start (local, no API keys)

**Prerequisites:** Python 3.10+ (3.11 or 3.12 recommended), Node.js 18+ (20
recommended), npm.

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

uvicorn api.main:app --reload --port 8000
```

Startup creates missing tables and seeds the scam catalogue, laws, helplines and
clearly-labelled demo rows. Open <http://localhost:8000/docs> for the API docs.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
npm run dev
```

Open <http://localhost:5173>. The Vite dev server proxies `/api` to the backend.

On Windows you can also run `start-dev.bat`.

### 3. Try it

Search one of the seeded demo identifiers:

| Value | Outcome | Why |
| --- | --- | --- |
| `demo.kyc-alert@exampleupi` | HIGH RISK / REPORTED | Demo reports, verified |
| `demo.collect@exampleupi` | SUSPICIOUS | Demo report, pending only |
| `https://demo-scam.example/kyc-verify` | HIGH RISK / REPORTED | Demo URL report |
| `upi://pay?pa=demo.qr@exampleupi&pn=Demo%20Store` | NO REPORTS FOUND | Entity exists, no reports |

Demo rows always carry `[DEMO DATA]` in the description and set
`demo_data: true` in the API response. Disable them with
`DEMO_DATA_ENABLED=false`.

---

## Configuration

Copy `backend/.env.example` to `backend/.env`. Everything below is optional for
local use; the core lookup works with defaults and no external accounts.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | dev value | JWT signing key. Change in production. |
| `DATABASE_URL` | `sqlite:///…/spectra_upi.db` | SQLite or PostgreSQL URL. |
| `CORS_ORIGINS` | localhost origins | Comma-separated allowed browser origins. |
| `REPORTER_HASH_SALT` | dev value | Salt for reporter hashes. Change in production. |
| `TRUST_PROXY_HEADERS` | `false` | Trust `X-Forwarded-For` only behind a known proxy. |
| `DEMO_DATA_ENABLED` | `true` | Seed/label demo entities. |
| `RATE_LIMIT_ENABLED` | `true` | slowapi in-memory rate limiting. |
| `LOOKUP_RATE_LIMIT` | `60/minute` | Public lookup limit per IP. |
| `REPORT_RATE_LIMIT` | `5/hour` | Report submissions per reporter hash. |
| `DISPUTE_RATE_LIMIT` | `3/hour` | Dispute submissions per reporter hash. |
| `API_KEY_RATE_LIMIT` | `60/minute` | Developer lookup limit per key. |
| `CAPTCHA_DISABLED` | `false` | Explicitly skip Turnstile. |
| `TURNSTILE_SECRET_KEY` | empty | If set, CAPTCHA fails closed without a token. |
| `EXTERNAL_CHECKS_ENABLED` | `true` | Master switch for optional link checks. |
| `GOOGLE_SAFE_BROWSING_KEY` | empty | Optional Safe Browsing lookup. |
| `VIRUSTOTAL_API_KEY` | empty | Optional VirusTotal lookup. |
| `OPENPHISH_FEED_URL` | empty | Optional OpenPhish feed URL. |
| `PHISHTANK_FEED_URL` | empty in code sample | Optional PhishTank CSV feed. |
| `EXTERNAL_CACHE_HOURS` | `24` | Cache window for external results. |

Frontend (`frontend/.env`):

| Variable | Purpose |
| --- | --- |
| `VITE_API_URL` | Backend root. Empty uses the dev/nginx proxy. |
| `VITE_TURNSTILE_SITE_KEY` | Cloudflare Turnstile site key. Empty hides the widget. |

### CAPTCHA pairing

`CAPTCHA_DISABLED` and `TURNSTILE_SECRET_KEY` on the backend must agree with
`VITE_TURNSTILE_SITE_KEY` on the frontend. If the server requires a token but the
widget is not configured, reports and disputes are rejected. If both sides are
empty/disabled, the service works fully offline.

---

## Roles and moderation

There is no default account and no default password.

```bash
cd backend
python -m scripts.create_admin --email you@example.com --name "Your Name" --phone 9876543210
```

The script prompts for a password (or reads `ADMIN_PASSWORD` for automation).
Use `--role moderator` to create a moderator. Existing users can be promoted by
re-running the script with the same email.

Roles:

| Role | Access |
| --- | --- |
| `user` | Transaction analysis, history, CSV export, API keys. |
| `moderator` | All user features plus the moderation queue and disputes. |
| `admin` | Same as moderator (reserved for broader administration). |

Moderation rules enforced by the API:

1. New reports are always `pending`.
2. Only a moderator/admin can verify or reject.
3. `verified` reports raise an entity to `reported` and can produce HIGH RISK.
4. Pending reports are counted but never published as fact; their descriptions,
   amounts and timeline entries are hidden from the public response.
5. Rejecting the last pending/verified report returns the entity to `clean`.
6. Every action writes a `moderation_logs` row.

---

## API overview

Base URL: `http://localhost:8000`

### Public (no login)

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/lookup?q=…&type=auto` | Three-outcome lookup. `type` is `auto`, `upi_id`, `url`, `qr_payload` or `phone`. Optional transaction fields add a model signal. |
| `POST` | `/api/reports` | Submit an anonymous report (`pending`). |
| `POST` | `/api/disputes` | Dispute a listing. |
| `GET` | `/api/awareness` | Scam patterns, laws, helplines and safety note. |
| `GET` | `/api/stats` | Aggregate counters only. Never identifiers. |

### Auth and transaction analyzer

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Create a user; returns a JWT. |
| `POST` | `/api/v1/auth/login` | Log in; returns a JWT. |
| `GET` | `/api/v1/auth/me` | Current profile (including role). |
| `POST` | `/api/v1/transactions/check` | Existing ML fraud check. |
| `GET` | `/api/v1/transactions` | Paginated history. |
| `GET` | `/api/v1/transactions/stats` | User statistics. |
| `DELETE` | `/api/v1/transactions/{id}` | Delete one of your records. |
| `GET` | `/api/v1/fraud-patterns` | Legacy knowledge-base endpoint. |

### Moderator/admin (JWT with `moderator` or `admin` role)

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/admin/reports?status=pending` | Queue (`pending`, `verified`, `rejected`, `all`). |
| `PATCH` | `/api/admin/reports/{id}` | `{"action": "verify" \| "reject", "note": "…"}`. |
| `GET` | `/api/admin/disputes?status=open` | Dispute list. |
| `PATCH` | `/api/admin/disputes/{id}` | `{"status": "open" \| "resolved"}`. |

### API keys and developer lookup

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/keys` | Create a key (returns the raw key once). |
| `GET` | `/api/keys` | List your keys (prefix only). |
| `DELETE` | `/api/keys/{id}` | Revoke a key. |
| `GET` | `/api/v1/lookup` | Same lookup, authenticated with `X-API-Key`. |

Example:

```bash
curl "http://localhost:8000/api/lookup?q=demo.kyc-alert@exampleupi"

curl "http://localhost:8000/api/v1/lookup?q=demo.kyc-alert@exampleupi" \
  -H "X-API-Key: spk_your_key_here"
```

---

## How a lookup is assembled

1. **Normalize** (`services/normalize.py`): detect the identifier type, lowercase
   handles, strip tracking parameters, resolve `upi://pay?pa=…` to the payee UPI
   ID and compute a salted value hash.
2. **Query** the entity and its reports by hash.
3. **Local signals** (`services/patterns.py`): suspicious TLDs, IP hosts, short
   links, lookalike keywords and similar heuristics.
4. **Optional link checks** (`services/linkcheck.py`): only when configured and
   only for URLs; cached for 24 hours.
5. **Verdict** (`services/verdict.py`): verified reports → HIGH RISK; pending
   reports or medium/high signals → SUSPICIOUS; otherwise NO REPORTS FOUND.
6. **Explain** (`services/explain.py`): deterministic templates for the
   incident summary, why-risky bullets, laws, helplines, prevention and
   paid/not-paid next steps. No LLM is called.
7. **Public response** (`services/lookup_service.py`): lists use masked values;
   the exact-match detail response includes the value the user searched for.

The existing transaction model is optional. It runs through the pure-NumPy
scaler path only and never imports sklearn/scipy into runtime inference.

---

## Privacy and data policy

- No login is required for lookup, QR scanning, awareness, reports or disputes.
- Anonymous reports store a **salted hash** of the request IP for duplicate
  protection. Raw IP addresses are never stored.
- Reporter contact email and evidence links are optional, visible only to
  moderators, and evidence links are **never fetched** by the server.
- Public list responses use masked identifiers. Aggregate stats never include
  identifiers.
- QR images and camera frames are decoded in the browser and never uploaded.
- There is no server-side OCR or image storage.
- Demo identifiers use reserved `.example` names and are labelled in the API
  (`demo_data: true`) and UI.

See [`docs/DATA_POLICY.md`](docs/DATA_POLICY.md) for retention, takedown and
moderation guidance.

---

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests -q
```

The suite covers normalization, masking, verdict rules, explanation templates,
public lookup, reporting, CAPTCHA failure, duplicate protection, disputes,
role checks, moderation effects, API keys, missing external keys and rate
limiting. Tests use a temporary SQLite database and run with CAPTCHA disabled.

Frontend verification:

```bash
cd frontend
npm ci
npm run build
```

---

## Docker

```bash
docker compose up --build
```

- Frontend: <http://localhost:8080>
- Backend: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>

The compose file uses SQLite in a named volume (`spectra-data`), disables
external link checks and CAPTCHA by default, and proxies `/api` through nginx.
For production, set a real `SECRET_KEY`, `REPORTER_HASH_SALT`, configure
Turnstile, and consider PostgreSQL:

```bash
DATABASE_URL=postgresql://user:password@host:5432/spectra_upi
```

### Migrations

Startup performs additive `create_all` + missing-column migrations and never
drops data. For explicit versioned migrations:

```bash
cd backend
alembic upgrade head
```

The baseline migration `0001_public_lookup` adds the public-lookup tables and
`users.role`. Its downgrade is intentionally a no-op: the project never drops
existing tables automatically.

---

## Deployment notes

- `render.yaml` contains a Render blueprint with a free PostgreSQL database.
  Set `SECRET_KEY`, `REPORTER_HASH_SALT`, `CAPTCHA_DISABLED=false` and the
  Turnstile keys in the dashboard.
- Set `VITE_API_URL` to the deployed backend origin when the frontend is hosted
  separately; otherwise use the nginx proxy.
- Set `CORS_ORIGINS` to your real frontend origin.
- Set `TRUST_PROXY_HEADERS=true` only if the app sits behind a trusted proxy
  (Render, Fly, nginx) that overwrites `X-Forwarded-For`.
- Rate limiting is in-memory per process. For multi-instance deployments, place
  a shared limiter or gateway in front.

---

## Optional integrations

All are free-tier friendly and optional:

| Integration | Requirement | Effect |
| --- | --- | --- |
| Cloudflare Turnstile | site + secret key | Adds CAPTCHA to reports/disputes. |
| Google Safe Browsing | API key | Adds a high-severity link signal. |
| VirusTotal | API key | Adds a link signal with throttling. |
| OpenPhish | feed URL | Checks the community feed. |
| PhishTank | CSV feed URL | Checks the community feed. |

When none are configured the lookup works fully offline.

---

## Safety, legal and limitations

SPECTRA-UPI is a **community reporting tool**, not a court, regulator, credit
bureau or fraud-prevention guarantee. Reports are user allegations. Identifiers
can be mistyped, impersonated or reported maliciously. Moderators review
reports, but no system is perfect.

- Never treat NO REPORTS FOUND as "safe".
- Never share a UPI PIN, OTP, card number or bank password.
- In India, report cyber fraud at <https://cybercrime.gov.in> or call **1930**.
- Victims should contact their bank immediately; early reporting improves the
  chance of a transaction hold.
- If you are wrongly listed, use the dispute form.

---

## Contributing

Contributions are welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) first. Security issues should follow
[`SECURITY.md`](SECURITY.md).

## License

MIT — see [`LICENSE`](LICENSE). Third-party components are listed in
[`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).

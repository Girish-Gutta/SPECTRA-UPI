# Contributing to SPECTRA-UPI

Thanks for helping make UPI payments safer. This project is free and
community-run, and every contribution — code, documentation, test cases,
translations or moderation guidance — is welcome.

## Before you start

- Read the [README](README.md), [data policy](docs/DATA_POLICY.md) and
  [code of conduct](CODE_OF_CONDUCT.md).
- Search existing issues before opening a new one.
- For security vulnerabilities, **do not open a public issue**. Follow
  [SECURITY.md](SECURITY.md).
- Never commit real personal data, real scam identifiers, API keys, `.env`
  files, database files or model artifacts that contain sensitive data.

## Development setup

### Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn api.main:app --reload --port 8000
```

Run the tests before opening a pull request:

```bash
python -m pytest tests -q
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
npm run build
```

The build must pass with no errors. Bundle-size warnings are acceptable; broken
routes, console errors and missing loading/empty states are not.

## What to work on

Good first contributions:

- Add test cases for normalization, verdict rules, moderation and rate limits.
- Improve accessibility, mobile layout and empty/error states.
- Improve scam-awareness copy, helplines and law references with cited sources.
- Add translations (keep the English fallback).
- Improve documentation and the demo checklist.

Please open an issue before large refactors or new data sources.

## Project rules

1. **Never say "SAFE".** The public API and UI have exactly three outcomes:
   `HIGH RISK / REPORTED`, `SUSPICIOUS` and `NO REPORTS FOUND`. NO_REPORTS must
   always be accompanied by the safety note.
2. **Only verified reports can raise HIGH RISK.** Pending reports are capped at
   SUSPICIOUS and their details stay out of public responses.
3. **Mask identifiers in lists.** Full values appear only on the exact-match
   detail response the user searched for.
4. **No raw IP storage.** Use the existing salted reporter hash helpers.
5. **No server-side image upload or OCR.** QR decoding stays in the browser.
6. **Never fetch evidence URLs.** Validate and store them for moderators only.
7. **No paid dependencies** and no feature that requires an account for core
   lookup, reporting or disputes.
8. **Keep inference on the pure-NumPy scaler path.** Do not add sklearn/scipy to
   the runtime inference path.
9. **Migrations must be additive** and work on SQLite and PostgreSQL. Never drop
   existing tables in an automatic startup path.
10. **Template explanations only.** Do not add an LLM dependency for public
    explanations.

## Code style

- Backend: type hints where practical, small service functions, descriptive
  names, no silent broad exceptions except at optional-integration boundaries.
- Frontend: function components and hooks, `async/await`, accessible labels on
  inputs and buttons, loading/error/empty states for every network call.
- Keep the existing warm stone/emerald visual language (`bg-gray-950`, `.card`,
  `.btn-primary`, `.input`).
- Prefer plain, direct copy over jargon. Explain acronyms on first use.

## Database changes

- Update the SQLAlchemy models.
- Add an Alembic revision for the change. The baseline is
  `backend/alembic/versions/0001_public_lookup.py`.
- Keep `create_all` + missing-column startup migrations working for existing
  SQLite databases.
- Do not edit or delete a released migration that users may already have run.
- Test on a fresh SQLite file **and** on an existing database.

## Tests

A pull request that changes behavior should include tests. Useful patterns:

- Use the `client` and `db_session` fixtures in `backend/tests/conftest.py`.
- Tests run against a temporary SQLite database with rate limiting disabled and
  CAPTCHA disabled.
- Mock external services. Tests must not make real network calls.
- Cover failure paths: invalid input, duplicate reports, CAPTCHA failure,
  missing API keys, role denial and rejected moderation actions.

## Pull requests

- Keep the scope focused and describe the user-facing change.
- List changed files and the test steps you ran.
- Link the related issue.
- Include screenshots for UI changes when possible.
- Do not mix formatting-only rewrites with behavior changes.

## Commit messages

Use a short imperative subject, optionally with a scope:

```text
api: reject reports with unsafe evidence links
frontend: add QR scanner fallback for denied camera permission
docs: document Turnstile pairing
```

## Reporting data problems

If an identifier is wrongly listed, use the in-app dispute flow. Do not open a
public issue containing the full identifier, personal details or screenshots of
private chats. Moderators can handle those through the dispute process.

## License

By contributing, you agree that your contribution is licensed under the
project's [MIT License](LICENSE).

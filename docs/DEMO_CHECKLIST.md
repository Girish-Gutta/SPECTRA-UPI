# Manual demo checklist

A 10–15 minute walkthrough of every public feature. Run it after a fresh clone,
before a release, or when recording a demo.

Use fictional `.example` identifiers only. Demo rows are seeded automatically
unless `DEMO_DATA_ENABLED=false`.

---

## 0. Setup

- [ ] Backend running: `cd backend && uvicorn api.main:app --reload --port 8000`
- [ ] API docs load at <http://localhost:8000/docs>
- [ ] Frontend running: `cd frontend && npm run dev` → <http://localhost:5173>
- [ ] `GET http://localhost:8000/health` returns `{"status":"ok"}`
- [ ] `GET http://localhost:8000/api/stats` returns counters and no identifiers
- [ ] Create an admin/moderator:
      `cd backend && python -m scripts.create_admin --email admin@example.com --name "Demo Admin" --phone 9876543210 --role admin`
- [ ] Sign in as that account and confirm the **Moderation** item appears.

---

## 1. Public home and stats

- [ ] Home page loads without login.
- [ ] Stats cards show seeded counts (or `—` briefly while loading).
- [ ] Search box accepts a UPI ID, URL, phone number or QR payload.
- [ ] The QR button opens the scanner modal.
- [ ] Footer shows the safety note, helpline 1930 and cybercrime.gov.in.
- [ ] Demo chips populate and run a lookup.

---

## 2. The three verdicts

- [ ] Search `demo.kyc-alert@exampleupi`
      → **HIGH RISK / REPORTED**, verified count > 0, "demo data" banner present.
- [ ] Search `demo.collect@exampleupi`
      → **SUSPICIOUS**, verified count 0, pending count > 0, no pending details.
- [ ] Search `demo.qr@exampleupi`
      → **NO REPORTS FOUND**, safety note visible.
- [ ] Search `https://demo-scam.example/kyc-verify`
      → **HIGH RISK / REPORTED** (URL entity).
- [ ] Search `https://totally-new.example/pay`
      → **NO REPORTS FOUND** (or SUSPICIOUS only if a local signal fires).
- [ ] Search `not a upi id` or an empty/1-character value
      → friendly validation error, not a crash.
- [ ] Confirm the word "SAFE" never appears as a verdict.
- [ ] Copy the identifier from the detail card.
- [ ] Switch the type selector; results remain consistent for a valid UPI ID.

---

## 3. Lookup detail content

- [ ] Verdict badge, detected type, identifier and public mask are shown.
- [ ] Safety note appears on every verdict, including NO REPORTS FOUND.
- [ ] Verified/pending/total/loss counters match the reports.
- [ ] Signals render with severity colour and source.
- [ ] Explanation, prevention steps, laws and helplines are present.
- [ ] Verified timeline shows dates and amounts; no pending rows.
- [ ] "Report" and "Dispute" buttons carry the identifier into the forms.
- [ ] A bad network or stopped backend shows a readable error state.

---

## 4. QR scanner (browser only)

- [ ] Allow camera access; a live preview appears.
- [ ] Point the camera at a QR code and confirm it runs a lookup.
- [ ] Deny camera permission; the upload fallback remains usable.
- [ ] Upload a QR image and confirm it decodes.
- [ ] Upload a non-QR image; a toast explains that no code was found.
- [ ] Open DevTools → Network and confirm **no image upload** request occurs.
- [ ] Close the modal; the camera light turns off.

Test payload (fictional):
`upi://pay?pa=demo.qr@exampleupi&pn=Demo%20Store`

---

## 5. Anonymous report → moderation → verdict change

Use a new fictional identifier such as `demo.check.<timestamp>@exampleupi`.

- [ ] Open `/report` from the public nav.
- [ ] Submit with a missing scam type / short description → validation message.
- [ ] Submit a valid report.
- [ ] A success card shows `#REP-<id>`, `pending`, and the masked value.
- [ ] Look up the identifier → **SUSPICIOUS**, verified 0, pending 1.
- [ ] Confirm the pending description, amount and timeline are not public.
- [ ] Submit the same report again within 24 hours → duplicate warning.
- [ ] Sign in as moderator → **Moderation → Reports → Pending**.
- [ ] The report shows priority if it had an evidence link or account link.
- [ ] Open the full identifier and description; contact/evidence fields are
      moderator-only.
- [ ] Verify the report with a note.
- [ ] Look up the identifier again → **HIGH RISK / REPORTED**, timeline visible.
- [ ] Reject a different pending report → lookup returns to SUSPICIOUS or
      NO REPORTS FOUND.
- [ ] Confirm a moderation log row exists (optional DB check).

---

## 6. Dispute flow

- [ ] Open `/dispute` without logging in.
- [ ] Submit a reason shorter than 20 characters → validation message.
- [ ] Submit a valid dispute for a listed identifier.
- [ ] Success card shows `#DIS-<id>` and `open`.
- [ ] Try to open more than two open disputes for the same identifier →
      conflict message.
- [ ] As moderator, open **Moderation → Disputes**, read the reason and contact
      email, and mark it resolved.
- [ ] Reopen and re-resolve (if desired).
- [ ] Confirm disputes do not automatically delete verified reports.

---

## 7. Access control

- [ ] `/admin` while signed out → redirected to login.
- [ ] `/admin` as a normal `user` → redirected to the dashboard.
- [ ] `/admin` as moderator/admin → queue loads.
- [ ] `GET /api/admin/reports` with no token → 401/403.
- [ ] `GET /api/admin/reports` as a normal user → 403.
- [ ] `/developer` while signed out → login.
- [ ] Account sign-out clears the session and public pages still work.

---

## 8. Developer API keys

- [ ] Sign in, open **API keys**.
- [ ] Create a key; the raw key is shown once.
- [ ] Copy it; the list afterwards shows only `spk_…`/prefix metadata.
- [ ] Call the developer endpoint:

      curl "http://localhost:8000/api/v1/lookup?q=demo.kyc-alert@exampleupi" \
        -H "X-API-Key: spk_..."

- [ ] Without the header → 401.
- [ ] Revoke the key and repeat → 401.
- [ ] Confirm keys are stored hashed in the database.
- [ ] Confirm the API never returns the raw key in list responses.

---

## 9. Awareness and public content

- [ ] `/awareness` loads without login.
- [ ] All 8 scam patterns expand/collapse.
- [ ] Helplines include 1930, and cybercrime.gov.in opens.
- [ ] Laws render.
- [ ] Golden rules are readable on mobile.
- [ ] `/api/awareness` and `/api/stats` return data with no login.

---

## 10. Existing transaction features

- [ ] Register/sign in.
- [ ] Run a transaction check in **Fraud Check**.
- [ ] History shows the record; filters and CSV export work.
- [ ] Dashboard charts render.
- [ ] Profile loads.
- [ ] A wrong password is rejected cleanly.

---

## 11. Optional integrations and offline mode

- [ ] With no Safe Browsing/VirusTotal/OpenPhish/PhishTank keys, URL lookup
      still returns a verdict and does not error.
- [ ] With `EXTERNAL_CHECKS_ENABLED=false`, lookup skips external calls.
- [ ] External results are cached for the configured window (check
      `external_check_cache`).
- [ ] With Turnstile keys configured on both sides, the widget renders and a
      report requires a successful challenge.
- [ ] With the widget missing but the secret configured, submission fails
      closed with a clear CAPTCHA message.
- [ ] With `CAPTCHA_DISABLED=true` and no site key, submission works offline.

---

## 12. Mobile and accessibility

- [ ] Public navigation collapses into a working menu.
- [ ] Forms are usable at 375 px width; no horizontal scroll.
- [ ] Focus rings are visible on inputs and buttons.
- [ ] Inputs have labels; icons have accessible names.
- [ ] The verdict is not conveyed by colour alone (text label present).
- [ ] Loading, empty and error states are readable.

---

## 13. Build, tests and deployment

- [ ] `cd backend && python -m pytest tests -q` passes.
- [ ] `cd frontend && npm run build` succeeds.
- [ ] `docker compose up --build` serves the app at <http://localhost:8080>.
- [ ] `/api` requests through nginx reach the backend.
- [ ] Restarting the backend keeps SQLite data (volume mounted).
- [ ] `GET /api/...` responses include `X-Content-Type-Options: nosniff` and
      `Cache-Control: no-store`.
- [ ] A production deploy sets real `SECRET_KEY` and `REPORTER_HASH_SALT`.

---

## Demo script (short version)

1. Home → search `demo.kyc-alert@exampleupi` → HIGH RISK, safety note.
2. Search `demo.collect@exampleupi` → SUSPICIOUS, pending only.
3. Search a new identifier → NO REPORTS FOUND, explain why that is not "safe".
4. Scan/upload a QR → lookup.
5. Report a new fake identifier → SUSPICIOUS.
6. Sign in as moderator → verify it → HIGH RISK.
7. Open a dispute → moderator resolves it.
8. Show API key creation and one `curl` lookup.
9. Show `/awareness` and helpline 1930.

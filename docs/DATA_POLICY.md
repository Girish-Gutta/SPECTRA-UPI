# Data policy

**Last updated: 26 October 2026**

SPECTRA-UPI is a community scam-lookup service. This document explains what the
reference implementation collects, why, how it is exposed, and the retention and
takedown practices deployments should follow.

This is an engineering and transparency document, not legal advice. Operators
who deploy SPECTRA-UPI are responsible for complying with applicable law in their
jurisdiction, including data-protection and intermediary rules.

---

## 1. Principles

1. **No login for safety checks.** Lookup, QR scanning, awareness content,
   reports and disputes work without an account.
2. **Collect the minimum.** We do not ask for bank credentials, card numbers,
   OTPs, PINs, government IDs or identity documents.
3. **Never store raw IP addresses.** A salted hash is used only to stop
   duplicate reports and abuse.
4. **Mask public lists.** Full identifiers appear only in the exact-match
   response to the person who searched for them.
5. **Publish allegations carefully.** Only moderator-verified reports can raise
   an identifier to HIGH RISK. Pending reports are capped at SUSPICIOUS and
   their details are not published.
6. **No server-side images.** QR images and camera frames are decoded in the
   browser and never uploaded or stored.
7. **No evidence fetching.** Evidence links are stored for moderators and are
   never requested by the server, which prevents SSRF and accidental data
   leakage.

---

## 2. What is collected

### 2.1 Public lookup

| Data | Stored? | Purpose |
| --- | --- | --- |
| The identifier you type or scan | No, except as a hash used to find an existing entity | Return the verdict. |
| Request IP | No raw IP. In-memory rate-limit counters only. | Abuse prevention. |
| Transaction fields (optional) | No | Add a model signal when amount and platform are supplied. |
| Link-reputation results | A hash of the URL plus the provider result, cached for up to `EXTERNAL_CACHE_HOURS` (default 24 hours) | Avoid repeated paid/free-tier API calls. |

### 2.2 Reports

| Data | Required? | Public? |
| --- | --- | --- |
| Identifier (UPI ID, URL, phone, QR payload) | Yes | Masked in lists; full value in the exact-match detail view if the listing is public. |
| Scam type | Yes | Yes, once verified. |
| Description | Yes (10–2000 chars) | Verified reports may contribute to the incident summary and timeline. Pending details are not published. |
| Amount lost | Optional | Aggregated for verified reports. |
| Incident date | Optional | Timeline month/day for verified reports. |
| Evidence URL | Optional | Moderators only. Never fetched or rendered publicly. |
| Contact email | Optional | Moderators only. No automated email is sent. |
| Reporter hash | Generated | Used for 24-hour duplicate protection. Never exposed. |
| Account link | If signed in | Used to attribute the report to your account; not shown publicly. |
| Timestamps and status | Generated | Used for moderation and the verified timeline. |

Reports are **allegations**. A report does not establish that a named person
committed a crime.

### 2.3 Disputes

| Data | Required? | Public? |
| --- | --- | --- |
| Identifier | Yes | Masked in moderator lists. |
| Reason | Yes (20–2000 chars) | Moderators only. |
| Contact email | Recommended | Moderators only. |
| Status and timestamps | Generated | Moderators only. |

### 2.4 Accounts (optional)

Name, email, phone number, bcrypt password hash, role, account status and the
transaction records you choose to create. Passwords are never stored in plain
text. JWTs are signed with the server `SECRET_KEY`.

### 2.5 Developer API keys

Key name, creation/revocation timestamps and a SHA-256 hash of the key. The raw
key is shown once at creation and is not recoverable. Requests made with a key
are rate-limited by a hash of the key.

### 2.6 Demo data

Seeded demo entities use fictional handles and the reserved `.example` namespace.
Descriptions start with `[DEMO DATA]`, and responses include `demo_data: true`.
Demo data is not a statement about any real person or business. Disable it with
`DEMO_DATA_ENABLED=false`.

---

## 3. What is never collected

- UPI PINs, OTPs, passwords, card numbers or CVVs.
- Bank statements, identity documents or selfies.
- Raw IP addresses.
- Precise location or device fingerprints.
- Uploaded QR images or camera frames.
- Contents of evidence links (the server does not fetch them).
- Contact lists, SMS or notification contents.

Please do not include any of these in a report, dispute or issue. Moderators may
remove content that contains them.

---

## 4. Public exposure

The public API returns:

- The verdict, risk level and template explanation.
- Masked identifiers in list/aggregate contexts.
- The identifier the requester supplied in the exact-match response.
- Verified report counts, aggregate reported loss, scam types, laws and
  helplines.
- Aggregate counters on `/api/stats` with no identifiers.

It does **not** return:

- Pending or rejected report descriptions, amounts or timelines.
- Reporter hashes, IP hashes, contact emails or evidence URLs.
- User account details.
- Raw external-provider responses.

Moderators can see full identifiers, descriptions, optional contact emails and
evidence links because they need them to assess reports.

---

## 5. Retention (recommended)

The reference implementation does not run an automatic deletion job. Operators
should schedule one and document any differences.

| Data | Recommended retention |
| --- | --- |
| Lookup queries | Not persisted. |
| External check cache | `EXTERNAL_CACHE_HOURS`, default 24 hours. |
| Pending reports | Review within 90 days; delete or reject stale reports after 180 days. |
| Verified reports | Retain while the listing is active; review at least annually. |
| Rejected reports | Delete or anonymise after 12 months. |
| Open disputes | Resolve within 90 days. |
| Resolved disputes | Delete or anonymise after 24 months. |
| Moderation logs | Retain for accountability; minimise reviewer notes where possible. |
| Account data | Until account deletion, plus a short legal/audit window. |
| API keys | Until revoked; delete metadata after 12 months of inactivity. |
| Server/access logs | 30 days or less, with IPs truncated or hashed. |

Deletion means removing the row or irreversibly anonymising identifiers while
keeping aggregate counts if needed for integrity.

---

## 6. Disputes and takedown

1. Anyone can submit a dispute without an account.
2. A moderator reviews the dispute with the original reports.
3. The moderator may request proof of ownership, resolve the dispute, or leave
   the listing in place.
4. A resolved dispute does not automatically delete verified reports; deleting
   evidence of repeated fraud could put others at risk.
5. If a listing is clearly mistaken, the underlying reports should be rejected
   or removed by an administrator, and the entity recalculated.
6. For urgent safety or legal requests, contact the deployment's maintainers
   through the repository's private channel. Do not post full identifiers or
   personal data in a public issue.

Operators should publish a contact route and response target for legal requests.

---

## 7. External services

All external integrations are optional. If enabled, the following data may leave
the server:

| Service | Data sent | When |
| --- | --- | --- |
| Cloudflare Turnstile | CAPTCHA token and, if supplied, the client IP | On report/dispute submission. |
| Google Safe Browsing | The URL being checked | On URL lookup, if configured. |
| VirusTotal | The URL being checked | On URL lookup, if configured and within quota. |
| OpenPhish / PhishTank | A request for their public feed | Periodically, if configured. |

No report descriptions, contact emails or account data are sent to these
services. Self-hosters can disable all of them with
`EXTERNAL_CHECKS_ENABLED=false`.

---

## 8. Security

- Salted reporter hashes, not raw IPs.
- API keys and passwords stored as hashes.
- JWT-authenticated moderation with role checks.
- Rate limiting on lookup, reports, disputes and API keys.
- Security headers on API responses.
- Evidence URLs restricted to http(s) and never fetched.
- Browser-only QR decoding.
- Additive database migrations; no automatic table drops.

Report vulnerabilities privately as described in [SECURITY.md](../SECURITY.md).

---

## 9. Children

The service is intended for adults handling their own payments. It is not
directed at children. Do not submit a child's personal data. If such data is
discovered, moderators should remove it promptly.

---

## 10. Changes

Material changes to this policy should be recorded in the repository history and,
where practical, announced in the README or release notes. Deployments that
modify retention or add integrations should update this document.

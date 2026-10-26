# Security policy

## Supported versions

Security fixes are applied to the latest `main` branch. Older snapshots are not
maintained.

## Reporting a vulnerability

**Please do not open a public issue for a security vulnerability.**

Report privately using **GitHub Security Advisories** on this repository
(Security → Advisories → New draft advisory). If that is unavailable, contact a
maintainer privately through their GitHub profile.

Include:

- A description of the issue and its impact.
- Steps to reproduce, ideally with a minimal request or payload.
- The affected endpoint, version or commit.
- Whether any personal data, report data or moderation capability is exposed.
- Any suggested mitigation.

We aim to acknowledge reports within 7 days and to provide a remediation plan
within 30 days. Please give us reasonable time to fix the issue before public
disclosure.

## Scope

In scope:

- Authentication or authorization bypass, including moderator/admin actions.
- Exposure of full identifiers, reporter hashes, contact emails or evidence URLs
  through public endpoints.
- SQL injection, SSRF, path traversal, stored XSS or template injection.
- CAPTCHA bypass that allows automated report/dispute spam.
- API key leakage or privilege escalation.
- Rate-limit bypass with meaningful impact.
- Unsafe handling of QR payloads or evidence links.
- Dependency vulnerabilities with a practical exploit path.

Out of scope:

- Self-XSS or issues requiring a compromised device.
- Missing security headers without a demonstrated impact.
- Denial of service through extreme traffic volumes.
- Reports that an identifier is listed; use the dispute flow.
- Social engineering of maintainers.
- Vulnerabilities in third-party services (report them upstream).

## Safe harbor

We will not pursue legal action or report researchers who:

- Act in good faith and avoid privacy violations, data destruction or service
  disruption.
- Only interact with accounts they own or test data they created.
- Stop testing and report promptly after discovering a vulnerability.
- Do not exfiltrate or publish personal data.

## Security design notes

- Public lists use masked identifiers; exact values are returned only to the
  requester who supplied them.
- Pending and rejected reports never contribute to HIGH RISK or public details.
- Reporter IP addresses are never stored; only a salted hash for duplicate
  protection.
- Evidence URLs are validated as http(s), stored for moderators and never
  fetched by the server.
- QR decoding happens entirely in the browser.
- API keys are stored as SHA-256 hashes and shown once at creation.
- JWTs are signed with `SECRET_KEY`; change the default in production.
- Set `TRUST_PROXY_HEADERS=true` only behind a trusted proxy that overwrites
  `X-Forwarded-For`.
- External link checks are optional, timeout-bounded and failure-tolerant.

## Dependency hygiene

Run `pip list --outdated` / `npm audit` periodically and update dependencies in
focused pull requests. Do not add a dependency that requires a paid account for
core functionality.

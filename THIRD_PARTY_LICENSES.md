# Third-party licenses

SPECTRA-UPI is MIT licensed. It depends on the following open-source projects.
The list is provided for attribution and convenience; consult each project for
the authoritative license text and version-specific terms.

## Backend (Python)

| Project | License | Use |
| --- | --- | --- |
| FastAPI | MIT | HTTP API framework |
| Uvicorn | BSD-3-Clause | ASGI server |
| SQLAlchemy | MIT | ORM and database toolkit |
| Alembic | MIT | Schema migrations |
| Pydantic / pydantic-settings | MIT | Validation and settings |
| slowapi | MIT | Rate limiting |
| python-jose | MIT | JWT handling |
| cryptography | Apache-2.0 or BSD-3-Clause | Crypto primitives |
| passlib | BSD-3-Clause | Password hashing |
| bcrypt | Apache-2.0 | Password hashing backend |
| python-multipart | Apache-2.0 | Form parsing |
| pandas | BSD-3-Clause | Data processing in training scripts |
| scikit-learn | BSD-3-Clause | Training/evaluation only |
| XGBoost | Apache-2.0 | Fraud model |
| imbalanced-learn | MIT | Training utilities |
| joblib | BSD-3-Clause | Model artifact loading |
| psycopg2-binary | LGPL-3.0-or-later with exceptions | PostgreSQL driver |
| pytest | MIT | Test runner (development) |
| httpx | BSD-3-Clause | Test client (development) |

## Frontend (JavaScript)

| Project | License | Use |
| --- | --- | --- |
| React / React DOM | MIT | UI runtime |
| React Router | MIT | Client-side routing |
| Axios | MIT | HTTP client |
| clsx | MIT | Conditional class names |
| lucide-react | ISC | Icons |
| react-hot-toast | MIT | Toast notifications |
| Recharts | MIT | Charts on existing dashboard pages |
| jsQR | Apache-2.0 | Browser QR decoding |
| Tailwind CSS | MIT | Styling |
| Vite | MIT | Build tool |
| @vitejs/plugin-react | MIT | React plugin |
| PostCSS | MIT | CSS processing |
| Autoprefixer | MIT | CSS vendor prefixes |

## Runtime and assets

| Project | License | Use |
| --- | --- | --- |
| Python | PSF-2.0 | Runtime |
| Node.js | MIT and third-party licenses | Build/runtime tooling |
| nginx | BSD-2-Clause | Production static server and reverse proxy |
| Inter font | SIL Open Font License 1.1 | UI typeface |
| Cloudflare Turnstile | Cloudflare terms | Optional CAPTCHA |
| Google Safe Browsing | Google API terms | Optional link reputation |
| VirusTotal | VirusTotal terms | Optional link reputation |
| OpenPhish | OpenPhish terms | Optional feed |
| PhishTank | PhishTank terms | Optional feed |

## Data

`backend/data/fraud_patterns.json` and the law/helpline reference data are
project-authored summaries based on public RBI/NPCI/cybercrime guidance. They are
not official legal texts. Demo entities are fictional and use reserved
`.example` names; they do not describe real people or businesses.

If you redistribute this project, keep this file, the MIT license and the
licenses of any bundled dependencies. Some transitive dependencies may carry
additional notices; run `pip-licenses` or `npm query` in your environment for a
complete inventory.

# HFpEF Hemodynamic Inpatient Agent

Experimental rule-based software for exploring synthetic inpatient-monitoring indicators. It includes a browser demonstration, Python command-line tools, and a FastAPI service.

**Not clinically validated. Not for diagnosis, treatment, triage, real patient monitoring, or use with protected health information (PHI).** The numeric metrics are unitless illustrations, not validated HFpEF clinical measurements or guideline thresholds. No actual clinician notification or diuretic recommendation is performed.

## Browser application

The static application in [web/](web/) runs entirely in modern browsers using JavaScript modules. It evaluates synthetic inputs without a server or Python runtime, shows deterministic rule results, and supports JSON export. It sends no form data over the network and uses no persistent browser storage.

Run locally over HTTP (ES modules may not load directly from `file://`):

```bash
python -m http.server 8080 --directory web
```

Open `http://localhost:8080`. A [GitHub Pages deployment workflow](.github/workflows/pages.yml) is included; availability of a public live site depends on GitHub Pages being enabled and a successful deployment.

The browser demonstrates the same generic rule triggers as the primary Python workers: primary metric **>25**, secondary metric **>12**, a manual critical flag, and a set of descriptor keywords. These cutoffs have **no claimed medical validity**. The browser does not implement the Python API, HMAC audit logging, or a PHI detector.

## Python installation

Requires Python **3.10+**.

```bash
git clone https://github.com/abusuraihsakhri/hfpef-hemodynamic-inpatient-agent.git
cd hfpef-hemodynamic-inpatient-agent
python -m pip install -e ".[api,test]"
```

The repository retains several original entry points. The documented primary CLI and API use the `agents/` package and `cli.py`. The `hfpef_hemodynamic_inpatient_agent/` package and `hfpef_sentinel.py` are separate legacy rule implementations with different data schemas and thresholds. Their outputs should not be assumed equivalent.

### Primary CLI

```bash
python cli.py audit --task-id SYN-001 --target SYN-TARGET-1 --primary 28.5 --secondary 14.2 --status DISCORDANT
python cli.py chat "show configuration"
python cli.py batch --input sample.csv --output results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

The batch importer accepts both `primary_metric`/`secondary_metric` and the supplied sample's `metric_primary`/`metric_secondary` column conventions. It also recognizes `case_id`, `patient_synthetic_id`, `status_flag`, and `is_stat`. Rows containing invalid values or recognized sensitive identifiers are skipped with a warning. Results are CSV files with an illustrative rule status and the per-process audit hash.

### FastAPI

Start the service with the `serve` command above. The primary app (`agents/api.py`) exposes:

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service health and demonstration scope |
| `POST /api/audit` | Evaluate a synthetic `SystemTaskPayload` |
| `POST /api/chat` | Deterministic mock response; no live language-model provider |
| `GET /api/audit/logs` | In-memory audit metadata and HMAC chain verification |
| `GET /metrics` | JSON counters for in-memory demonstration activity |

API documentation is available at `http://127.0.0.1:8000/docs`. The standalone `openapi_spec.json` is a reference snapshot; the running FastAPI app generates its own OpenAPI schema.

## Security and data handling

- Use **synthetic identifiers only**. The Python API includes best-effort regex and nested-field screening; this does **not** guarantee PHI detection, HIPAA compliance, or safe de-identification.
- Audit entries are HMAC-SHA256 signed and their signatures are reverified. An `AUDIT_SECRET_KEY` environment variable is **mandatory when `APP_ENV=production`**. Without it, non-production execution uses an ephemeral development key; verification does not survive process restart.
- Audit events and processed dossiers are stored **in process memory only**, not in durable storage. There is no authentication, authorization, access logging, rate limiting, retention control, or external secret-management system.
- The API should run on localhost for demonstration. Do not expose it as a patient-data service without a separate, documented security and clinical validation program.
- The LLM factory currently implements **only a deterministic mock adapter**. It does not call external model APIs.

## Tests and deployment

```bash
python -m pytest -v
node --test tests/browser_demo.test.mjs
python -m pip check
```

GitHub Actions tests Python 3.10–3.12, the package installation, and browser evaluation logic. The browser demonstration can be served by GitHub Pages without Pyodide because its small rule evaluator is implemented directly in JavaScript; the Python API and its in-memory signed log require a separate server.

For local Docker use, set a private key in the environment (never commit it):

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

Docker serves the Python API on port 8000, **not** the static Pages demonstration. The container uses `APP_ENV=production` and refuses to start without a signing key.

## Technical scope

Python, Pydantic 2, FastAPI, Uvicorn, pytest, JavaScript ES modules, Node's built-in test runner, Docker and GitHub Actions. The demo is intended for modern ES-module-capable desktop and mobile browsers. Browser compatibility and clinical performance have not been formally validated.

## License

[MIT](LICENSE).

# Hfpef Hemodynamic Inpatient Agent

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics
> **Reference Guidelines & Standards:** `AHA/ACC Practice Guidelines & ESC Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Hfpef Hemodynamic Inpatient Agent** is an advanced analytical and computational platform implementing Spot Urine Sodium Trajectory & Diuretic Resistance Agent for inpatient cardiovascular monitoring. It evaluates hemodynamic parameters across specialized sub-agents to detect congestion trajectory anomalies and diuretic resistance patterns.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`Severity`** — dedicated module for severity evaluation and state verification.
- **`DomainKnowledgeRegistry`**: Enterprise domain rules, guideline matrices, and evidence benchmarks.
- **`AgentAlert`** — dedicated module for agent alert evaluation and state verification.
- **`UrineSodiumResponseAgent`**: Specialized Sub-Agent 1 for urine sodium response evaluation
- **`FluidTrajectoryAgent`**: Specialized Sub-Agent 2 for fluid trajectory and kinetic escalation monitoring
- **`NephronBlockadeAdvisorAgent`**: Specialized Sub-Agent 3 for biomarker concordance and nephron blockade advisory

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/hfpef-hemodynamic-inpatient-agent.git
cd hfpef-hemodynamic-inpatient-agent

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## 🖥️ CLI Usage

The CLI provides multiple subcommands for different operations:

### 1. Audit (Single Case Evaluation)
```bash
python cli.py audit --task-id TASK-2026-001 --target KEY-TARGET-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Chat (Supervisory Query)
```bash
python cli.py chat "Explain the current system status"
```

### 3. Batch (CSV Processing)
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail
```bash
python cli.py verify-audit
```

### 5. Serve (REST API Server)
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### CLI Parameters

| Parameter | Command | Description | Default |
|:----------|:--------|:------------|:--------|
| `--task-id` | audit | Unique task / case identifier | TASK-2026-001 |
| `--target` | audit | Target identifier | KEY-TARGET-01 |
| `--primary` | audit | Primary metric (float) | 28.5 |
| `--secondary` | audit | Secondary metric (float) | 14.2 |
| `--critical` | audit | Flag critical status | False |
| `--status` | audit | Status descriptor | DISCORDANT |
| `-i, --input` | batch | Input CSV file path | Required |
| `-o, --output` | batch | Output CSV file path | results.csv |
| `--host` | serve | Server host | 127.0.0.1 |
| `--port` | serve | Server port | 8000 |

### Input Data Schema (for batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Task identifier | Required |
| `target_identifier` | Target entity identifier | Required |
| `primary_metric` | Primary measurement value | Required |
| `secondary_metric` | Secondary measurement value | Optional |
| `is_critical_flag` | Critical status flag | Optional |
| `status_descriptor` | Status description | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Hardening

- The `AUDIT_SECRET_KEY` environment variable **must** be set in production to ensure cryptographic audit trail integrity.
- Without `AUDIT_SECRET_KEY`, a development-only fallback is used with a runtime warning.
- All file I/O operations validate paths to prevent directory traversal attacks.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t hfpef-hemodynamic-inpatient-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secure-key hfpef-hemodynamic-inpatient-agent

# Or use docker-compose
AUDIT_SECRET_KEY=your-secure-key docker-compose up
```

---

## 📁 Project Structure

```
hfpef-hemodynamic-inpatient-agent/
├── agents/                     # Core agent package
│   ├── api.py                  # FastAPI REST endpoints
│   ├── base.py                 # Security, PHI guard, audit trail
│   ├── models.py               # Pydantic data models
│   ├── supervisor.py           # Supervisor orchestrator
│   ├── workers.py              # Specialized worker agents
│   ├── llm_factory.py          # LLM provider factory
│   ├── metrics.py              # Prometheus metrics collector
│   ├── learning.py             # Bayesian calibration engine
│   └── streamer.py             # WebSocket telemetry streamer
├── tests/                      # Test suite
├── hfpef_hemodynamic_inpatient_agent/  # Package module
├── cli.py                      # Main CLI entry point
├── hfpef_sentinel.py           # Standalone sentinel agent
├── enrichment.py               # Feature enrichment engines
├── simulator.py                # Batch simulation tool
├── sample.csv                  # Sample input data
├── Dockerfile                  # Docker build config
└── docker-compose.yml          # Docker Compose config
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

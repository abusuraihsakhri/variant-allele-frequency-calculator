# Variant Allele Frequency Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Standards:** CAP / CLSI / ISO / HIPAA Safe Harbor

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-55%20Passed-brightgreen.svg)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

Variant Allele Frequency Calculator is a clinical decision support tool that computes:

- **Variant Allele Frequency (VAF)** with binomial 95% confidence intervals from tumour/normal sequencing pileup data
- **MELD-Na score** for liver disease severity assessment
- **QTc interval** (Bazett's formula) with clinical interpretation
- **BMI Z-score** with weight category classification
- **HbA1c ↔ eAG** conversion (ADA formula)
- **APRI and FIB-4** liver fibrosis scores

All calculations are implemented using Python stdlib — no external dependencies for core computation.

The enterprise module adds FastAPI REST endpoints, Prometheus telemetry, HMAC-SHA256 tamper-evident audit trails, and a Zero-PHI outbound guard that blocks protected health information from leaving the system.

---

## Installation

### Standard (stdlib core)
```bash
git clone https://github.com/abusuraihsakhri/variant-allele-frequency-calculator.git
cd variant-allele-frequency-calculator
```

### With FastAPI server
```bash
pip install fastapi uvicorn pydantic
```

### Development (with tests)
```bash
pip install -e ".[dev]"
```

---

## Usage

### Core CLI (stdlib)
```bash
# Single calculation with JSON input
python vaf_calc.py single --json '{"variant_depth": 30, "total_depth": 100}'

# MELD-Na calculation
python vaf_calc.py single --bili 2.0 --creat 1.5 --inr 1.2 --na 135

# Batch process CSV
python vaf_calc.py batch --input sample.csv --output results.csv
```

### Enterprise CLI with Multi-Agent Supervisor
```bash
# Run a single task evaluation
python cli.py audit --task-id TASK-01 --primary 28.5 --secondary 14.2

# System chat query
python cli.py chat "Explain current calibration"

# Batch process CSV records
python cli.py batch -i sample.csv -o results.csv

# Verify HMAC audit trail integrity
python cli.py verify-audit

# Launch FastAPI REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### FastAPI REST API
```bash
python cli.py serve
```

Endpoints:
- `GET /health` — Service health check
- `GET /metrics` — Operational metrics (dossier count, audit blocks)
- `POST /api/audit` — Submit task payload for evaluation
- `POST /api/chat` — System configuration query
- `GET /api/audit/logs` — Retrieve HMAC-signed audit trail

### High-Throughput Simulation
```bash
python simulator.py 1000
```

---

## Input Data Schemas

### VAF Calculation
| Field | Type | Description |
|:------|:-----|:------------|
| `variant_depth` | float | Number of reads supporting the variant allele |
| `total_depth` | float | Total read depth at the position |

### MELD-Na Calculation
| Field | Type | Description |
|:------|:-----|:------------|
| `bilirubin` | float | Serum bilirubin (mg/dL) |
| `creatinine` | float | Serum creatinine (mg/dL) |
| `inr` | float | International Normalized Ratio |
| `sodium` | float | Serum sodium (mEq/L) |
| `dialysis` | bool | Whether patient received dialysis (default: false) |

### QTc Calculation
| Field | Type | Description |
|:------|:-----|:------------|
| `qt_ms` | float | QT interval in milliseconds |
| `rr_ms` | float | RR interval in milliseconds (or provide `hr_bpm`) |
| `hr_bpm` | float | Heart rate in beats per minute (alternative to RR) |

### BMI Z-Score
| Field | Type | Description |
|:------|:-----|:------------|
| `weight_kg` | float | Weight in kilograms |
| `height_cm` | float | Height in centimeters |
| `age_months` | float | Age in months (default: 60) |

### HbA1c Conversion
| Field | Type | Description |
|:------|:-----|:------------|
| `hba1c_percent` | float | HbA1c as percentage (provide this OR `eag_mgdl`) |
| `eag_mgdl` | float | Estimated Average Glucose in mg/dL |

### APRI/FIB-4 (Liver Fibrosis)
| Field | Type | Description |
|:------|:-----|:------------|
| `ast_u_l` | float | Aspartate aminotransferase (U/L) |
| `alt_u_l` | float | Alanine aminotransferase (U/L) |
| `platelets_109` | float | Platelet count (×10⁹/L) |
| `age_years` | float | Patient age in years |

---

## Testing

Run the full test suite:
```bash
pytest -v
```

Run specific test modules:
```bash
pytest tests/test_vaf_functions.py -v     # Core calculation functions
pytest tests/test_enrichment.py -v         # Enrichment features
pytest tests/test_variant_allele_frequency_calculator.py -v  # Enterprise supervisor
```

---

## Security Architecture

### Zero-PHI Outbound Guard
Active regex-based inspection that blocks SSNs, MRNs, phone numbers, email addresses, DOB patterns, and patient name identifiers from any outbound data stream.

### HMAC-SHA256 Audit Trail
- Chained, cryptographically signed logs for every evaluation and state transition
- Each entry includes previous hash, creating a tamper-evident blockchain-style ledger
- Integrity verification via `AuditLogger.verify_integrity()`

**Important:** Set the `AUDIT_SECRET_KEY` environment variable in production to ensure persistent audit integrity across restarts. If not set, an ephemeral random key is generated per session.

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

# Windows PowerShell
$env:AUDIT_SECRET_KEY = -join ((48..57) + (97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

### Input Validation
All calculation functions use safe float conversion and validate input ranges to prevent computation errors from malformed data.

---

## Container Deployment

```bash
docker build -t variant-allele-frequency-calculator .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key variant-allele-frequency-calculator
```

With Docker Compose:
```bash
docker-compose up -d
```

---

## Project Structure

```
variant-allele-frequency-calculator/
├── vaf_calc.py          # Core calculation functions (stdlib only)
├── cli.py               # Enterprise CLI with multi-agent supervisor
├── simulator.py         # High-throughput stress testing
├── enrichment.py        # Enrichment feature engine
├── pyproject.toml       # Project metadata and dependencies
├── agents/              # Enterprise agent framework
│   ├── __init__.py
│   ├── api.py           # FastAPI REST endpoints
│   ├── base.py          # Security, PHI guard, HMAC audit trail
│   ├── models.py        # Pydantic data models
│   ├── supervisor.py    # Multi-agent orchestrator
│   ├── workers.py       # Domain-specific evaluation workers
│   ├── metrics.py       # Prometheus metrics collector
│   ├── learning.py      # Bayesian calibration engine
│   ├── llm_factory.py   # LLM client abstraction
│   └── streamer.py      # WebSocket telemetry broadcaster
├── tests/               # Test suite
│   ├── test_vaf_functions.py
│   ├── test_enrichment.py
│   └── test_variant_allele_frequency_calculator.py
├── web/index.html       # Operations console UI
├── sample.csv           # Example input data
├── benchmark_dataset.json  # Golden benchmark test cases
├── Dockerfile
└── docker-compose.yml
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

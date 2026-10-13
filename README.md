# Variant Allele Frequency Calculator

A small browser and Python tool for variant allele frequency (VAF) from alternate-supporting and total read counts, including a two-sided 95% Wilson score confidence interval.

## Browser application

The static application is in [web/](web/). It works directly from `web/index.html` in a current browser, or can be served locally:

```bash
python -m http.server 8000 --directory web
```

Open http://localhost:8000/. Enter alternate and total read counts (nonnegative integers with total > 0). The result includes VAF fraction, percentage, 95% Wilson CI and a descriptive VAF band.

For batch processing, upload a UTF-8 CSV with `variant_depth,total_depth` columns. `alt_depth,depth` are accepted aliases. The browser validates each row and provides a downloadable CSV. Files remain within the browser; no backend, account, external library or Python runtime is required. Browser batch limits are 2 MiB and 10,000 rows.

**Scientific interpretation:** VAF is alternate-supporting reads divided by total depth. The Wilson interval models binomial sampling uncertainty, not sequencing errors, allelic bias, sample purity or biological heterogeneity. **VAF thresholds do not establish zygosity, germline/somatic origin, clonality or copy number.** This calculator has not been clinically validated; do not use it alone for patient care.

## Python CLI

Requires Python 3.10+.

```bash
python -m pip install -e ".[dev]"
vaf-calc single --json '{"variant_depth":30,"total_depth":100}'
vaf-calc batch --input counts.csv --output results.csv
python -m pytest -q
```

Core functions in `vaf_calc.py` require only the standard library. `calculate_vaf(30, 100)` returns the fraction, percentage, Wilson bounds, read counts and a descriptive band. Invalid counts return an `error` field. CSV header aliases are case-insensitive.

The repository also includes pre-existing MELD-Na, QTc, BMI, HbA1c and fibrosis functions plus a generic demonstration score. These are legacy utilities with limited clinical validation; the BMI Z-score is an approximation and **not** a growth-reference Z-score. They are retained for compatibility, not recommended for clinical decision support.

## Optional FastAPI / supervisory module

```bash
python cli.py serve
# http://127.0.0.1:8000/ - browser calculator
# http://127.0.0.1:8000/docs - API documentation
python cli.py audit --task-id TEST-01
python cli.py verify-audit
```

API routes: `/health`, `/metrics`, `/api/audit`, `/api/chat` and `/api/audit/logs`. The supervisory logic is rule-based, not a clinically validated AI assessment. Its chat provider currently returns deterministic mock responses. Do not submit patient identifiers or protected health information.

Audit entries have HMAC-SHA256 integrity verification within a process. The audit trail and signing key are **in-memory**, so they do not constitute a persistent, compliant audit system. Regex-based sensitive-identifier screening is incomplete and is not a HIPAA compliance guarantee.

For Docker:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

**Security:** Never commit the signing key. Docker Compose now requires an externally supplied key. Any previously hard-coded key must be considered disclosed and must not be reused. Data placed in the FastAPI service is processed server-side; the standalone browser calculator is local-only.

## Technology and testing

- Browser: native HTML/CSS/JavaScript; no client-side Python and no third-party dependencies.
- Python: standard-library numerical calculations, FastAPI/Pydantic for the optional API.
- Automated checks: `python -m pytest -q`, `node --check web/app.js`, `node --test web/app.test.cjs` (Node 22+). GitHub Actions runs Python 3.10–3.12 and browser regression tests.
- Browser compatibility: current Chromium, Firefox and Safari versions supporting File.text(), Blob downloads, and standard ES2020 JavaScript.
- Deployable static files: `web/index.html` and `web/app.js` (a Pages workflow is included).

## License

[MIT](LICENSE).

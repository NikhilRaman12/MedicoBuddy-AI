# MedicoBuddy AI — Release Checklist

Before tag & production deployment, verify:

- [ ] All unit, safety, adversarial, and MCP tests pass (`pytest tests/ -v`).
- [ ] Evidence ingestion report exists (`evidence/reports/ingestion_report.json`).
- [ ] No hardcoded passwords, secret keys, or fabricated citations exist.
- [ ] Readiness probe `/health/ready` accurately reports status.
- [ ] Streamlit UI launches without warning banners and renders high-contrast Action Table.
- [ ] Docker build succeeds (`docker build -t medicobuddy .`).

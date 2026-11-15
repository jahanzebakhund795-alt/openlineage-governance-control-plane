# Validation evidence

Prepared November 15, 2026.

- **2 pytest tests passed** using Python 3.9.6.
- Run replay, terminal-state consistency, late START handling, dataset/column lineage, role-derived access, field allowlisting, and keyed pseudonyms. The local catalog demo was executed.
- A full OpenLineage conformance suite and external identity/Atlas integrations were not executed.

Source Python and YAML configurations were parsed. Docker and Java were unavailable on the preparation machine; a parsed configuration is not an executed deployment. The documented Python 3.11 containers are supplied for reproducible integration checks and were not run here.

## Reproduce

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
pytest -q
```

See the README for optional full-stack commands and `reports/validation-summary.json` for the recorded local result.

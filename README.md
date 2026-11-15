# OpenLineage Governance Control Plane

A newly built portfolio implementation for Jahanzeb Akhund, aligned with the data architecture and engineering work described in his resume. All example data is synthetic. This repository is independent sample work; it does not contain employer code, claim a historical deployment, or reproduce resume performance metrics.

## Implemented system

A persistent OpenLineage-style run-event receiver records job transitions, dataset dependencies, and column lineage facets. It provides bounded transitive impact analysis, role-controlled field policies, allowlist-based record projection, keyed pseudonymization, and metadata-only preview audits. Server-validated credentials determine roles; request payloads cannot claim steward privileges.

[Architecture diagram and design review](docs/ARCHITECTURE.md)

## Run

Use Python 3.11 for the documented development environment.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
pytest -q
python -m governance_plane.demo
export GOVERNANCE_ADMIN_KEY=replace-admin-key GOVERNANCE_READER_KEY=replace-reader-key
export MASKING_KEY=replace-with-at-least-32-random-characters
uvicorn governance_plane.api:create_app --factory --port 8000
```

## Design and operating limits

The receiver implements a documented subset of OpenLineage run and column facets, not full schema conformance or an Apache Atlas replacement. Historical edges remain in the catalog, so impact is a conservative union across completed runs. HMAC is pseudonymization, not anonymization. Last-four masking can leak information and must be explicitly selected by policy. Preview records are not persisted, but lineage payloads and policies are; send metadata only. A real deployment needs federated identity, TLS, secret rotation, audit retention, and a multi-process database.

See [the operating guide](docs/OPERATIONS.md) for recovery, deployment, and validation boundaries. An optional GitHub Actions definition is in `docs/ci-template.yml`; enabling it requires installing it under `.github/workflows/` with workflow permission.

## References

- [OpenLineage object model](https://openlineage.io/docs/spec/object-model/)
- [OpenLineage column lineage facet](https://openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet/)

## Executed validation

2 pytest tests passed. Run replay, terminal-state consistency, late START handling, dataset/column lineage, role-derived access, field allowlisting, and keyed pseudonyms. The local catalog demo was executed.

[Full validation evidence and limits](VALIDATION.md)

# Operating guide

## Deployment contract

The receiver implements a documented subset of OpenLineage run and column facets, not full schema conformance or an Apache Atlas replacement. Historical edges remain in the catalog, so impact is a conservative union across completed runs. HMAC is pseudonymization, not anonymization. Last-four masking can leak information and must be explicitly selected by policy. Preview records are not persisted, but lineage payloads and policies are; send metadata only. A real deployment needs federated identity, TLS, secret rotation, audit retention, and a multi-process database.

Keep credentials in environment variables or a secret manager; `.env` is ignored. Example credentials, when present, are for isolated local development. No service in this portfolio is represented as an audited HIPAA/GDPR system.

## Change and recovery procedure

Run the tests before deploying. Start with synthetic fixtures, retain the input batch or event offset, and inspect rejected records before replaying. The source code and tests specify the idempotency keys and transactional boundaries. Do not bypass those boundaries to repair a failed load.

For a real service, define retention and backup policies, TLS, identity federation, per-role permissions, dependency patching, resource limits, and alert destinations. Containers and local files demonstrate deployment contracts; operating these integrations at scale requires load and failure testing in the target environment.

## Validation evidence

`VALIDATION.md` records checks actually executed when this portfolio was prepared. Integration commands requiring external services are explicitly distinguished from executed local tests. No availability, throughput, cost-saving, or compliance guarantee is inferred from unit tests.

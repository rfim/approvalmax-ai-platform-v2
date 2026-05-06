# Client Integration Change Requests

Client integration changes are handled as metadata-first pull requests. The process covers new B2B client onboarding, existing client feature additions, feature removals, schema changes, new CDC contexts, and optional Databricks dashboard candidates.

## Request Flow

1. Add a request JSON file under `sample_data/client_change_requests/`.
2. GitHub Actions runs `scripts/detect_client_integration_changes.py`.
3. If a reviewable change is detected, the workflow writes `recovery/client_integration_change_request.json`.
4. The workflow creates candidate updates to `metadata/client_integrations.yml`.
5. Unknown CDC contexts are added to `metadata/supported_cdc_contexts.yml` with `human_review_required: true`.
6. Optional dashboard candidates are generated under `src/dashboards/` and `resources/dashboard_candidates/`.
7. Codex opens a draft PR for human review.

## Review Rules

- New clients must remain `status: candidate` until reviewed.
- New CDC contexts must not be promoted beyond Bronze until grain and business key are approved.
- Feature removals require backwards compatibility review before downstream models change.
- Business keys and financial metrics must not be changed without explicit approval.
- Dashboard candidates must use Gold or monitoring tables only.
- Dashboard SQL must be tested in Databricks SQL before deployment.
- Dashboard resources in `resources/dashboard_candidates/` are not deployed automatically.

## Dashboard Candidates

Dashboard candidates are intentionally generated as review artefacts. They include a Lakeview dashboard JSON file, a non-deployed candidate bundle resource, and recovery documentation.

Before deploying a dashboard:

1. Confirm the dashboard audience and grain.
2. Test all dashboard SQL queries.
3. Confirm Unity Catalog permissions, row filters, and tenant visibility.
4. Move the reviewed resource into the deployed bundle resource path.
5. Run bundle validation and deployment through CI/CD.

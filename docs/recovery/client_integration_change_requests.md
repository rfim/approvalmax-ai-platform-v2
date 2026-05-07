# Client Integration Change Requests

Client integration changes are handled as metadata-first pull requests. The process covers new B2B client onboarding, existing client feature additions, feature removals, schema changes, new CDC contexts, optional Databricks dashboard candidates, and optional Databricks App candidates.

## Request Flow

1. Add a request JSON file under `sample_data/client_change_requests/`.
2. GitHub Actions runs `scripts/detect_client_integration_changes.py`.
3. If a reviewable change is detected, the workflow writes `recovery/client_integration_change_request.json`.
4. The workflow creates candidate updates to `metadata/client_integrations.yml`.
5. Unknown CDC contexts are added to `metadata/supported_cdc_contexts.yml` with `human_review_required: true`.
6. Optional dashboard candidates are generated under `src/dashboards/` and `resources/dashboard_candidates/`.
7. Optional Databricks App candidates are generated under `src/apps/` and `resources/app_candidates/`.
8. Codex opens a draft PR for human review.

## Review Rules

- New clients must remain `status: candidate` until reviewed.
- New CDC contexts must not be promoted beyond Bronze until grain and business key are approved.
- Feature removals require backwards compatibility review before downstream models change.
- Business keys and financial metrics must not be changed without explicit approval.
- Dashboard candidates must use Gold or monitoring tables only.
- Dashboard SQL must be tested in Databricks SQL before deployment.
- Dashboard resources in `resources/dashboard_candidates/` are not deployed automatically.
- Databricks App candidates must use `app.yaml` `valueFrom` for platform resources.
- Databricks App candidates must not hardcode secrets, tokens, warehouse IDs, or tenant filters.
- Databricks App resources in `resources/app_candidates/` are not deployed automatically.

## Dashboard Candidates

Dashboard candidates are intentionally generated as review artefacts. They include a Lakeview dashboard JSON file, a non-deployed candidate bundle resource, and recovery documentation.

Before deploying a dashboard:

1. Confirm the dashboard audience and grain.
2. Test all dashboard SQL queries.
3. Confirm Unity Catalog permissions, row filters, and tenant visibility.
4. Move the reviewed resource into the deployed bundle resource path.
5. Run bundle validation and deployment through CI/CD.

## Databricks App Candidates

App candidates are generated as Streamlit apps for client operations views. They use Databricks app authentication, SQL warehouse resource binding through `app.yaml`, and reviewed Gold and monitoring tables.

Before deploying an app:

1. Confirm the client should receive a Databricks App.
2. Confirm Unity Catalog grants, row filters, column masks, and tenant visibility.
3. Confirm the SQL warehouse resource binding.
4. Confirm no financial metrics are redefined.
5. Move the reviewed app resource into the deployed bundle resource path.

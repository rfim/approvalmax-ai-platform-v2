# approvalmax_ai_platform_v2

`approvalmax_ai_platform_v2` is a Databricks Asset Bundle demo for an AI-native data platform patterned after ApprovalMax workflows.

It implements a thin slice:

```text
CDC JSONL files
-> GitHub Actions trigger
-> Databricks Asset Bundle validation
-> Databricks serverless notebook job
-> Bronze raw CDC table
-> Silver current-state tables
-> Vault-style integration tables
-> Gold semantic marts
-> dbt Gold model and tests
-> Great Expectations-style validation
-> Dashboard-ready monitoring tables
-> Codex semi self-healing PR workflow
```

## Databricks Layout

Bundle name: `approvalmax_ai_platform_v2`

Target: `dev`

Databricks CLI profile: `vim`

Unity Catalog schemas:

- `approvalmax_ai_platform.bronze`
- `approvalmax_ai_platform.silver`
- `approvalmax_ai_platform.vault`
- `approvalmax_ai_platform.gold`
- `approvalmax_ai_platform.quarantine`
- `approvalmax_ai_platform.monitoring`

The workspace is serverless-only. Bundle jobs use notebook task resources without classic cluster settings.

## Project Structure

```text
approvalmax_ai_platform_v2/
├── databricks.yml
├── resources/
├── src/
├── models/
├── metadata/
├── scripts/
├── sample_data/
├── docs/
├── skills/
└── .github/workflows/
```

## Required GitHub Secrets

- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN`
- `CODEX_AUTH_JSON`

Optional:

- `OPENAI_API_KEY`

Do not commit `profiles.yml`, tokens, `.codex/auth.json`, or any generated recovery artifacts.

## Deploy

```bash
databricks bundle validate -t dev --profile vim
databricks bundle deploy -t dev --profile vim
```

## Run CDC Automation

```bash
databricks bundle run approvalmax_cdc_automation_serverless -t dev --profile vim
```

This runs `src/cdc_automation_notebook.ipynb`, which:

- creates the six Unity Catalog schemas
- creates inline CDC records with `spark.createDataFrame(records)`
- writes `approvalmax_ai_platform.bronze.approvalmax_cdc_raw`
- builds Silver current-state tables
- builds Vault-style hub/link/satellite tables
- builds Gold dimensions and facts
- writes ETL audit logs to `approvalmax_ai_platform.monitoring.etl_audit_log`
- writes failed quality rows to `approvalmax_ai_platform.quarantine`

## Run dbt

Copy the example profile and replace `<WAREHOUSE_ID>` with a Databricks SQL warehouse ID.

```bash
cp profiles.yml.example profiles.yml
dbt deps --profiles-dir .
dbt debug --profiles-dir . --target dev
dbt compile --profiles-dir . --target dev
dbt run --profiles-dir . --target dev --select fact_approval_document_lifecycle_dbt
dbt test --profiles-dir . --target dev --select fact_approval_document_lifecycle_dbt
```

The dbt Gold model builds:

```text
approvalmax_ai_platform.gold.fact_approval_document_lifecycle_dbt
```

In GitHub Actions, `run-dbt-gold.yml` discovers an available SQL warehouse and replaces the placeholder in the generated `profiles.yml`.

## Run Great Expectations-Style Validation

```bash
databricks bundle run approvalmax_great_expectations_serverless -t dev --profile vim
```

The validation notebook writes results to:

```text
approvalmax_ai_platform.monitoring.great_expectations_results
```

Critical checks:

- `document_id` not null
- `company_id` not null
- `document_status` accepted values
- `total_amount >= 0`
- `approval_cycle_time_minutes >= 0`
- Gold grain unique by `document_id`

## Refresh Dashboard Tables

```bash
databricks bundle run approvalmax_dashboard_refresh_serverless -t dev --profile vim
```

This builds:

- `dashboard_kpi_snapshot`
- `dashboard_layer_row_counts`
- `dashboard_pipeline_run_summary`
- `dashboard_etl_step_timeline`
- `dashboard_quality_status`
- `dashboard_gold_documents`

## Detect New CDC Contexts

Run locally:

```bash
python scripts/detect_new_cdc_contexts.py
```

The script reads `sample_data/approvalmax_cdc/*.jsonl`, compares `source_table` values with `metadata/supported_cdc_contexts.yml`, writes `recovery/new_cdc_contexts.json`, and exits:

- `0` when no new contexts exist
- `10` when new contexts exist
- non-zero for detector errors

Known candidate key inference includes:

- `payments -> payment_id`
- `payment_batches -> payment_batch_id`
- `budgets -> budget_id`
- `expense_claims -> expense_claim_id`
- `vendor_contracts -> vendor_contract_id`
- `audit_policies -> audit_policy_id`
- `suppliers -> supplier_id`

New contexts are marked `human_review_required: true`. Do not promote new CDC contexts beyond Bronze until the grain and business key are approved.

## GitHub Actions Chain

- `Databricks Bundle CI`: validates and deploys the bundle.
- `Run CDC Automation`: validates and runs the deployed CDC job when CDC sample files change.
- `Run dbt Gold Models`: runs dbt after CDC succeeds or when dbt files change.
- `Run Great Expectations`: runs validation after dbt succeeds.
- `Refresh Dashboard Tables`: refreshes dashboard tables after validation succeeds.
- `Detect New CDC Contexts`: creates candidate metadata PRs for unknown CDC contexts.
- `Codex Auto Fix On Failure`: creates reviewable recovery PRs for failed workflows.

## AI Recovery Safety

AI-assisted recovery is semi self-healing, not autonomous production change.

Rules:

- AI proposes, tests validate, humans approve, CI/CD deploys.
- Do not auto-merge.
- Do not disable tests.
- Do not change or print secrets.
- Do not change business keys without human review.
- Do not redefine financial metrics without human review.
- New CDC contexts require human review before promotion beyond Bronze.

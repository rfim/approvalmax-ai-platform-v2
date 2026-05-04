---
name: approvalmax-semi-self-recovery
description: Diagnose ApprovalMax v2 Databricks bundle, dbt, validation, dashboard, and CDC context failures and prepare minimal reviewable recovery patches.
---

# ApprovalMax Semi Self-Recovery

This skill is for semi self-healing only. It may propose a patch and PR. It must not auto-merge, disable tests, change secrets, print secrets, change business keys, or redefine financial metrics without human review.

## missing_schema

Evidence: `SCHEMA_NOT_FOUND`, `USE SCHEMA` failure.
Fix: add `CREATE SCHEMA IF NOT EXISTS workspace.<schema>` before reads or writes. Keep schema names stable.

## missing_tool_uv

Evidence: `uv: command not found`.
Fix: install uv in the failing GitHub Actions workflow before bundle commands.

## databricks_auth_failure

Evidence: `cannot configure default credentials`, failed `databricks current-user me`.
Fix: ensure workflows use `DATABRICKS_HOST` and `DATABRICKS_TOKEN` secrets. Never print token values.

## schema_type_change

Evidence: cast/type failures.
Fix: add safe casts and quarantine invalid records. Do not silently coerce financial values.

## duplicate_or_grain_failure

Evidence: unique/grain/dbt test failures.
Fix: add deterministic deduplication or diagnostics. Do not remove uniqueness tests.

## missing_required_value

Evidence: not-null failures.
Fix: quarantine rows and document missing fields. Do not fabricate keys.

## invalid_business_metric

Evidence: incorrect or disputed financial metric.
Fix: stop at diagnostics and require human review. Do not redefine metrics.

## great_expectations_failure

Evidence: failed rows in `approvalmax_ai_platform.monitoring.great_expectations_results`.
Fix: inspect expectation results, add quarantine/reporting, and keep critical expectations active.

## new_cdc_context_detected

Evidence: `scripts/detect_new_cdc_contexts.py` exits 10.
Fix: update `metadata/supported_cdc_contexts.yml` with candidate metadata and `human_review_required: true`; add docs under `docs/recovery/`. Add Silver/Gold/dbt changes only when grain and business key are obvious and low risk.


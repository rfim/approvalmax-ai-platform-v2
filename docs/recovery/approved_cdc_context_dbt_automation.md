# Approved CDC Context dbt Automation

When a candidate CDC context is ready for modelling, update `metadata/supported_cdc_contexts.yml` in the candidate PR:

```yaml
status: approved_for_modelling
human_review_required: false
```

After that PR is merged to `main`, GitHub Actions runs `Generate dbt and GE for Approved CDC Contexts`.
The workflow creates a separate draft PR with generated dbt current-state models under `models/gold/generated/`.

The generated models read from Bronze raw CDC, use the approved business key, and include basic dbt tests.
Great Expectations-style validation discovers generated `*_current_dbt` Gold tables and validates source table, sequence, raw payload, primary key presence, and primary-key grain.
The automation intentionally does not define financial metrics or promote unknown contexts without human approval.

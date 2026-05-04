# Dashboard Queries

Use these tables from `approvalmax_ai_platform.monitoring`:

```sql
SELECT * FROM approvalmax_ai_platform.monitoring.dashboard_kpi_snapshot;
SELECT * FROM approvalmax_ai_platform.monitoring.dashboard_layer_row_counts;
SELECT * FROM approvalmax_ai_platform.monitoring.dashboard_pipeline_run_summary;
SELECT * FROM approvalmax_ai_platform.monitoring.dashboard_etl_step_timeline;
SELECT * FROM approvalmax_ai_platform.monitoring.dashboard_quality_status;
SELECT * FROM approvalmax_ai_platform.monitoring.dashboard_gold_documents;
```

Recommended dashboard sections:
- Lifecycle KPIs from `dashboard_kpi_snapshot`
- Row-count health by layer from `dashboard_layer_row_counts`
- Pipeline history from `dashboard_pipeline_run_summary`
- Step timeline from `dashboard_etl_step_timeline`
- Validation status from `dashboard_quality_status`
- Document details from `dashboard_gold_documents`


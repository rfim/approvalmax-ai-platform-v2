# Dashboard Queries

Use these tables from `workspace.approvalmax_v2_monitoring`:

```sql
SELECT * FROM workspace.approvalmax_v2_monitoring.dashboard_kpi_snapshot;
SELECT * FROM workspace.approvalmax_v2_monitoring.dashboard_layer_row_counts;
SELECT * FROM workspace.approvalmax_v2_monitoring.dashboard_pipeline_run_summary;
SELECT * FROM workspace.approvalmax_v2_monitoring.dashboard_etl_step_timeline;
SELECT * FROM workspace.approvalmax_v2_monitoring.dashboard_quality_status;
SELECT * FROM workspace.approvalmax_v2_monitoring.dashboard_gold_documents;
```

Recommended dashboard sections:
- Lifecycle KPIs from `dashboard_kpi_snapshot`
- Row-count health by layer from `dashboard_layer_row_counts`
- Pipeline history from `dashboard_pipeline_run_summary`
- Step timeline from `dashboard_etl_step_timeline`
- Validation status from `dashboard_quality_status`
- Document details from `dashboard_gold_documents`


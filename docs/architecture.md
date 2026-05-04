# Architecture

`approvalmax_ai_platform_v2` is a thin-slice Databricks Asset Bundle for an AI-native data platform demo.

Flow:

```text
CDC JSONL
-> GitHub Actions
-> Databricks bundle validation
-> serverless notebook job
-> Bronze raw CDC
-> Silver current-state tables
-> Vault-style integration tables
-> Gold semantic marts
-> dbt Gold model/tests
-> Great Expectations-style validation
-> dashboard-ready monitoring tables
-> Codex semi self-healing PR workflow
```

Unity Catalog schemas:
- `workspace.approvalmax_v2_bronze`
- `workspace.approvalmax_v2_silver`
- `workspace.approvalmax_v2_vault`
- `workspace.approvalmax_v2_gold`
- `workspace.approvalmax_v2_quarantine`
- `workspace.approvalmax_v2_monitoring`

All Databricks jobs are notebook tasks with no cluster configuration so serverless compute can be used by the workspace.


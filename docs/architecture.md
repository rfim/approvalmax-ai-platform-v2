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
- `approvalmax_ai_platform.bronze`
- `approvalmax_ai_platform.silver`
- `approvalmax_ai_platform.vault`
- `approvalmax_ai_platform.gold`
- `approvalmax_ai_platform.quarantine`
- `approvalmax_ai_platform.monitoring`

All Databricks jobs are notebook tasks with no cluster configuration so serverless compute can be used by the workspace.


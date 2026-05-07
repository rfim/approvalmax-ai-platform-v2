# Dashboard Candidate: Apex Manufacturing

Client: `client_apex_manufacturing`

Dashboard type: `client_operations`

This candidate uses reviewed Gold and monitoring tables only:

- `approvalmax_ai_platform.gold.fact_approval_document_lifecycle`
- `approvalmax_ai_platform.monitoring.dashboard_quality_status`

Human review checklist:

- [ ] Confirm the client dashboard grain.
- [ ] Confirm requested metrics do not redefine financial measures.
- [ ] Test every dashboard SQL query in Databricks SQL before deployment.
- [ ] Confirm Unity Catalog permissions, row filters, and tenant visibility.
- [ ] Move the candidate resource into the deployed bundle resource path only after approval.

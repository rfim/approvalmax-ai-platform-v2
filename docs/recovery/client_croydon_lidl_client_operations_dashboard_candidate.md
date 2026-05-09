# Dashboard Candidate: Croydon Lidl

Client: `client_croydon_lidl`

Dashboard type: `client_operations`

This client-specific candidate uses reviewed Gold and monitoring tables only:

- `approvalmax_ai_platform.gold.fact_approval_document_lifecycle`
- `approvalmax_ai_platform.monitoring.dashboard_quality_status`

Validated dashboard datasets:

- Lidl document summary: document count, total document value, average approval cycle time, and SLA breach count.
- Lidl documents by status: status distribution with value and cycle-time context.
- Lidl company performance: company-level document count, value, cycle time, and SLA breach count.
- Lidl supplier exposure: top suppliers by document value and cycle time.
- Lidl document detail: latest lifecycle records for operational review.
- Lidl quality status: latest governance checks from monitoring.

Human review checklist:

- [ ] Confirm the client dashboard grain.
- [ ] Confirm requested metrics do not redefine financial measures.
- [x] Test every dashboard SQL query in Databricks SQL before deployment.
- [ ] Confirm Unity Catalog permissions, row filters, and tenant visibility.
- [ ] Move the candidate resource into the deployed bundle resource path only after approval.

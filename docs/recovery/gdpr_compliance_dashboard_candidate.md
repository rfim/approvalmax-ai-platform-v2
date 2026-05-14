# GDPR Compliance Dashboard Candidate

Dashboard: `gdpr_compliance`

This candidate provides an evidence dashboard for GDPR/UK GDPR operational controls. It is not a legal determination of compliance and must be reviewed by the DPO, legal/privacy, data governance, and platform owners before deployment.

Reviewed control areas:

- Individual rights request evidence: access, rectification, erasure/right to be forgotten, restriction, portability, objection, and automated decision-making review.
- Right to be forgotten evidence: keyword evidence in `tenant_change_log` until a formal erasure execution register exists.
- Processing inventory evidence from `monitoring.etl_audit_log`.
- Retention review candidates from Gold document lifecycle timestamps.
- Data quality and accuracy evidence from `monitoring.dashboard_quality_status`.
- Explicit gap reporting for missing source tables such as DSAR intake, consent/legal basis, portability exports, restriction/objection workflow, and automated decisioning/profiling registry.

Validated dashboard datasets:

- `gdpr_compliance_summary`
- `gdpr_individual_rights_evidence`
- `gdpr_processing_inventory`
- `gdpr_retention_review`
- `gdpr_quality_evidence`
- `gdpr_control_coverage`

Human review checklist:

- [x] Test every dashboard SQL query in Databricks SQL before deployment.
- [ ] Confirm GDPR/UK GDPR reporting requirements with DPO/legal.
- [ ] Confirm retention threshold and policy mapping; this candidate uses an 84-month review threshold.
- [ ] Confirm tenant/client visibility rules and Unity Catalog row filters.
- [ ] Add formal DSAR, erasure, consent/legal-basis, portability, restriction/objection, and automated decisioning source tables before treating the dashboard as complete compliance evidence.
- [ ] Move the candidate resource into the deployed bundle resource path only after approval.

Reference guidance:

- ICO individual rights guidance: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/
- ICO right to erasure guidance: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/

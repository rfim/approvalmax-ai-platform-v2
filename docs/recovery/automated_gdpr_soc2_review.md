# Automated GDPR and SOC 2 Change Review

The platform workflow runs `scripts/compliance_change_review.py` on pull requests and main-branch pushes that touch platform, data, dashboard, model, metadata, workflow, or recovery files.

The review is evidence-oriented. It does not certify GDPR, UK GDPR, or SOC 2 compliance, and it does not replace human approval. It highlights governance-relevant changes and fails only on hard safety violations such as secret/auth file changes or quality gate removals.

Review coverage:

- GDPR: data minimisation, data-subject rights terms, right to erasure/right to be forgotten, retention, client/CDC metadata, dashboard exposure, and privacy review requirements.
- SOC 2: change management, processing integrity, confidentiality/privacy, availability, quality gate retention, access review for Databricks Apps, and dashboard permission review.

Workflow behaviour:

- Pull requests receive a Markdown review comment and an uploaded JSON/Markdown artefact.
- Pushes to `main` run the same review before deployment and CDC execution.
- Warning checks require reviewer acknowledgement.
- Failed checks must be resolved before merge or deployment.

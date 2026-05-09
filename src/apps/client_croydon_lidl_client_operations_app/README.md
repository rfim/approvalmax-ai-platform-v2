# Croydon Lidl Operations App

Candidate Databricks App for `client_croydon_lidl`.

The app uses Streamlit, Databricks app authentication, and a SQL warehouse resource supplied through `app.yaml` `valueFrom`.

Review before deployment:

- Confirm tenant/client visibility rules.
- Confirm Unity Catalog grants, row filters, and column masks.
- Confirm the SQL warehouse resource binding.
- Confirm no financial metrics are redefined.

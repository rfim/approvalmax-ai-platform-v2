# Client Integration Change Request

Candidate metadata was generated from client change request files.
Human review is required before modelling, dashboard deployment, or feature promotion.

## Quality Gate

- Status: `warning`
- Critical failures: `0`
- Warnings: `2`

## Croydon Lidl

- Client id: `client_croydon_lidl`
- Request type: `new_client`
- Required actions: `app_candidate_requested, context_or_schema_change, dashboard_candidate_requested, new_client, unknown_cdc_context`
- Quality status: `warning`

### Quality Checks

| Check | Status | Severity | Details |
| --- | --- | --- | --- |
| `request_required_fields_present` | `passed` | `info` | All required request fields are present. |
| `request_type_supported` | `passed` | `info` | request_type='new_client' |
| `new_client_not_already_active` | `passed` | `info` | Client does not already exist. |
| `request_contexts_unique` | `passed` | `info` | No duplicate source_table values. |
| `companies_context_required_fields_present` | `passed` | `info` | All required context fields are present. |
| `companies_business_key_matches_registry` | `passed` | `info` | requested='company_id', registry='company_id' |
| `companies_feature_removal_review` | `passed` | `info` | No feature removals requested for this context. |
| `finance_documents_context_required_fields_present` | `passed` | `info` | All required context fields are present. |
| `finance_documents_business_key_matches_registry` | `passed` | `info` | requested='document_id', registry='document_id' |
| `finance_documents_feature_removal_review` | `warning` | `warning` | Disabled features require compatibility review: expense_claims |
| `approval_events_context_required_fields_present` | `passed` | `info` | All required context fields are present. |
| `approval_events_business_key_matches_registry` | `passed` | `info` | requested='event_id', registry='event_id' |
| `approval_events_feature_removal_review` | `passed` | `info` | No feature removals requested for this context. |
| `users_context_required_fields_present` | `passed` | `info` | All required context fields are present. |
| `users_business_key_matches_registry` | `passed` | `info` | requested='user_id', registry='user_id' |
| `users_feature_removal_review` | `passed` | `info` | No feature removals requested for this context. |
| `retail_store_locations_context_required_fields_present` | `passed` | `info` | All required context fields are present. |
| `retail_store_locations_business_key_candidate_present` | `passed` | `warning` | Candidate business key 'store_id'; context is not approved in registry. |
| `retail_store_locations_feature_removal_review` | `passed` | `info` | No feature removals requested for this context. |
| `dashboard_sources_are_curated` | `passed` | `info` | Dashboard uses Gold or monitoring tables only. |
| `dashboard_metrics_declared` | `passed` | `info` | Requested metrics: document_count, approval_cycle_time_minutes, approval_sla_breach_flag, validation_status |
| `app_framework_supported` | `passed` | `info` | framework='streamlit'; current generator supports streamlit. |
| `app_sources_are_curated` | `passed` | `info` | App uses Gold or monitoring tables only. |


```json
{
  "change_count": 1,
  "changes": [
    {
      "request_id": "new_client_croydon_lidl",
      "request_file": "sample_data/client_change_requests/new_client_croydon_lidl.json",
      "client_id": "client_croydon_lidl",
      "display_name": "Croydon Lidl",
      "request_type": "new_client",
      "required_actions": [
        "app_candidate_requested",
        "context_or_schema_change",
        "dashboard_candidate_requested",
        "new_client",
        "unknown_cdc_context"
      ],
      "context_changes": [
        {
          "source_table": "companies",
          "change": "context_added"
        },
        {
          "source_table": "finance_documents",
          "change": "context_added"
        },
        {
          "source_table": "approval_events",
          "change": "context_added"
        },
        {
          "source_table": "users",
          "change": "context_added"
        },
        {
          "source_table": "retail_store_locations",
          "change": "context_added"
        }
      ],
      "unknown_contexts": [
        {
          "source_table": "retail_store_locations",
          "candidate_business_key": "store_id",
          "human_review_required": true,
          "reason": "source_table is not in metadata/supported_cdc_contexts.yml"
        }
      ],
      "candidate_client_config": {
        "status": "candidate",
        "display_name": "Croydon Lidl",
        "enabled_contexts": {
          "companies": {
            "schema_version": "approvalmax_cdc_v1",
            "features": {
              "company_master_data": true,
              "multi_entity_reporting": true
            },
            "business_key": "company_id"
          },
          "finance_documents": {
            "schema_version": "approvalmax_cdc_v1",
            "features": {
              "purchase_orders": true,
              "invoice_approval": true,
              "expense_claims": false
            },
            "business_key": "document_id"
          },
          "approval_events": {
            "schema_version": "approvalmax_cdc_v1",
            "features": {
              "approval_workflows": true,
              "delegated_approvals": true
            },
            "business_key": "event_id"
          },
          "users": {
            "schema_version": "approvalmax_cdc_v1",
            "features": {
              "approver_assignment": true,
              "store_manager_approvals": true
            },
            "business_key": "user_id"
          },
          "retail_store_locations": {
            "schema_version": "approvalmax_retail_cdc_v1",
            "features": {
              "store_level_spend_reporting": true,
              "regional_approval_routing": true
            },
            "business_key": "store_id"
          }
        },
        "human_review_required": true,
        "source_request_id": "new_client_croydon_lidl",
        "dashboards": {
          "client_operations": {
            "status": "candidate",
            "grain": "company_id",
            "source_tables": [
              "approvalmax_ai_platform.gold.fact_approval_document_lifecycle",
              "approvalmax_ai_platform.monitoring.dashboard_quality_status"
            ],
            "requested_metrics": [
              "document_count",
              "approval_cycle_time_minutes",
              "approval_sla_breach_flag",
              "validation_status"
            ],
            "human_review_required": true
          }
        },
        "apps": {
          "client_operations": {
            "status": "candidate",
            "framework": "streamlit",
            "source_tables": [
              "approvalmax_ai_platform.gold.fact_approval_document_lifecycle",
              "approvalmax_ai_platform.monitoring.dashboard_quality_status"
            ],
            "human_review_required": true
          }
        }
      },
      "dashboard_request": {
        "required": true,
        "dashboard_type": "client_operations",
        "grain": "company_id",
        "primary_tables": [
          "approvalmax_ai_platform.gold.fact_approval_document_lifecycle",
          "approvalmax_ai_platform.monitoring.dashboard_quality_status"
        ],
        "requested_metrics": [
          "document_count",
          "approval_cycle_time_minutes",
          "approval_sla_breach_flag",
          "validation_status"
        ],
        "human_review_required": true
      },
      "app_request": {
        "required": true,
        "app_type": "client_operations",
        "framework": "streamlit",
        "primary_tables": [
          "approvalmax_ai_platform.gold.fact_approval_document_lifecycle",
          "approvalmax_ai_platform.monitoring.dashboard_quality_status"
        ],
        "human_review_required": true
      },
      "quality_evaluation": {
        "overall_status": "warning",
        "critical_failure_count": 0,
        "warning_count": 2,
        "checks": [
          {
            "name": "request_required_fields_present",
            "status": "passed",
            "severity": "info",
            "details": "All required request fields are present."
          },
          {
            "name": "request_type_supported",
            "status": "passed",
            "severity": "info",
            "details": "request_type='new_client'"
          },
          {
            "name": "new_client_not_already_active",
            "status": "passed",
            "severity": "info",
            "details": "Client does not already exist."
          },
          {
            "name": "request_contexts_unique",
            "status": "passed",
            "severity": "info",
            "details": "No duplicate source_table values."
          },
          {
            "name": "companies_context_required_fields_present",
            "status": "passed",
            "severity": "info",
            "details": "All required context fields are present."
          },
          {
            "name": "companies_business_key_matches_registry",
            "status": "passed",
            "severity": "info",
            "details": "requested='company_id', registry='company_id'"
          },
          {
            "name": "companies_feature_removal_review",
            "status": "passed",
            "severity": "info",
            "details": "No feature removals requested for this context."
          },
          {
            "name": "finance_documents_context_required_fields_present",
            "status": "passed",
            "severity": "info",
            "details": "All required context fields are present."
          },
          {
            "name": "finance_documents_business_key_matches_registry",
            "status": "passed",
            "severity": "info",
            "details": "requested='document_id', registry='document_id'"
          },
          {
            "name": "finance_documents_feature_removal_review",
            "status": "warning",
            "severity": "warning",
            "details": "Disabled features require compatibility review: expense_claims"
          },
          {
            "name": "approval_events_context_required_fields_present",
            "status": "passed",
            "severity": "info",
            "details": "All required context fields are present."
          },
          {
            "name": "approval_events_business_key_matches_registry",
            "status": "passed",
            "severity": "info",
            "details": "requested='event_id', registry='event_id'"
          },
          {
            "name": "approval_events_feature_removal_review",
            "status": "passed",
            "severity": "info",
            "details": "No feature removals requested for this context."
          },
          {
            "name": "users_context_required_fields_present",
            "status": "passed",
            "severity": "info",
            "details": "All required context fields are present."
          },
          {
            "name": "users_business_key_matches_registry",
            "status": "passed",
            "severity": "info",
            "details": "requested='user_id', registry='user_id'"
          },
          {
            "name": "users_feature_removal_review",
            "status": "passed",
            "severity": "info",
            "details": "No feature removals requested for this context."
          },
          {
            "name": "retail_store_locations_context_required_fields_present",
            "status": "passed",
            "severity": "info",
            "details": "All required context fields are present."
          },
          {
            "name": "retail_store_locations_business_key_candidate_present",
            "status": "passed",
            "severity": "warning",
            "details": "Candidate business key 'store_id'; context is not approved in registry."
          },
          {
            "name": "retail_store_locations_feature_removal_review",
            "status": "passed",
            "severity": "info",
            "details": "No feature removals requested for this context."
          },
          {
            "name": "dashboard_sources_are_curated",
            "status": "passed",
            "severity": "info",
            "details": "Dashboard uses Gold or monitoring tables only."
          },
          {
            "name": "dashboard_metrics_declared",
            "status": "passed",
            "severity": "info",
            "details": "Requested metrics: document_count, approval_cycle_time_minutes, approval_sla_breach_flag, validation_status"
          },
          {
            "name": "app_framework_supported",
            "status": "passed",
            "severity": "info",
            "details": "framework='streamlit'; current generator supports streamlit."
          },
          {
            "name": "app_sources_are_curated",
            "status": "passed",
            "severity": "info",
            "details": "App uses Gold or monitoring tables only."
          }
        ]
      },
      "human_review_required": true
    }
  ],
  "quality_gate": {
    "status": "warning",
    "critical_failure_count": 0,
    "warning_count": 2,
    "review_required": true
  },
  "safety": {
    "auto_merge": false,
    "business_key_changes_require_review": true,
    "financial_metric_changes_allowed": false,
    "dashboard_publish_allowed": false,
    "app_deploy_allowed": false
  }
}
```

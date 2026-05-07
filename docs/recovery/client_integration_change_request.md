# Client Integration Change Request

Candidate metadata was generated from client change request files.
Human review is required before modelling, dashboard deployment, or feature promotion.

## Northwind Procurement

- Client id: `client_northwind_procurement`
- Request type: `new_client`
- Required actions: `app_candidate_requested, dashboard_candidate_requested`


```json
{
  "change_count": 1,
  "changes": [
    {
      "request_id": "new_client_procurement_dashboard",
      "request_file": "sample_data/client_change_requests/new_client_procurement_dashboard.json",
      "client_id": "client_northwind_procurement",
      "display_name": "Northwind Procurement",
      "request_type": "new_client",
      "required_actions": [
        "app_candidate_requested",
        "dashboard_candidate_requested"
      ],
      "context_changes": [],
      "unknown_contexts": [],
      "candidate_client_config": {
        "status": "candidate",
        "display_name": "Northwind Procurement",
        "enabled_contexts": {
          "companies": {
            "schema_version": "approvalmax_cdc_v1",
            "features": {
              "company_master_data": true
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
              "delegated_approval": false
            },
            "business_key": "event_id"
          },
          "users": {
            "schema_version": "approvalmax_cdc_v1",
            "features": {
              "approver_assignment": true
            },
            "business_key": "user_id"
          }
        },
        "human_review_required": true,
        "source_request_id": "new_client_procurement_dashboard",
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
      "human_review_required": true
    }
  ],
  "safety": {
    "auto_merge": false,
    "business_key_changes_require_review": true,
    "financial_metric_changes_allowed": false,
    "dashboard_publish_allowed": false,
    "app_deploy_allowed": false
  }
}
```

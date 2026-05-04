# New CDC Contexts Detected

Candidate metadata was inferred from CDC envelopes. Human review is required before promotion beyond Bronze.

```json
{
  "budgets": {
    "candidate_business_key": "budget_id",
    "candidate_silver_table": "budgets_current",
    "candidate_gold_tables": [
      "dim_budget"
    ],
    "human_review_required": true,
    "files": [
      "sample_data/approvalmax_cdc/schema_evolution_budgets_20260504.jsonl"
    ],
    "sample_records": [
      {
        "schema": "approvalmax_budgeting_cdc_v1",
        "source_system": "approvalmax_mock_budget_service",
        "source_table": "budgets",
        "op": "c",
        "sequence_id": 300401,
        "event_timestamp": "2026-05-04T22:28:00Z",
        "ingestion_timestamp": "2026-05-04T22:28:20Z",
        "primary_key": {
          "budget_id": "BUD-003",
          "company_id": "COMP-003"
        },
        "before": {},
        "after": {
          "budget_id": "BUD-003",
          "company_id": "COMP-003",
          "budget_name": "FY2026 Operations",
          "budget_owner_user_id": "USR-003",
          "period_start": "2026-01-01",
          "period_end": "2026-12-31",
          "budget_amount": 50000.0,
          "committed_amount": 1200.0,
          "currency": "GBP",
          "dimensions": {
            "department": "Finance",
            "region": "EMEA"
          },
          "status": "active"
        },
        "metadata": {
          "connector": "mock_debezium_style",
          "database": "approvalmax_budgeting",
          "lsn": 300401,
          "tx_id": "TX-030401",
          "is_snapshot": false,
          "schema_version": "budget_v1"
        }
      }
    ]
  },
  "payments": {
    "candidate_business_key": "payment_id",
    "candidate_silver_table": "payments_current",
    "candidate_gold_tables": [
      "dim_payment"
    ],
    "human_review_required": true,
    "files": [
      "sample_data/approvalmax_cdc/new_context_payments_test.jsonl",
      "sample_data/approvalmax_cdc/schema_evolution_payments_20260504.jsonl"
    ],
    "sample_records": [
      {
        "schema": "approvalmax_cdc_v1",
        "source_system": "approvalmax_mock_cdc",
        "source_table": "payments",
        "op": "c",
        "sequence_id": 200001,
        "event_timestamp": "2026-05-04T12:00:00Z",
        "ingestion_timestamp": "2026-05-04T12:00:20Z",
        "primary_key": {
          "payment_id": "PAY-TEST-001",
          "company_id": "COMP-001"
        },
        "before": null,
        "after": {
          "payment_id": "PAY-TEST-001",
          "company_id": "COMP-001",
          "document_id": "PO-001",
          "supplier_id": "SUP-001",
          "payment_status": "scheduled",
          "payment_amount": 850.25,
          "currency": "GBP",
          "scheduled_at": "2026-05-06T09:00:00Z",
          "paid_at": null,
          "created_at": "2026-05-04T12:00:00Z",
          "updated_at": "2026-05-04T12:00:00Z"
        },
        "metadata": {
          "connector": "mock_debezium_style",
          "database": "approvalmax_operational",
          "lsn": 200001,
          "tx_id": "TX-020001",
          "is_snapshot": false,
          "note": "test_new_context_payments"
        }
      },
      {
        "schema": "approvalmax_payments_cdc_v2",
        "source_system": "approvalmax_mock_payment_service",
        "source_table": "payments",
        "op": "c",
        "sequence_id": 300301,
        "event_timestamp": "2026-05-04T22:27:00Z",
        "ingestion_timestamp": "2026-05-04T22:27:20Z",
        "primary_key": {
          "payment_id": "PAY-003",
          "company_id": "COMP-003"
        },
        "before": {},
        "after": {
          "payment_id": "PAY-003",
          "company_id": "COMP-003",
          "document_id": "INV-003",
          "payment_batch_id": "PB-003",
          "payment_status": "scheduled",
          "payment_method": "bank_transfer",
          "payment_amount": 1200.0,
          "currency": "GBP",
          "scheduled_payment_at": "2026-05-06T09:00:00Z",
          "bank_reference": "REF-300301",
          "risk_flags": [
            "new_supplier",
            "high_value"
          ]
        },
        "metadata": {
          "connector": "mock_debezium_style",
          "database": "approvalmax_payments",
          "lsn": 300301,
          "tx_id": "TX-030301",
          "is_snapshot": false,
          "schema_registry_subject": "payments-value-v2"
        }
      }
    ]
  },
  "suppliers": {
    "candidate_business_key": "supplier_id",
    "candidate_silver_table": "suppliers_current",
    "candidate_gold_tables": [
      "dim_supplier"
    ],
    "human_review_required": true,
    "files": [
      "sample_data/approvalmax_cdc/test_supplier_new_context_20260504.jsonl"
    ],
    "sample_records": [
      {
        "schema": "approvalmax_cdc_v1",
        "source_system": "approvalmax_mock_cdc",
        "source_table": "suppliers",
        "op": "c",
        "sequence_id": 200201,
        "event_timestamp": "2026-05-04T21:56:00Z",
        "ingestion_timestamp": "2026-05-04T21:56:20Z",
        "primary_key": {
          "supplier_id": "SUP-002",
          "company_id": "COMP-002"
        },
        "before": {},
        "after": {
          "supplier_id": "SUP-002",
          "company_id": "COMP-002",
          "supplier_name": "Demo Office Supplies",
          "status": "active",
          "country": "GB"
        },
        "metadata": {
          "connector": "mock_debezium_style",
          "database": "approvalmax_operational",
          "lsn": 200201,
          "tx_id": "TX-020201",
          "is_snapshot": false
        }
      }
    ]
  },
  "vendor_contracts": {
    "candidate_business_key": "vendor_contract_id",
    "candidate_silver_table": "vendor_contracts_current",
    "candidate_gold_tables": [
      "dim_vendor_contract"
    ],
    "human_review_required": true,
    "files": [
      "sample_data/approvalmax_cdc/schema_evolution_vendor_contracts_20260504.jsonl"
    ],
    "sample_records": [
      {
        "schema": "approvalmax_contracts_cdc_v3",
        "source_system": "approvalmax_mock_contract_service",
        "source_table": "vendor_contracts",
        "op": "u",
        "sequence_id": 300501,
        "event_timestamp": "2026-05-04T22:29:00Z",
        "ingestion_timestamp": "2026-05-04T22:29:20Z",
        "primary_key": {
          "vendor_contract_id": "VC-003",
          "company_id": "COMP-003"
        },
        "before": {
          "contract_status": "draft"
        },
        "after": {
          "vendor_contract_id": "VC-003",
          "company_id": "COMP-003",
          "supplier_id": "SUP-003",
          "contract_status": "approved",
          "contract_type": "software_subscription",
          "annual_value": 14400.0,
          "currency": "GBP",
          "effective_from": "2026-05-01",
          "effective_to": "2027-04-30",
          "renewal_terms": {
            "auto_renew": false,
            "notice_days": 60
          },
          "approval_document_id": "INV-003"
        },
        "metadata": {
          "connector": "mock_debezium_style",
          "database": "approvalmax_contracts",
          "lsn": 300501,
          "tx_id": "TX-030501",
          "is_snapshot": false,
          "schema_version": "contract_v3",
          "source_partition": 4
        }
      }
    ]
  }
}
```

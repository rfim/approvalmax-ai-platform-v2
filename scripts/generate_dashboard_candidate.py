#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DASHBOARD_DIR = Path("src/dashboards")
RESOURCE_DIR = Path("resources/dashboard_candidates")
DOC_DIR = Path("docs/recovery")


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned or not re.match(r"^[a-zA-Z_]", cleaned):
        raise ValueError(f"Unsafe identifier: {value!r}")
    return cleaned


def dashboard_json(client_id: str, display_name: str) -> dict:
    title = f"{display_name} Operations"
    return {
        "datasets": [
            {
                "name": "document_summary",
                "displayName": "Document Summary",
                "queryLines": [
                    "SELECT ",
                    "  COUNT(*) AS document_count, ",
                    "  AVG(approval_cycle_time_minutes) AS avg_approval_cycle_time_minutes, ",
                    "  SUM(approval_sla_breach_flag) AS sla_breach_count ",
                    "FROM approvalmax_ai_platform.gold.fact_approval_document_lifecycle ",
                ],
            },
            {
                "name": "documents_by_status",
                "displayName": "Documents by Status",
                "queryLines": [
                    "SELECT ",
                    "  document_status, ",
                    "  COUNT(*) AS document_count ",
                    "FROM approvalmax_ai_platform.gold.fact_approval_document_lifecycle ",
                    "GROUP BY document_status ",
                    "ORDER BY document_count DESC ",
                ],
            },
            {
                "name": "quality_status",
                "displayName": "Quality Status",
                "queryLines": [
                    "SELECT ",
                    "  expectation_name, ",
                    "  status, ",
                    "  severity, ",
                    "  failed_row_count, ",
                    "  checked_at ",
                    "FROM approvalmax_ai_platform.monitoring.dashboard_quality_status ",
                    "ORDER BY checked_at DESC ",
                    "LIMIT 20 ",
                ],
            },
        ],
        "pages": [
            {
                "name": "overview",
                "displayName": "Overview",
                "pageType": "PAGE_TYPE_CANVAS",
                "layout": [
                    {
                        "widget": {
                            "name": "title",
                            "multilineTextboxSpec": {"lines": [f"## {title}"]},
                        },
                        "position": {"x": 0, "y": 0, "width": 6, "height": 1},
                    },
                    {
                        "widget": {
                            "name": "subtitle",
                            "multilineTextboxSpec": {
                                "lines": [
                                    "Review candidate dashboard. Queries use reviewed Gold and monitoring tables only."
                                ]
                            },
                        },
                        "position": {"x": 0, "y": 1, "width": 6, "height": 1},
                    },
                    counter_widget("document-count", "document_summary", "document_count", "Documents", 0, 2),
                    counter_widget(
                        "avg-cycle-time",
                        "document_summary",
                        "avg_approval_cycle_time_minutes",
                        "Avg Cycle Minutes",
                        2,
                        2,
                    ),
                    counter_widget("sla-breaches", "document_summary", "sla_breach_count", "SLA Breaches", 4, 2),
                    {
                        "widget": {
                            "name": "status-chart",
                            "queries": [
                                {
                                    "name": "main_query",
                                    "query": {
                                        "datasetName": "documents_by_status",
                                        "fields": [
                                            {"name": "document_status", "expression": "`document_status`"},
                                            {"name": "document_count", "expression": "`document_count`"},
                                        ],
                                        "disaggregated": True,
                                    },
                                }
                            ],
                            "spec": {
                                "version": 3,
                                "widgetType": "bar",
                                "encodings": {
                                    "x": {
                                        "fieldName": "document_status",
                                        "scale": {"type": "categorical"},
                                        "displayName": "Status",
                                    },
                                    "y": {
                                        "fieldName": "document_count",
                                        "scale": {"type": "quantitative"},
                                        "displayName": "Documents",
                                    },
                                },
                                "frame": {"title": "Documents by Status", "showTitle": True},
                            },
                        },
                        "position": {"x": 0, "y": 5, "width": 6, "height": 5},
                    },
                    {
                        "widget": {
                            "name": "quality-table",
                            "queries": [
                                {
                                    "name": "main_query",
                                    "query": {
                                        "datasetName": "quality_status",
                                        "fields": [
                                            {"name": "expectation_name", "expression": "`expectation_name`"},
                                            {"name": "status", "expression": "`status`"},
                                            {"name": "severity", "expression": "`severity`"},
                                            {"name": "failed_row_count", "expression": "`failed_row_count`"},
                                            {"name": "checked_at", "expression": "`checked_at`"},
                                        ],
                                        "disaggregated": True,
                                    },
                                }
                            ],
                            "spec": {
                                "version": 2,
                                "widgetType": "table",
                                "encodings": {
                                    "columns": [
                                        {"fieldName": "expectation_name", "displayName": "Expectation"},
                                        {"fieldName": "status", "displayName": "Status"},
                                        {"fieldName": "severity", "displayName": "Severity"},
                                        {"fieldName": "failed_row_count", "displayName": "Failed Rows"},
                                        {"fieldName": "checked_at", "displayName": "Checked At"},
                                    ]
                                },
                                "frame": {"title": "Quality Status", "showTitle": True},
                            },
                        },
                        "position": {"x": 0, "y": 10, "width": 6, "height": 6},
                    },
                ],
            }
        ],
    }


def counter_widget(name: str, dataset: str, field: str, title: str, x: int, y: int) -> dict:
    return {
        "widget": {
            "name": name,
            "queries": [
                {
                    "name": "main_query",
                    "query": {
                        "datasetName": dataset,
                        "fields": [{"name": field, "expression": f"`{field}`"}],
                        "disaggregated": True,
                    },
                }
            ],
            "spec": {
                "version": 2,
                "widgetType": "counter",
                "encodings": {"value": {"fieldName": field, "displayName": title}},
                "frame": {"title": title, "showTitle": True},
            },
        },
        "position": {"x": x, "y": y, "width": 2, "height": 3},
    }


def write_candidate(change: dict) -> dict:
    client_id = safe_id(change["client_id"])
    dashboard_request = change.get("dashboard_request") or {}
    dashboard_type = safe_id(str(dashboard_request.get("dashboard_type", "client_operations")))
    slug = f"{client_id}_{dashboard_type}"
    display_name = change.get("display_name", client_id)

    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    RESOURCE_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)

    dashboard_path = DASHBOARD_DIR / f"{slug}.lvdash.json"
    resource_path = RESOURCE_DIR / f"{slug}.dashboard.yml"
    doc_path = DOC_DIR / f"{slug}_dashboard_candidate.md"

    dashboard_path.write_text(json.dumps(dashboard_json(client_id, display_name), indent=2), encoding="utf-8")
    resource_path.write_text(
        f"""# Candidate resource. Move to resources/ after dashboard SQL and permissions are reviewed.
resources:
  dashboards:
    {slug}:
      display_name: "[${{bundle.target}}] {display_name} Operations"
      file_path: ../../src/dashboards/{slug}.lvdash.json
      warehouse_id: "${{var.dashboard_warehouse_id}}"
""",
        encoding="utf-8",
    )
    doc_path.write_text(
        f"""# Dashboard Candidate: {display_name}

Client: `{client_id}`

Dashboard type: `{dashboard_type}`

This candidate uses reviewed Gold and monitoring tables only:

- `approvalmax_ai_platform.gold.fact_approval_document_lifecycle`
- `approvalmax_ai_platform.monitoring.dashboard_quality_status`

Human review checklist:

- [ ] Confirm the client dashboard grain.
- [ ] Confirm requested metrics do not redefine financial measures.
- [ ] Test every dashboard SQL query in Databricks SQL before deployment.
- [ ] Confirm Unity Catalog permissions, row filters, and tenant visibility.
- [ ] Move the candidate resource into the deployed bundle resource path only after approval.
""",
        encoding="utf-8",
    )
    return {
        "client_id": client_id,
        "dashboard_type": dashboard_type,
        "dashboard_path": str(dashboard_path),
        "resource_path": str(resource_path),
        "doc_path": str(doc_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="recovery/client_integration_change_request.json")
    parser.add_argument("--manifest", default="recovery/dashboard_candidates.json")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    candidates = [
        write_candidate(change)
        for change in payload.get("changes", [])
        if (change.get("dashboard_request") or {}).get("required")
    ]
    Path(args.manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.manifest).write_text(json.dumps({"candidates": candidates}, indent=2), encoding="utf-8")
    print(f"Generated dashboard candidates: {len(candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

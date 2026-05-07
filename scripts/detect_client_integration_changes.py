#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


REQUEST_DIR = Path("sample_data/client_change_requests")
CLIENT_REGISTRY_PATH = Path("metadata/client_integrations.yml")
CDC_REGISTRY_PATH = Path("metadata/supported_cdc_contexts.yml")
OUTPUT_PATH = Path("recovery/client_integration_change_request.json")
REQUIRED_REQUEST_FIELDS = {"request_id", "client_id", "display_name", "request_type", "contexts"}
ALLOWED_REQUEST_TYPES = {
    "new_client",
    "feature_added",
    "feature_removed",
    "schema_changed",
    "context_added",
    "context_removed",
}
REQUIRED_CONTEXT_FIELDS = {"source_table", "schema_version", "business_key", "features"}


def parse_scalar(value: str) -> Any:
    value = value.strip().strip("'\"")
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() in {"null", "none"}:
        return None
    return value


def load_yaml(path: Path, root_key: str) -> dict:
    if not path.exists():
        return {root_key: {}}
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {root_key: {}}

    # Small fallback parser for the simple registry shapes used in this repo.
    root: dict[str, dict] = {root_key: {}}
    stack: list[tuple[int, dict | list]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if stripped.startswith("- ") and isinstance(parent, list):
            parent.append(parse_scalar(stripped[2:]))
            continue
        if ":" not in stripped or not isinstance(parent, dict):
            continue
        key, value = stripped.split(":", 1)
        if value.strip():
            parent[key] = parse_scalar(value)
            continue
        child: dict = {}
        parent[key] = child
        stack.append((indent, child))
    return root


def read_requests() -> list[dict]:
    requests: list[dict] = []
    for path in sorted(REQUEST_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    item.setdefault("_request_file", str(path))
                    requests.append(item)
        elif isinstance(payload, dict):
            payload.setdefault("_request_file", str(path))
            requests.append(payload)
    return requests


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned or not re.match(r"^[a-zA-Z_]", cleaned):
        raise ValueError(f"Unsafe identifier: {value!r}")
    return cleaned


def severity(has_critical: bool, has_warning: bool) -> str:
    if has_critical:
        return "failed"
    if has_warning:
        return "warning"
    return "passed"


def evaluate_request_quality(request: dict, clients: dict, supported_contexts: dict) -> dict:
    checks: list[dict[str, Any]] = []

    def add_check(name: str, status: str, severity_level: str, details: str) -> None:
        checks.append(
            {
                "name": name,
                "status": status,
                "severity": severity_level,
                "details": details,
            }
        )

    missing_fields = sorted(REQUIRED_REQUEST_FIELDS - set(request.keys()))
    add_check(
        "request_required_fields_present",
        "failed" if missing_fields else "passed",
        "critical" if missing_fields else "info",
        f"Missing fields: {', '.join(missing_fields)}" if missing_fields else "All required request fields are present.",
    )

    request_type = request.get("request_type")
    add_check(
        "request_type_supported",
        "passed" if request_type in ALLOWED_REQUEST_TYPES else "failed",
        "critical" if request_type not in ALLOWED_REQUEST_TYPES else "info",
        f"request_type={request_type!r}",
    )

    client_id = safe_id(str(request.get("client_id", "missing_client_id")))
    client_exists = client_id in clients
    if request_type == "new_client":
        status = "passed" if not client_exists else "warning"
        add_check(
            "new_client_not_already_active",
            status,
            "warning" if client_exists else "info",
            "Client already exists in metadata/client_integrations.yml." if client_exists else "Client does not already exist.",
        )

    contexts = request.get("contexts") or []
    source_tables = [safe_id(str(context.get("source_table", ""))) for context in contexts if context.get("source_table")]
    duplicate_contexts = sorted({context for context in source_tables if source_tables.count(context) > 1})
    add_check(
        "request_contexts_unique",
        "failed" if duplicate_contexts else "passed",
        "critical" if duplicate_contexts else "info",
        f"Duplicate source_table values: {', '.join(duplicate_contexts)}" if duplicate_contexts else "No duplicate source_table values.",
    )

    for index, context in enumerate(contexts, start=1):
        source_table = safe_id(str(context.get("source_table", f"context_{index}")))
        missing_context_fields = sorted(REQUIRED_CONTEXT_FIELDS - set(context.keys()))
        add_check(
            f"{source_table}_context_required_fields_present",
            "failed" if missing_context_fields else "passed",
            "critical" if missing_context_fields else "info",
            f"Missing fields: {', '.join(missing_context_fields)}"
            if missing_context_fields
            else "All required context fields are present.",
        )

        approved = supported_contexts.get(source_table)
        requested_key = context.get("business_key")
        approved_key = approved.get("business_key") if isinstance(approved, dict) else None
        if approved_key and requested_key:
            add_check(
                f"{source_table}_business_key_matches_registry",
                "passed" if approved_key == requested_key else "failed",
                "critical" if approved_key != requested_key else "info",
                f"requested={requested_key!r}, registry={approved_key!r}",
            )
        elif requested_key:
            add_check(
                f"{source_table}_business_key_candidate_present",
                "passed",
                "warning",
                f"Candidate business key {requested_key!r}; context is not approved in registry.",
            )
        else:
            add_check(
                f"{source_table}_business_key_present",
                "failed",
                "critical",
                "No requested business key was supplied.",
            )

        features = context.get("features") or {}
        if isinstance(features, dict):
            removed_features = sorted(name for name, enabled in features.items() if enabled is False)
            add_check(
                f"{source_table}_feature_removal_review",
                "warning" if removed_features else "passed",
                "warning" if removed_features else "info",
                f"Disabled features require compatibility review: {', '.join(removed_features)}"
                if removed_features
                else "No feature removals requested for this context.",
            )
        else:
            add_check(
                f"{source_table}_features_shape_valid",
                "failed",
                "critical",
                "features must be an object of feature_name: boolean.",
            )

    dashboard_request = request.get("dashboard_request") or {}
    if dashboard_request.get("required"):
        dashboard_tables = dashboard_request.get("primary_tables") or []
        invalid_tables = [
            table
            for table in dashboard_tables
            if not str(table).startswith("approvalmax_ai_platform.gold.")
            and not str(table).startswith("approvalmax_ai_platform.monitoring.")
        ]
        add_check(
            "dashboard_sources_are_curated",
            "failed" if invalid_tables else "passed",
            "critical" if invalid_tables else "info",
            f"Invalid dashboard source tables: {', '.join(invalid_tables)}"
            if invalid_tables
            else "Dashboard uses Gold or monitoring tables only.",
        )
        metrics = dashboard_request.get("requested_metrics") or []
        add_check(
            "dashboard_metrics_declared",
            "passed" if metrics else "failed",
            "critical" if not metrics else "info",
            f"Requested metrics: {', '.join(metrics)}" if metrics else "No requested dashboard metrics supplied.",
        )

    app_request = request.get("app_request") or {}
    if app_request.get("required"):
        framework = app_request.get("framework")
        add_check(
            "app_framework_supported",
            "passed" if framework in {"streamlit"} else "failed",
            "critical" if framework not in {"streamlit"} else "info",
            f"framework={framework!r}; current generator supports streamlit.",
        )
        app_tables = app_request.get("primary_tables") or []
        invalid_tables = [
            table
            for table in app_tables
            if not str(table).startswith("approvalmax_ai_platform.gold.")
            and not str(table).startswith("approvalmax_ai_platform.monitoring.")
        ]
        add_check(
            "app_sources_are_curated",
            "failed" if invalid_tables else "passed",
            "critical" if invalid_tables else "info",
            f"Invalid app source tables: {', '.join(invalid_tables)}"
            if invalid_tables
            else "App uses Gold or monitoring tables only.",
        )

    has_critical = any(check["status"] == "failed" and check["severity"] == "critical" for check in checks)
    has_warning = any(check["status"] == "warning" or check["severity"] == "warning" for check in checks)
    return {
        "overall_status": severity(has_critical, has_warning),
        "critical_failure_count": sum(1 for check in checks if check["status"] == "failed" and check["severity"] == "critical"),
        "warning_count": sum(1 for check in checks if check["status"] == "warning" or check["severity"] == "warning"),
        "checks": checks,
    }


def candidate_client_config(request: dict) -> dict:
    contexts = {}
    for context in request.get("contexts", []):
        source_table = safe_id(str(context["source_table"]))
        contexts[source_table] = {
            "schema_version": context.get("schema_version", "unknown"),
            "features": context.get("features", {}),
        }
        if context.get("business_key"):
            contexts[source_table]["business_key"] = context["business_key"]

    config = {
        "status": "candidate",
        "display_name": request.get("display_name", request["client_id"]),
        "enabled_contexts": contexts,
        "human_review_required": True,
        "source_request_id": request.get("request_id"),
    }
    dashboard_request = request.get("dashboard_request") or {}
    if dashboard_request.get("required"):
        dashboard_type = safe_id(str(dashboard_request.get("dashboard_type", "client_operations")))
        config["dashboards"] = {
            dashboard_type: {
                "status": "candidate",
                "grain": dashboard_request.get("grain"),
                "source_tables": dashboard_request.get("primary_tables", []),
                "requested_metrics": dashboard_request.get("requested_metrics", []),
                "human_review_required": True,
            }
        }
    app_request = request.get("app_request") or {}
    if app_request.get("required"):
        app_type = safe_id(str(app_request.get("app_type", "client_operations")))
        config["apps"] = {
            app_type: {
                "status": "candidate",
                "framework": app_request.get("framework", "streamlit"),
                "source_tables": app_request.get("primary_tables", []),
                "human_review_required": True,
            }
        }
    return config


def detect_request(request: dict, clients: dict, supported_contexts: dict) -> dict:
    client_id = safe_id(str(request["client_id"]))
    existing_client = clients.get(client_id, {})
    existing_contexts = existing_client.get("enabled_contexts", {}) if isinstance(existing_client, dict) else {}
    existing_dashboards = existing_client.get("dashboards", {}) if isinstance(existing_client, dict) else {}
    existing_apps = existing_client.get("apps", {}) if isinstance(existing_client, dict) else {}
    actions: list[str] = []
    unknown_contexts: list[dict] = []
    context_changes: list[dict] = []

    if client_id not in clients:
        actions.append("new_client")

    if request.get("request_type") in {"feature_added", "feature_removed", "schema_changed", "context_added", "context_removed"}:
        actions.append(str(request["request_type"]))

    for context in request.get("contexts", []):
        source_table = safe_id(str(context["source_table"]))
        supported = supported_contexts.get(source_table)
        if source_table not in existing_contexts:
            context_changes.append({"source_table": source_table, "change": "context_added"})
        else:
            old_version = existing_contexts.get(source_table, {}).get("schema_version")
            new_version = context.get("schema_version")
            if old_version and new_version and old_version != new_version:
                context_changes.append(
                    {
                        "source_table": source_table,
                        "change": "schema_changed",
                        "old_schema_version": old_version,
                        "new_schema_version": new_version,
                    }
                )
        if source_table not in supported_contexts:
            unknown_contexts.append(
                {
                    "source_table": source_table,
                    "candidate_business_key": context.get("business_key"),
                    "human_review_required": True,
                    "reason": "source_table is not in metadata/supported_cdc_contexts.yml",
                }
            )
        elif isinstance(supported, dict) and supported.get("business_key") and context.get("business_key"):
            if supported["business_key"] != context["business_key"]:
                context_changes.append(
                    {
                        "source_table": source_table,
                        "change": "business_key_mismatch",
                        "approved_business_key": supported["business_key"],
                        "requested_business_key": context["business_key"],
                        "human_review_required": True,
                    }
                )

    if context_changes:
        actions.append("context_or_schema_change")
    if unknown_contexts:
        actions.append("unknown_cdc_context")
    dashboard_request = request.get("dashboard_request") or {}
    dashboard_type = safe_id(str(dashboard_request.get("dashboard_type", "client_operations")))
    if dashboard_request.get("required") and dashboard_type not in existing_dashboards:
        actions.append("dashboard_candidate_requested")

    app_request = request.get("app_request") or {}
    app_type = safe_id(str(app_request.get("app_type", "client_operations")))
    if app_request.get("required") and app_type not in existing_apps:
        actions.append("app_candidate_requested")

    quality_evaluation = evaluate_request_quality(request, clients, supported_contexts)
    return {
        "request_id": request.get("request_id", client_id),
        "request_file": request.get("_request_file"),
        "client_id": client_id,
        "display_name": request.get("display_name", client_id),
        "request_type": request.get("request_type"),
        "required_actions": sorted(set(actions)),
        "context_changes": context_changes,
        "unknown_contexts": unknown_contexts,
        "candidate_client_config": candidate_client_config(request),
        "dashboard_request": request.get("dashboard_request", {}),
        "app_request": request.get("app_request", {}),
        "quality_evaluation": quality_evaluation,
        "human_review_required": True,
    }


def main() -> int:
    client_registry = load_yaml(CLIENT_REGISTRY_PATH, "clients")
    cdc_registry = load_yaml(CDC_REGISTRY_PATH, "supported_contexts")
    clients = client_registry.get("clients") or {}
    supported_contexts = cdc_registry.get("supported_contexts") or {}
    requests = read_requests()

    changes = [
        detect_request(request, clients, supported_contexts)
        for request in requests
        if request.get("client_id")
    ]
    changes = [change for change in changes if change["required_actions"]]
    critical_failures = sum(change["quality_evaluation"]["critical_failure_count"] for change in changes)
    warnings = sum(change["quality_evaluation"]["warning_count"] for change in changes)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "change_count": len(changes),
                "changes": changes,
                "quality_gate": {
                    "status": "failed" if critical_failures else "warning" if warnings else "passed",
                    "critical_failure_count": critical_failures,
                    "warning_count": warnings,
                    "review_required": bool(changes),
                },
                "safety": {
                    "auto_merge": False,
                    "business_key_changes_require_review": True,
                    "financial_metric_changes_allowed": False,
                    "dashboard_publish_allowed": False,
                    "app_deploy_allowed": False,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Client integration change requests: {len(requests)}")
    print(f"Reviewable changes detected: {len(changes)}")
    return 10 if changes else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


APP_DIR = Path("src/apps")
RESOURCE_DIR = Path("resources/app_candidates")
DOC_DIR = Path("docs/recovery")
CLIENT_REGISTRY_PATH = Path("metadata/client_integrations.yml")


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned or not re.match(r"^[a-zA-Z_]", cleaned):
        raise ValueError(f"Unsafe identifier: {value!r}")
    return cleaned


def safe_app_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9-]+", "-", value.strip().lower().replace("_", "-"))
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    if not cleaned:
        raise ValueError(f"Unsafe app name: {value!r}")
    return cleaned[:60]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {"clients": {}}
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {"clients": {}}

    root: dict[str, dict] = {"clients": {}}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#") or raw_line.lstrip().startswith("- "):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if value.strip():
            parent[key] = value.strip().strip("'\"")
            continue
        child: dict = {}
        parent[key] = child
        stack.append((indent, child))
    return root


def load_changes(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("changes", [])


def connected_clients(registry: dict, changes: list[dict[str, Any]], include_active: bool) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    if include_active:
        for client_id, config in (registry.get("clients") or {}).items():
            if not isinstance(config, dict) or config.get("status") not in {"active", "candidate"}:
                continue
            apps = config.get("apps") or {}
            if apps:
                app_type, app_config = next(iter(apps.items())) if isinstance(apps, dict) else ("client_operations", {})
                app_request = dict(app_config or {})
                app_request.setdefault("app_type", app_type)
                selected[safe_id(client_id)] = {
                    "client_id": safe_id(client_id),
                    "display_name": config.get("display_name", client_id),
                    "app_request": app_request,
                }

    for change in changes:
        app_request = change.get("app_request") or {}
        if app_request.get("required"):
            selected[safe_id(change["client_id"])] = {
                "client_id": safe_id(change["client_id"]),
                "display_name": change.get("display_name", change["client_id"]),
                "app_request": app_request,
            }
    return list(selected.values())


def app_py(client_id: str, display_name: str) -> str:
    return f'''import os

import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config


CLIENT_ID = os.getenv("CLIENT_ID", "{client_id}")
CLIENT_DISPLAY_NAME = os.getenv("CLIENT_DISPLAY_NAME", "{display_name}")
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")
USE_MOCK = os.getenv("USE_MOCK_BACKEND", "false").lower() == "true"


st.set_page_config(page_title=f"{{CLIENT_DISPLAY_NAME}} Operations", layout="wide")


@st.cache_resource
def get_connection():
    if USE_MOCK or not WAREHOUSE_ID:
        return None
    cfg = Config()
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{{WAREHOUSE_ID}}",
        credentials_provider=lambda: cfg.authenticate,
    )


@st.cache_data(ttl=300)
def query(sql_text: str) -> pd.DataFrame:
    conn = get_connection()
    if conn is None:
        return mock_data(sql_text)
    with conn.cursor() as cursor:
        cursor.execute(sql_text)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def mock_data(sql_text: str) -> pd.DataFrame:
    if "GROUP BY document_status" in sql_text:
        return pd.DataFrame(
            [
                {{"document_status": "approved", "document_count": 24}},
                {{"document_status": "submitted", "document_count": 7}},
                {{"document_status": "rejected", "document_count": 2}},
            ]
        )
    if "dashboard_quality_status" in sql_text:
        return pd.DataFrame(
            [
                {{"expectation_name": "document_id_not_null", "status": "passed", "severity": "critical", "failed_row_count": 0}},
                {{"expectation_name": "gold_grain_unique", "status": "passed", "severity": "critical", "failed_row_count": 0}},
            ]
        )
    return pd.DataFrame(
        [{{"document_count": 33, "avg_approval_cycle_time_minutes": 41.5, "sla_breach_count": 1}}]
    )


summary_sql = """
SELECT
  COUNT(*) AS document_count,
  AVG(approval_cycle_time_minutes) AS avg_approval_cycle_time_minutes,
  SUM(approval_sla_breach_flag) AS sla_breach_count
FROM approvalmax_ai_platform.gold.fact_approval_document_lifecycle
"""

status_sql = """
SELECT
  document_status,
  COUNT(*) AS document_count
FROM approvalmax_ai_platform.gold.fact_approval_document_lifecycle
GROUP BY document_status
ORDER BY document_count DESC
"""

quality_sql = """
SELECT
  expectation_name,
  status,
  severity,
  failed_row_count
FROM approvalmax_ai_platform.monitoring.dashboard_quality_status
ORDER BY checked_at DESC
LIMIT 20
"""


st.title(f"{{CLIENT_DISPLAY_NAME}} Operations")
st.caption(f"Client id: {{CLIENT_ID}}")

summary = query(summary_sql)
status = query(status_sql)
quality = query(quality_sql)

if not summary.empty:
    row = summary.iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Documents", int(row.get("document_count") or 0))
    c2.metric("Avg cycle minutes", round(float(row.get("avg_approval_cycle_time_minutes") or 0), 1))
    c3.metric("SLA breaches", int(row.get("sla_breach_count") or 0))

st.subheader("Documents by status")
if not status.empty:
    st.bar_chart(status.set_index("document_status"))
else:
    st.info("No document status data available.")

st.subheader("Quality status")
st.dataframe(quality, use_container_width=True)
'''


def app_yaml(client_id: str, display_name: str) -> str:
    return f'''command:
  - streamlit
  - run
  - app.py

env:
  - name: DATABRICKS_WAREHOUSE_ID
    valueFrom: sql-warehouse
  - name: CLIENT_ID
    value: "{client_id}"
  - name: CLIENT_DISPLAY_NAME
    value: "{display_name}"
  - name: USE_MOCK_BACKEND
    value: "false"
'''


def write_candidate(client: dict[str, Any]) -> dict[str, str]:
    client_id = safe_id(client["client_id"])
    display_name = str(client.get("display_name", client_id))
    app_type = safe_id(str((client.get("app_request") or {}).get("app_type", "client_operations")))
    slug = f"{client_id}_{app_type}_app"
    app_name = safe_app_name(f"approvalmax-{client_id}-{app_type}")
    app_path = APP_DIR / slug
    resource_path = RESOURCE_DIR / f"{slug}.app.yml"
    doc_path = DOC_DIR / f"{slug}_candidate.md"

    app_path.mkdir(parents=True, exist_ok=True)
    RESOURCE_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)

    (app_path / "app.py").write_text(app_py(client_id, display_name), encoding="utf-8")
    (app_path / "app.yaml").write_text(app_yaml(client_id, display_name), encoding="utf-8")
    (app_path / "requirements.txt").write_text(
        "databricks-sdk\n"
        "databricks-sql-connector\n"
        "pandas\n",
        encoding="utf-8",
    )
    (app_path / "README.md").write_text(
        f"""# {display_name} Operations App

Candidate Databricks App for `{client_id}`.

The app uses Streamlit, Databricks app authentication, and a SQL warehouse resource supplied through `app.yaml` `valueFrom`.

Review before deployment:

- Confirm tenant/client visibility rules.
- Confirm Unity Catalog grants, row filters, and column masks.
- Confirm the SQL warehouse resource binding.
- Confirm no financial metrics are redefined.
""",
        encoding="utf-8",
    )
    resource_path.write_text(
        f"""# Candidate resource. Move to resources/ after app SQL, permissions, and tenant isolation are reviewed.
resources:
  apps:
    {slug}:
      name: {app_name}-${{bundle.target}}
      description: "{display_name} operations app"
      source_code_path: ../../src/apps/{slug}
""",
        encoding="utf-8",
    )
    doc_path.write_text(
        f"""# Databricks App Candidate: {display_name}

Client: `{client_id}`

App type: `{app_type}`

Generated files:

- `src/apps/{slug}/app.py`
- `src/apps/{slug}/app.yaml`
- `src/apps/{slug}/requirements.txt`
- `resources/app_candidates/{slug}.app.yml`

Human review checklist:

- [ ] Confirm this client should receive a Databricks App.
- [ ] Confirm Unity Catalog permissions, row filters, and tenant visibility.
- [ ] Confirm SQL warehouse resource binding in the Databricks Apps UI or bundle resource.
- [ ] Confirm no financial metrics are redefined.
- [ ] Move the candidate app resource into the deployed bundle resource path only after approval.
""",
        encoding="utf-8",
    )
    return {
        "client_id": client_id,
        "app_type": app_type,
        "app_path": str(app_path),
        "resource_path": str(resource_path),
        "doc_path": str(doc_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="recovery/client_integration_change_request.json")
    parser.add_argument("--manifest", default="recovery/client_app_candidates.json")
    parser.add_argument("--include-active", action="store_true")
    args = parser.parse_args()

    registry = load_yaml(CLIENT_REGISTRY_PATH) if args.include_active else {"clients": {}}
    changes = load_changes(Path(args.input))
    clients = connected_clients(registry, changes, args.include_active)
    candidates = [write_candidate(client) for client in clients]

    Path(args.manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.manifest).write_text(json.dumps({"candidates": candidates}, indent=2), encoding="utf-8")
    print(f"Generated Databricks App candidates: {len(candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

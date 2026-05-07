import os

import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config


CLIENT_ID = os.getenv("CLIENT_ID", "client_quality_evidence_probe")
CLIENT_DISPLAY_NAME = os.getenv("CLIENT_DISPLAY_NAME", "Quality Evidence Probe")
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")
USE_MOCK = os.getenv("USE_MOCK_BACKEND", "false").lower() == "true"


st.set_page_config(page_title=f"{CLIENT_DISPLAY_NAME} Operations", layout="wide")


@st.cache_resource
def get_connection():
    if USE_MOCK or not WAREHOUSE_ID:
        return None
    cfg = Config()
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
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
                {"document_status": "approved", "document_count": 24},
                {"document_status": "submitted", "document_count": 7},
                {"document_status": "rejected", "document_count": 2},
            ]
        )
    if "dashboard_quality_status" in sql_text:
        return pd.DataFrame(
            [
                {"expectation_name": "document_id_not_null", "status": "passed", "severity": "critical", "failed_row_count": 0},
                {"expectation_name": "gold_grain_unique", "status": "passed", "severity": "critical", "failed_row_count": 0},
            ]
        )
    return pd.DataFrame(
        [{"document_count": 33, "avg_approval_cycle_time_minutes": 41.5, "sla_breach_count": 1}]
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


st.title(f"{CLIENT_DISPLAY_NAME} Operations")
st.caption(f"Client id: {CLIENT_ID}")

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

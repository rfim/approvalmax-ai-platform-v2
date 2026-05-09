#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - workflow installs pyyaml
    yaml = None


REGISTRY_PATH = Path("metadata/supported_cdc_contexts.yml")
MODEL_DIR = Path("models/gold/generated")
DOC_PATH = Path("docs/recovery/approved_cdc_dbt_models.md")
MANIFEST_PATH = Path("recovery/approved_cdc_dbt_models.json")
APPROVED_STATUSES = {
    "approved",
    "approved_for_modeling",
    "approved_for_modelling",
    "ready_for_dbt",
}


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {"supported_contexts": {}}
    return parse_yaml(path.read_text(encoding="utf-8"))


def load_previous_registry(ref: str | None) -> dict:
    if not ref:
        return {"supported_contexts": {}}
    try:
        completed = subprocess.run(
            ["git", "show", f"{ref}:{REGISTRY_PATH.as_posix()}"],
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        return {"supported_contexts": {}}
    return parse_yaml(completed.stdout)


def parse_scalar(value: str):
    value = value.strip().strip("'\"")
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() in {"null", "none"}:
        return None
    return value


def parse_yaml(text: str) -> dict:
    if yaml is not None:
        return yaml.safe_load(text) or {"supported_contexts": {}}

    contexts: dict[str, dict] = {}
    current_context: str | None = None
    current_list_key: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "supported_contexts:":
            continue
        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            current_context = stripped[:-1]
            current_list_key = None
            contexts[current_context] = {}
            continue
        if not current_context or not line.startswith("    "):
            continue
        if line.startswith("    - ") and current_list_key:
            contexts[current_context].setdefault(current_list_key, []).append(parse_scalar(stripped[2:]))
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if value.strip() == "":
            current_list_key = key
            contexts[current_context][key] = []
        else:
            current_list_key = None
            contexts[current_context][key] = parse_scalar(value)

    return {"supported_contexts": contexts}


def is_approved(config: dict) -> bool:
    status = str(config.get("status", "")).strip().lower()
    if status in APPROVED_STATUSES:
        return True
    return config.get("human_review_required") is False and bool(config.get("business_key"))


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned or not re.match(r"^[a-zA-Z_]", cleaned):
        raise ValueError(f"Unsafe context name: {value!r}")
    return cleaned


def approved_contexts(current: dict, previous: dict, include_existing: bool) -> list[tuple[str, dict]]:
    current_contexts = current.get("supported_contexts") or {}
    previous_contexts = previous.get("supported_contexts") or {}
    selected: list[tuple[str, dict]] = []

    for context, config in sorted(current_contexts.items()):
        if not isinstance(config, dict) or not is_approved(config):
            continue
        previous_config = previous_contexts.get(context)
        became_approved = not isinstance(previous_config, dict) or not is_approved(previous_config)
        if include_existing or became_approved:
            selected.append((context, config))

    return selected


def render_model(context: str, business_key: str, bronze_table: str = "approvalmax_cdc_raw") -> str:
    model_name = f"{safe_name(context)}_current_dbt"
    return f"""{{{{ config(
    materialized='table',
    alias='{model_name}',
    tags=['approved_cdc_context', 'generated']
) }}}}

-- Generated after human approval of the `{context}` CDC context.
-- This model intentionally exposes a conservative current-state view from Bronze
-- raw CDC only. It does not define financial metrics or alter business keys.
with source_rows as (
    select
        primary_key['{business_key}'] as {business_key},
        primary_key,
        source_table,
        schema as cdc_schema,
        source_system,
        op,
        sequence_id,
        cast(event_timestamp as timestamp) as event_timestamp,
        cast(ingestion_timestamp as timestamp) as ingestion_timestamp,
        _loaded_at,
        _run_id,
        _raw_json as raw_cdc_payload
    from {{{{ source('bronze', 'approvalmax_cdc_raw') }}}}
    where source_table = '{context}'
      and op != 'd'
),

ranked as (
    select
        *,
        row_number() over (
            partition by {business_key}
            order by sequence_id desc, ingestion_timestamp desc
        ) as row_num
    from source_rows
    where {business_key} is not null
)

select
    {business_key},
    primary_key,
    source_table,
    cdc_schema,
    source_system,
    op,
    sequence_id,
    event_timestamp,
    ingestion_timestamp,
    _loaded_at,
    _run_id,
    raw_cdc_payload
from ranked
where row_num = 1
"""


def render_schema(contexts: list[tuple[str, dict]]) -> str:
    lines = ["version: 2", "", "models:"]
    for context, config in contexts:
        business_key = safe_name(str(config["business_key"]))
        model_name = f"{safe_name(context)}_current_dbt"
        description = (
            f"Generated dbt current-state model for approved CDC context `{context}`. "
            "Uses Bronze raw CDC and preserves payloads for human-reviewed modelling."
        )
        lines.extend(
            [
                f"  - name: {model_name}",
                f"    description: {json.dumps(description)}",
                "    columns:",
                f"      - name: {business_key}",
                "        tests:",
                "          - not_null",
                "          - unique",
                "      - name: source_table",
                "        tests:",
                "          - not_null",
                "      - name: sequence_id",
                "        tests:",
                "          - not_null",
                "      - name: raw_cdc_payload",
                "        tests:",
                "          - not_null",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def render_doc(contexts: list[tuple[str, dict]]) -> str:
    lines = [
        "# Approved CDC dbt Models",
        "",
        "These files were generated after human approval of CDC context metadata.",
        "The generated dbt models are conservative current-state views over Bronze raw CDC.",
        "Great Expectations-style validation dynamically discovers generated `*_current_dbt` Gold tables.",
        "They do not redefine financial metrics, change secrets, or change business keys.",
        "",
        "| Context | Business key | dbt model |",
        "| --- | --- | --- |",
    ]
    for context, config in contexts:
        business_key = safe_name(str(config["business_key"]))
        lines.append(f"| `{context}` | `{business_key}` | `{safe_name(context)}_current_dbt` |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous-ref", default=None)
    parser.add_argument("--include-existing-approved", action="store_true")
    args = parser.parse_args()

    current = load_yaml(REGISTRY_PATH)
    previous = load_previous_registry(args.previous_ref)
    contexts = approved_contexts(current, previous, args.include_existing_approved)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "contexts": [
                    {
                        "source_table": context,
                        "business_key": config.get("business_key"),
                        "status": config.get("status"),
                    }
                    for context, config in contexts
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    if not contexts:
        print("No newly approved CDC contexts found.")
        return 0

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for context, config in contexts:
        business_key = safe_name(str(config["business_key"]))
        model_path = MODEL_DIR / f"{safe_name(context)}_current_dbt.sql"
        bronze_table = str(config.get("bronze_table", "approvalmax_cdc_raw"))
        model_path.write_text(render_model(context, business_key, bronze_table), encoding="utf-8")

    (MODEL_DIR / "schema.yml").write_text(render_schema(contexts), encoding="utf-8")
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(render_doc(contexts), encoding="utf-8")

    print(f"Generated dbt models for: {', '.join(context for context, _ in contexts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

CDC_DIR = Path("sample_data/approvalmax_cdc")
REGISTRY_PATH = Path("metadata/supported_cdc_contexts.yml")
OUTPUT_PATH = Path("recovery/new_cdc_contexts.json")

KNOWN_BUSINESS_KEYS = {
    "payments": "payment_id",
    "payment_batches": "payment_batch_id",
    "budgets": "budget_id",
    "expense_claims": "expense_claim_id",
    "vendor_contracts": "vendor_contract_id",
    "audit_policies": "audit_policy_id",
    "suppliers": "supplier_id",
}
REQUIRED_CDC_FIELDS = {
    "schema",
    "source_system",
    "source_table",
    "op",
    "sequence_id",
    "event_timestamp",
    "ingestion_timestamp",
    "primary_key",
}
ALLOWED_OPS = {"c", "u", "d", "r"}


def singularize(context: str) -> str:
    if context.endswith("ies"):
        return context[:-3] + "y"
    if context.endswith("ses"):
        return context[:-2]
    if context.endswith("s"):
        return context[:-1]
    return context


def load_supported_contexts() -> dict:
    if not REGISTRY_PATH.exists():
        return {"supported_contexts": {}}
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {"supported_contexts": {}}

    contexts: dict[str, dict[str, str]] = {}
    current_context: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#") or line.startswith("supported_contexts:"):
            continue
        if line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
            current_context = line.strip()[:-1]
            contexts[current_context] = {}
            continue
        if current_context and line.startswith("    ") and ":" in line:
            key, value = line.strip().split(":", 1)
            contexts[current_context][key] = value.strip().strip("'\"")
    return {"supported_contexts": contexts}


def iter_cdc_records() -> tuple[set[str], dict[str, list[dict]], dict[str, list[str]]]:
    seen_contexts: set[str] = set()
    samples_by_context: dict[str, list[dict]] = defaultdict(list)
    files_by_context: dict[str, list[str]] = defaultdict(list)

    if not CDC_DIR.exists():
        return seen_contexts, samples_by_context, files_by_context

    for path in sorted(CDC_DIR.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc

                source_table = record.get("source_table")
                if not source_table:
                    continue

                seen_contexts.add(source_table)
                if len(samples_by_context[source_table]) < 3:
                    samples_by_context[source_table].append(record)
                if str(path) not in files_by_context[source_table]:
                    files_by_context[source_table].append(str(path))

    return seen_contexts, samples_by_context, files_by_context


def infer_business_key(context: str, sample_record: dict) -> str | None:
    if context in KNOWN_BUSINESS_KEYS:
        return KNOWN_BUSINESS_KEYS[context]

    after = sample_record.get("after") or {}
    primary_key = sample_record.get("primary_key") or {}
    context_specific = f"{singularize(context)}_id"
    if context_specific in primary_key or context_specific in after:
        return context_specific

    for key in primary_key:
        if key.endswith("_id") and key != "company_id":
            return key

    for key in after:
        if key.endswith("_id") and key != "company_id":
            return key

    if "company_id" in primary_key or "company_id" in after:
        return "company_id"

    return None


def value_type(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "string"


def evaluate_context_schema(context: str, records: list[dict], candidate_business_key: str | None) -> dict:
    checks = []

    def add_check(name: str, status: str, severity: str, details: str) -> None:
        checks.append({"name": name, "status": status, "severity": severity, "details": details})

    missing_by_record = []
    invalid_ops = []
    missing_business_key = 0
    field_types: dict[str, set[str]] = defaultdict(set)
    op_counts: dict[str, int] = defaultdict(int)

    for index, record in enumerate(records, start=1):
        missing = sorted(REQUIRED_CDC_FIELDS - set(record.keys()))
        if missing:
            missing_by_record.append({"sample_index": index, "missing_fields": missing})

        op = record.get("op")
        op_counts[str(op)] += 1
        if op not in ALLOWED_OPS:
            invalid_ops.append({"sample_index": index, "op": op})

        primary_key = record.get("primary_key") or {}
        after = record.get("after") or {}
        if candidate_business_key and candidate_business_key not in primary_key and candidate_business_key not in after:
            missing_business_key += 1

        for field, value in after.items():
            field_types[field].add(value_type(value))

    add_check(
        f"{context}_cdc_envelope_required_fields",
        "failed" if missing_by_record else "passed",
        "critical" if missing_by_record else "info",
        json.dumps(missing_by_record) if missing_by_record else "All sampled CDC records have required envelope fields.",
    )
    add_check(
        f"{context}_cdc_operation_values",
        "failed" if invalid_ops else "passed",
        "critical" if invalid_ops else "info",
        json.dumps(invalid_ops) if invalid_ops else f"All sampled op values are in {sorted(ALLOWED_OPS)}.",
    )
    add_check(
        f"{context}_candidate_business_key_present",
        "failed" if missing_business_key else "passed",
        "critical" if missing_business_key else "info",
        f"{missing_business_key} sampled records missing {candidate_business_key!r} in primary_key/after."
        if missing_business_key
        else f"Candidate business key {candidate_business_key!r} is present in sampled records.",
    )

    evolving_fields = {
        field: sorted(types)
        for field, types in sorted(field_types.items())
        if len(types - {"null"}) > 1
    }
    add_check(
        f"{context}_sample_schema_type_stability",
        "warning" if evolving_fields else "passed",
        "warning" if evolving_fields else "info",
        json.dumps(evolving_fields, sort_keys=True) if evolving_fields else "No conflicting non-null field types in samples.",
    )

    warnings = sum(1 for check in checks if check["status"] == "warning" or check["severity"] == "warning")
    critical = sum(1 for check in checks if check["status"] == "failed" and check["severity"] == "critical")
    return {
        "overall_status": "failed" if critical else "warning" if warnings else "passed",
        "critical_failure_count": critical,
        "warning_count": warnings,
        "operation_counts": dict(sorted(op_counts.items())),
        "after_field_types": {field: sorted(types) for field, types in sorted(field_types.items())},
        "checks": checks,
    }


def main() -> int:
    registry = load_supported_contexts()
    supported_contexts = set((registry.get("supported_contexts") or {}).keys())
    seen_contexts, samples_by_context, files_by_context = iter_cdc_records()
    new_contexts = sorted(seen_contexts - supported_contexts)

    inferred = {}
    for context in new_contexts:
        sample = samples_by_context[context][0] if samples_by_context[context] else {}
        singular = singularize(context)
        candidate_business_key = infer_business_key(context, sample)
        inferred[context] = {
            "candidate_business_key": candidate_business_key,
            "candidate_silver_table": f"{context}_current",
            "candidate_gold_tables": [f"dim_{singular}"],
            "human_review_required": True,
            "files": files_by_context.get(context, []),
            "sample_records": samples_by_context.get(context, []),
            "schema_evaluation": evaluate_context_schema(
                context,
                samples_by_context.get(context, []),
                candidate_business_key,
            ),
        }

    critical_failures = sum(item["schema_evaluation"]["critical_failure_count"] for item in inferred.values())
    warnings = sum(item["schema_evaluation"]["warning_count"] for item in inferred.values())

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "seen_contexts": sorted(seen_contexts),
                "supported_contexts": sorted(supported_contexts),
                "new_contexts": new_contexts,
                "inferred": inferred,
                "quality_gate": {
                    "status": "failed" if critical_failures else "warning" if warnings else "passed",
                    "critical_failure_count": critical_failures,
                    "warning_count": warnings,
                    "review_required": bool(new_contexts),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Seen contexts: {sorted(seen_contexts)}")
    print(f"Supported contexts: {sorted(supported_contexts)}")
    print(f"New contexts: {new_contexts}")
    print(f"Wrote: {OUTPUT_PATH}")
    return 10 if new_contexts else 0


if __name__ == "__main__":
    sys.exit(main())

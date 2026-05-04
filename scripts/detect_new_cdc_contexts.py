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


def main() -> int:
    registry = load_supported_contexts()
    supported_contexts = set((registry.get("supported_contexts") or {}).keys())
    seen_contexts, samples_by_context, files_by_context = iter_cdc_records()
    new_contexts = sorted(seen_contexts - supported_contexts)

    inferred = {}
    for context in new_contexts:
        sample = samples_by_context[context][0] if samples_by_context[context] else {}
        singular = singularize(context)
        inferred[context] = {
            "candidate_business_key": infer_business_key(context, sample),
            "candidate_silver_table": f"{context}_current",
            "candidate_gold_tables": [f"dim_{singular}"],
            "human_review_required": True,
            "files": files_by_context.get(context, []),
            "sample_records": samples_by_context.get(context, []),
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "seen_contexts": sorted(seen_contexts),
                "supported_contexts": sorted(supported_contexts),
                "new_contexts": new_contexts,
                "inferred": inferred,
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

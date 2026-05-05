#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


REGISTRY_PATH = Path("metadata/supported_cdc_contexts.yml")
DOC_PATH = Path("docs/recovery/swapi_people_context.md")


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {"supported_contexts": {}}
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {"supported_contexts": {}}

    contexts: dict[str, dict[str, object]] = {}
    current_context = None
    current_list_key = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped == "supported_contexts:":
            continue
        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            current_context = stripped[:-1]
            current_list_key = None
            contexts[current_context] = {}
            continue
        if not current_context or not line.startswith("    "):
            continue
        if line.startswith("    - ") and current_list_key:
            contexts[current_context].setdefault(current_list_key, []).append(stripped[2:])
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if not value.strip():
            current_list_key = key
            contexts[current_context][key] = []
        else:
            current_list_key = None
            contexts[current_context][key] = value.strip().strip("'\"")
    return {"supported_contexts": contexts}


def dump_registry(registry: dict) -> str:
    if yaml is not None:
        return yaml.safe_dump(registry, sort_keys=False)

    lines = ["supported_contexts:"]
    for context, config in registry.get("supported_contexts", {}).items():
        lines.append(f"  {context}:")
        for key, value in config.items():
            if isinstance(value, list):
                lines.append(f"    {key}:")
                for item in value:
                    lines.append(f"    - {item}")
            else:
                rendered = "true" if value is True else "false" if value is False else value
                lines.append(f"    {key}: {rendered}")
    return "\n".join(lines) + "\n"


def main() -> int:
    registry = load_registry()
    contexts = registry.setdefault("supported_contexts", {})
    if "swapi_people" not in contexts:
        contexts["swapi_people"] = {
            "business_key": "person_url",
            "bronze_table": "swapi_people_raw",
            "silver_table": "swapi_people_current",
            "vault_tables": ["hub_swapi_person", "sat_swapi_person_profile"],
            "gold_tables": ["dim_swapi_actor"],
            "gold_enrichment_candidates": ["dim_user_actor_enrichment"],
            "dbt_models": ["swapi_people_current_dbt"],
            "great_expectations": [
                "person_url_not_null",
                "name_not_null",
                "raw_payload_not_null",
                "person_version_grain_unique",
            ],
            "human_review_required": True,
            "status": "candidate_detected_from_swapi",
        }
        REGISTRY_PATH.write_text(dump_registry(registry), encoding="utf-8")

    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(
        """# SWAPI People Modelling Candidate

The SWAPI incremental ingestion workflow loads the top 10 records from `https://swapi.dev/api/people/?page=1` into:

`approvalmax_ai_platform.bronze.swapi_people_raw`

The records are treated as a new source context named `swapi_people`, where people are hypothetical actors for the demo.

## Proposed Modelling

| Layer | Candidate object | Notes |
| --- | --- | --- |
| Bronze | `swapi_people_raw` | Append-only raw API payload and selected attributes |
| Silver | `swapi_people_current` | Latest record by `person_url` and `edited` |
| Vault | `hub_swapi_person` | Hub keyed by `person_url` |
| Vault | `sat_swapi_person_profile` | Person profile attributes and hashdiff |
| Gold | `dim_swapi_actor` | Curated actor/person dimension |
| Gold enrichment | `dim_user_actor_enrichment` | Optional reviewed name match to existing user/document marts |
| dbt | `swapi_people_current_dbt` | Generated only after approval |
| Great Expectations | generated current-state checks | Covered by generated dbt/GE workflow after approval |

## Human Review

Required before promotion beyond Bronze:

- Confirm `person_url` as the business key.
- Confirm whether SWAPI people should be represented as actors.
- Confirm enrichment matching rules before changing existing Gold marts.
- Confirm no financial metrics are added or redefined.

To approve, update metadata:

```yaml
status: approved_for_modelling
human_review_required: false
```
""",
        encoding="utf-8",
    )
    print("Prepared SWAPI people modelling suggestion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

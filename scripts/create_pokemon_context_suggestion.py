#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


REGISTRY_PATH = Path("metadata/supported_cdc_contexts.yml")
DOC_PATH = Path("docs/recovery/pokemon_actor_context.md")


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
                    lines.append(f"      - {item}")
            else:
                rendered = "true" if value is True else "false" if value is False else value
                lines.append(f"    {key}: {rendered}")
    return "\n".join(lines) + "\n"


def main() -> int:
    registry = load_registry()
    contexts = registry.setdefault("supported_contexts", {})
    if "pokemon_actor" not in contexts:
        contexts["pokemon_actor"] = {
            "business_key": "pokemon_key",
            "bronze_table": "pokemon_actor_raw",
            "silver_table": "pokemon_actors_current",
            "vault_tables": ["hub_pokemon_actor", "sat_pokemon_actor_profile"],
            "gold_tables": ["dim_pokemon_actor", "fact_approval_document_lifecycle_pokemon_actor"],
            "gold_enrichment_candidates": ["fact_approval_document_lifecycle_pokemon_actor"],
            "dbt_models": ["pokemon_actor_current_dbt"],
            "great_expectations": [
                "pokemon_key_not_null",
                "pokemon_name_not_null",
                "raw_payload_not_null",
                "pokemon_actor_grain_unique",
            ],
            "human_review_required": True,
            "status": "candidate_detected_from_pokeapi",
        }
        REGISTRY_PATH.write_text(dump_registry(registry), encoding="utf-8")

    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(
        """# Pokemon Actor Modelling Candidate

The Pokemon incremental ingestion workflow fetches 10 random Pokemon from PokeAPI in GitHub Actions and uploads JSONL to a Unity Catalog Volume before Databricks ingestion.

Bronze target:

`approvalmax_ai_platform.bronze.pokemon_actor_raw`

## Current Automated Tables

| Layer | Object | Notes |
| --- | --- | --- |
| Bronze | `pokemon_actor_raw` | Append-only compact API payload and raw JSON |
| Silver | `pokemon_actors_current` | Latest actor profile keyed by `pokemon_key` |
| Silver | `user_pokemon_actor_bridge` | Deterministic bridge to existing `users_current` by row number |
| Gold | `dim_pokemon_actor` | Demo actor dimension |
| Gold | `fact_approval_document_lifecycle_pokemon_actor` | Non-financial enrichment of the existing lifecycle fact |

## Human Review

Required before generated dbt promotion:

- Confirm `pokemon_key` as the business key.
- Confirm Pokemon should be treated as random demo actors.
- Confirm actor assignment rules before expanding enrichment logic.
- Confirm no financial metrics are added or redefined.

To approve generated dbt/GE coverage, update metadata:

```yaml
status: approved_for_modelling
human_review_required: false
```
""",
        encoding="utf-8",
    )
    print("Prepared Pokemon actor modelling suggestion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

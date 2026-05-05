#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


POKEMON_ID_MAX = 1025


def fetch_pokemon(pokemon_id: int) -> dict:
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    request = urllib.request.Request(url, headers={"User-Agent": "approvalmax-ai-platform-v2"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload


def compact_record(payload: dict, run_id: str) -> dict:
    pokemon_id = int(payload["id"])
    types = [item["type"]["name"] for item in payload.get("types", [])]
    abilities = [item["ability"]["name"] for item in payload.get("abilities", [])]
    stats = {item["stat"]["name"]: item["base_stat"] for item in payload.get("stats", [])}
    return {
        "source_system": "pokeapi",
        "source_context": "pokemon_actor",
        "pokemon_id": pokemon_id,
        "pokemon_key": f"POKE-{pokemon_id:04d}",
        "pokemon_name": payload.get("name"),
        "base_experience": payload.get("base_experience"),
        "height": payload.get("height"),
        "weight": payload.get("weight"),
        "types_json": json.dumps(types),
        "abilities_json": json.dumps(abilities),
        "hp": stats.get("hp"),
        "attack": stats.get("attack"),
        "defense": stats.get("defense"),
        "special_attack": stats.get("special-attack"),
        "special_defense": stats.get("special-defense"),
        "speed": stats.get("speed"),
        "actor_join_key": f"POKEMON_ACTOR_{pokemon_id % 10:02d}",
        "source_url": f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}",
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "raw_json": json.dumps(payload, sort_keys=True),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", default="tmp/pokeapi_random_pokemon.jsonl")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    pokemon_ids = rng.sample(range(1, POKEMON_ID_MAX + 1), args.count)
    run_id = f"pokeapi_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for pokemon_id in pokemon_ids:
            handle.write(json.dumps(compact_record(fetch_pokemon(pokemon_id), run_id), sort_keys=True) + "\n")

    print(f"Wrote {len(pokemon_ids)} Pokemon records to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

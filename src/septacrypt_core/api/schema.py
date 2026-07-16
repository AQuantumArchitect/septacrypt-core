"""Render-state schema for game engines (Godot/Blender/custom clients)."""
from __future__ import annotations

from typing import Any, Dict, List

# Schema version bumped when payload shape changes incompatibly.
RENDER_SCHEMA_VERSION = "fledgeling.render.v1"

RENDER_STATE_DOC = """
fetch_render_state / GameSession.status payload
==============================================

{
  "schema_version": "fledgeling.render.v1",
  "meta": {
    "observer": str,              # who is viewing
    "turn": int,                  # session turn counter
    "zone": str | null,           # active zone name (ship mode)
    "global_tension": float,      # cumulant ZZ connected-correlation sum
    "current_mythos": {           # lore for nearest-pole Q3 mask
      "emoji": str, "name": str, "desc": str
    },
    "q3_mask": int,               # 0..7 nearest-pole composite
    "attention": float | null,    # remaining attention if budgeted
    "seed": int | null,
    "ledger_head": str | null,    # current stamp id if ledger enabled
  },
  "entities": {
    "<role>": {
      "raw_metrics": {
        "z_axis": float,   # -1..1 classical pole (animation)
        "radius": float,   # Bloch radius / confidence (fog = 1-radius)
        "phase_x": float,
        "phase_y": float,
      },
      "semantic": {
        "inferred_state": "active" | "latent",
        "view": "ground" | "private",
      }
    }
  },
  "narrative_log": [str, ...],    # last N story lines
  "zones": { ... } | null,        # multi-zone summary when ship mode + full=true
}
"""


def validate_render_state(payload: Dict[str, Any]) -> List[str]:
    """Return list of validation errors (empty = OK). Soft check for bots/tests."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return ["payload is not a dict"]
    if payload.get("schema_version") != RENDER_SCHEMA_VERSION:
        errors.append(f"schema_version missing or unexpected: {payload.get('schema_version')}")
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta missing")
    else:
        for key in ("observer", "turn", "global_tension", "current_mythos"):
            if key not in meta:
                errors.append(f"meta.{key} missing")
    entities = payload.get("entities")
    if not isinstance(entities, dict):
        errors.append("entities missing")
    else:
        for role, body in entities.items():
            if "raw_metrics" not in body or "semantic" not in body:
                errors.append(f"entities.{role} incomplete")
            else:
                for k in ("z_axis", "radius", "phase_x", "phase_y"):
                    if k not in body["raw_metrics"]:
                        errors.append(f"entities.{role}.raw_metrics.{k} missing")
    if "narrative_log" not in payload:
        errors.append("narrative_log missing")
    return errors

"""Render-state schema for game engines (Godot/Blender/custom clients)."""
from __future__ import annotations

from typing import Any, Dict, List

RENDER_SCHEMA_VERSION = "fledgeling.render.v2"

RENDER_STATE_DOC = """
GameSession.status payload (fledgeling.render.v2)
=================================================

Two-layer epistemology:
  public_world   — intentionally exposed structural facts
  observer_view  — belief-derived coordinates, mask, mythos, reports
  entities       — convenience mirror of observer_view.entities (or ground if private_observers=False)
  ground_debug   — null unless include_ground_debug=True

{
  "schema_version": "fledgeling.render.v2",
  "meta": {
    "observer", "turn", "zone", "attention", "seed", "ledger_head",
    "dynamics_version", "mode",
    "global_tension",   # observer uncertainty proxy when private
    "current_mythos",   # from observer belief when private
    "q3_mask"           # from observer belief when private
  },
  "public_world": { "turn", "zone_names", "active_zone", "topology_version" },
  "observer_view": { ... } | null,
  "entities": { "<role>": { raw_metrics, semantic } },
  "narrative_log": [str],
  "zones": { ... } | null,
  "ground_debug": { ... } | null
}
"""


def validate_render_state(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(payload, dict):
        return ["payload is not a dict"]
    ver = payload.get("schema_version")
    if ver not in (RENDER_SCHEMA_VERSION, "fledgeling.render.v1"):
        errors.append(f"schema_version missing or unexpected: {ver}")
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta missing")
    else:
        for key in ("observer", "turn", "current_mythos"):
            if key not in meta:
                errors.append(f"meta.{key} missing")
    if "entities" not in payload:
        errors.append("entities missing")
    if "narrative_log" not in payload:
        errors.append("narrative_log missing")
    if ver == RENDER_SCHEMA_VERSION:
        if "public_world" not in payload:
            errors.append("public_world missing in v2")
    return errors

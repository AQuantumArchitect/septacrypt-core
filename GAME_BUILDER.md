# Game builder handoff — Septacrypt / Fledgeling

This document is for **humans and bots** building a game on top of `septacrypt-core`.

You do **not** need to understand umwelt internals to start. Use `GameSession`.

---

## 60-second start

```bash
pip install -e ../umwelt          # sibling checkout
pip install -e .

python -c "
from septacrypt_core import GameSession
g = GameSession(mode='reactor', seed=42)
g.wait(steps=2)
g.look('player', 'valve_17')
print(g.status('player')['meta']['current_mythos'])
print(g.history())
"

# Interactive
septacrypt-repl --seed 0

# One-shot JSON demo
septacrypt-demo --mode reactor --seed 42
```

---

## Mental model

```text
Player action (LOOK / WAIT / STIR)
        ↓
Cumulant quantum substrate (real dynamics)
        ↓
Optional Knot Ledger stamp (verified replay certificate)
        ↓
JSON render payload → your engine (Godot, Unity, web, …)
```

| Concept | Meaning for game design |
|--------|-------------------------|
| **Role** | One qubit / component (`valve_17`, `nav_thruster`, …) |
| **z_axis** | Classical pole −1…+1 → animation / lights |
| **radius** | Confidence; low radius = fog / blur |
| **LOOK** | Measure one role; spends attention; ripples to entangled peers |
| **WAIT** | Time evolution; builds tension / correlations |
| **STIR** | Escape hatch if poles lock forever |
| **Mythos** | Diegetic name for nearest 3-bit Q3 state (0–7) |
| **Ledger** | Tamper-evident history of certified segments |
| **WEAVE** | Symbolic story path on the Q3 cube (not physics cert) |

**Rule of the kernel:** physics constrains; spirit/preference can rank legal options; narrative only expresses.

---

## Primary API: `GameSession`

```python
from septacrypt_core import GameSession

game = GameSession(
    mode="reactor",          # or "ship" (3 zones + soft bridges)
    seed=42,                 # deterministic LOOK outcomes
    enable_ledger=True,      # stamp LOOK/WAIT with certificates
    private_observers=False, # True → each observer has a private belief field
    attention_budget=50.0,   # None = unlimited
    apply_bridges=True,      # ship mode: cross-zone soft coupling after WAIT
)
```

### Commands

| Method | Use |
|--------|-----|
| `status(observer_id, zone=None, full_ship=False)` | Frame payload for UI |
| `wait(dt_scale=None, steps=1, zone=None)` | Evolve |
| `look(observer_id, role, zone=None)` | Measure |
| `stir()` | Unlock absorbing poles |
| `weave(start_mask, end_mask)` | Symbolic lore path string |
| `history()` | Ledger stamps (if enabled) |
| `quest_status()` / `victory()` | Ship campaign helpers |
| `set_zone(name)` / `zone_names()` | Multi-zone navigation |
| `validate_payload(frame)` | Schema soft-check |

### Reactor roles

`valve_17` (structure/father), `coolant_pump` (energy/son), `temp_sensor` (info/spirit)

### Ship zones

| Zone | Roles |
|------|--------|
| `Reactor_Core` | `core_valve`, `core_pump`, `core_sensor` |
| `Navigation` | `nav_strut`, `nav_thruster`, `nav_lens` |
| `Life_Support` | `ls_filter`, `ls_blower`, `ls_monitor` |

Soft bridges (params): reactor power → thruster / blower; life-support → sensor; nav stress → valve.

---

## Render payload (engine contract)

`schema_version`: `fledgeling.render.v1`

```json
{
  "schema_version": "fledgeling.render.v1",
  "meta": {
    "observer": "player",
    "turn": 3,
    "zone": "Repair_Station",
    "global_tension": 0.012,
    "current_mythos": {"emoji": "🌟", "name": "The Cosmic Dance", "desc": "..."},
    "q3_mask": 7,
    "attention": 49.0,
    "ledger_head": "stamp_abc...",
    "dynamics_version": "septacrypt.reactor.cumulant.v1+..."
  },
  "entities": {
    "valve_17": {
      "raw_metrics": {"z_axis": 0.9, "radius": 0.95, "phase_x": 0.1, "phase_y": 0.0},
      "semantic": {"inferred_state": "active", "view": "ground"}
    }
  },
  "narrative_log": ["..."],
  "zones": null
}
```

**Shader mapping suggestions**

- `z_axis` → blend shape / frame index  
- `1 - radius` → fog opacity  
- `global_tension` → screen shake / glitch  
- `current_mythos.emoji` → UI badge  

Validate: `validate_render_state(payload)` or `game.validate_payload()`.

---

## Private observers (no telepathy)

```python
game = GameSession(private_observers=True, seed=1)  # default
game.look("keith", "valve_17")     # updates keith's belief only
game.report("keith", "dwayne", "valve_17", confidence=0.35)
keith = game.status("keith")       # observer_view from keith's beliefs
dwayne = game.status("dwayne")     # dwayne unchanged until report
```

Payload layers:

- `public_world` — turn, zone names (intentionally public)
- `observer_view` / `entities` — belief-derived mask, mythos, coordinates
- `ground_debug` — only if `include_ground_debug=True` (admin)

Beliefs are a **first-moment e1 approximation**, not a complete private umwelt.

---

## Tuning knobs

Edit `septacrypt_core/scenario/params.py`:

- couplings, gamma, dt  
- cross-zone bridges  
- attention costs, default quests  
- stir strength  
- greedy bot threshold  

Do **not** raise evolve `dt_scale` above `MAX_STABLE_DT_SCALE` (1.0) or RK4 can explode.

---

## What not to reinvent

| Need | Use |
|------|-----|
| Playable loop | `GameSession` |
| Lore names | `LoreLexicon` |
| Symbolic path flavor text | `weave` / `EndlessKnotWeaver` |
| Certified history | `enable_ledger=True` + `history()` |
| Campaign multi-zone | `mode="ship"` or `CampaignManager` |
| Monte Carlo bots | `repl.bot` (`RandomBot`, `GreedyTensionBot`, `TargetBitBot`) |

Avoid calling raw `CumulantCluster` unless extending the kernel.

---

## Honest limits (v0.1)

- Ledger **content hashes**, not Merkle partial proofs  
- `weave` is **symbolic** Q3 grammar; dynamical truth is **cassettes + certificates**  
- Ship bridges are soft observes, not one 9-qubit Hamiltonian  
- Private observers are belief snapshots, not full multi-umwelt fields  
- No DomainSpec / full umwelt `GameHost` world registration yet  

---

## Proofs / CI

```bash
python proofs/run_all.py
pytest tests/ -q
```

Flagship physics claim: `proofs/prove_witnessed_knot.py`.

---

## Suggested engine integration loop

```text
each frame / tick:
  if player pressed WAIT:  game.wait()
  if player LOOKed role:   game.look(id, role)
  payload = game.status(id, full_ship=True)
  apply payload.entities[*].raw_metrics to visuals
  show payload.meta.current_mythos + narrative_log
  optional: persist game.history() for save/replay UI
```

That’s the whole contract. Build story, art, input, and progression on top.

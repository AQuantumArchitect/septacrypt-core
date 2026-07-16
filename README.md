# septacrypt-core

**Fledgeling Septacrypt / Endless Knot** — a compact quantum-narrative kernel for games.

**Building a game?** Start here → **[GAME_BUILDER.md](./GAME_BUILDER.md)**

```python
from septacrypt_core import GameSession

game = GameSession(mode="reactor", seed=42)
game.wait(steps=2)
game.look("player", "valve_17")
frame = game.status("player")   # JSON for Godot / any engine
```

## Install

Python ≥ 3.10. Requires [umwelt](https://github.com/AQuantumArchitect/umwelt) as a sibling:

```bash
pip install -e ../umwelt
pip install -e .
pytest -q
python proofs/run_all.py
```

CLI (after install):

```bash
septacrypt-repl --seed 0
septacrypt-demo --mode ship --seed 1
```

## Architecture

```text
GameSession  (handoff surface)
    ├── geometry / lore / emoji
    ├── umwelt CumulantCluster dynamics
    ├── LOOK / WAIT / STIR actions
    ├── Knot Ledger + TransitionCertificates
    └── JSON render payload (fledgeling.render.v1)
```

| Layer | Role |
|--------|------|
| `api.session.GameSession` | **Use this** to build games |
| `geometry` | Q3 combinatorics, paths, Berry |
| `ledger` | Checkpoints, cassettes, certificates, DAG |
| `scenario` | Reactor, ship, params, campaign |
| `narrative` | Lore, braid, symbolic weaver |
| `proofs` | Executable claims |

## Honest claims

- **Witnessed histories:** stamps require real cumulant replay between anchors  
- **Symbolic weave:** Q3 Hamming paths for story only  
- **State commitment:** content hash (not Merkle tree yet)  
- **Ship bridges:** soft cross-zone coupling, not one joint 9-qubit H  

## License

Apache-2.0 — see [LICENSE](./LICENSE).

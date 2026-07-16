"""Run all executable proofs in a stable order."""
from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

PROOF_ORDER = [
    "prove_pearl_edge_bijection.py",
    "prove_knot_ledger.py",
    "prove_emoji_grammar.py",
    "prove_scale_folding.py",
    "prove_retro_insertion.py",
    "prove_story_braid.py",
    "prove_entangled_repl.py",
    "prove_witnessed_knot.py",
    # monte_carlo_churn is long-running; skip by default
]


def _load_and_run(path: Path) -> None:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "run_proof"):
        raise AttributeError(f"{path.name} has no run_proof()")
    mod.run_proof()


def main(argv=None) -> int:
    root = Path(__file__).resolve().parent
    # Ensure src layout is importable when run as script
    src = root.parent / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    failures = []
    for name in PROOF_ORDER:
        path = root / name
        if not path.exists():
            print(f"[SKIP] missing {name}")
            continue
        print(f"\n{'=' * 72}\nRUN {name}\n{'=' * 72}")
        try:
            _load_and_run(path)
        except Exception:
            traceback.print_exc()
            failures.append(name)

    print("\n" + "=" * 72)
    if failures:
        print(f"[FAIL] {len(failures)} proof(s): {', '.join(failures)}")
        return 1
    print(f"[PASS] all {len(PROOF_ORDER)} proofs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

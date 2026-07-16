"""Console entry points: septacrypt-repl, septacrypt-proofs."""
from __future__ import annotations

import argparse
import json
import sys


def repl_main(argv=None) -> int:
    from .repl.terminal import SeptacryptREPL

    parser = argparse.ArgumentParser(description="Fledgeling Septacrypt REPL")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    repl = SeptacryptREPL(seed=args.seed)
    print("Septacrypt REPL — WAIT | LOOK <role> | WEAVE a b | STATUS | HISTORY | STIR | quit")
    print(repl.execute_command("STATUS"))
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line.lower() in ("quit", "exit", "q"):
            return 0
        print(repl.execute_command(line))


def demo_main(argv=None) -> int:
    """Non-interactive demo for bots / CI."""
    from . import GameSession

    parser = argparse.ArgumentParser(description="One-shot GameSession demo")
    parser.add_argument("--mode", choices=("reactor", "ship"), default="reactor")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    game = GameSession(mode=args.mode, seed=args.seed, enable_ledger=True)
    game.wait(steps=2)
    roles = list(game.cluster.qubit_roles)
    game.look("player", roles[0])
    frame = game.status("player", full_ship=(args.mode == "ship"))
    print(json.dumps(frame, indent=2, default=str)[:2000])
    print("--- history ---")
    print(json.dumps(game.history(), indent=2))
    errs = game.validate_payload(frame)
    if errs:
        print("SCHEMA ERRORS:", errs, file=sys.stderr)
        return 1
    print("schema ok; ledger stamps:", len(game.history()))
    return 0


def proofs_main(argv=None) -> int:
    from pathlib import Path
    import runpy

    root = Path(__file__).resolve().parents[2] / "proofs" / "run_all.py"
    if not root.exists():
        # installed package: look relative to cwd
        root = Path.cwd() / "proofs" / "run_all.py"
    if not root.exists():
        print("proofs/run_all.py not found", file=sys.stderr)
        return 1
    sys.argv = [str(root)] + (argv or [])
    runpy.run_path(str(root), run_name="__main__")
    return 0

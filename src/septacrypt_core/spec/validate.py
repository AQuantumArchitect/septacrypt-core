"""CLI: python -m septacrypt_core.spec.validate package.module:ATTR"""
from __future__ import annotations

import sys

from .load import load_spec


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print("usage: python -m septacrypt_core.spec.validate module:ATTR", file=sys.stderr)
        return 2
    spec = load_spec(argv[0])
    errors = spec.validate()
    if errors:
        for e in errors:
            print(f"INVALID: {e}")
        return 1
    zones = ", ".join(f"{z.name}({len(z.roles)})" for z in spec.zones)
    print(
        f"OK: {spec.spec_id} — zones [{zones}], "
        f"{len(spec.bridges)} bridges, {len(spec.quests)} quests"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

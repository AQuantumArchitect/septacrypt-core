"""Gates for the uncertified fast path (in-place apply, no clone/hash).

The fast path must be indistinguishable from the certified path's physics:
same seed + same verbs → same physics hash whether the ledger is on or off,
and any mid-cassette failure must leave the world (including berry-journey
state) exactly as it was.
"""
import time

import pytest

from septacrypt_core.api.session import GameSession
from septacrypt_core.ledger.events import KnotEvent, world_evolve_event
from septacrypt_core.world.transaction import CertifiedTransaction, TransactionError


def _drive(game: GameSession) -> None:
    game.wait(steps=2)
    game.look("prover", "core_valve", zone="Reactor_Core")
    game.stir()
    game.wait()


def test_ledger_on_off_hash_parity():
    hashes = []
    for enable_ledger in (True, False):
        game = GameSession(mode="ship", seed=99, enable_ledger=enable_ledger)
        _drive(game)
        hashes.append(game.physics_hash())
    assert hashes[0] == hashes[1], "fast path diverged from certified physics"


def test_fast_path_mid_cassette_rollback():
    game = GameSession(mode="ship", seed=5, enable_ledger=False)
    game.wait()  # get past genesis so berry journeys carry real state
    pre_hash = game.physics_hash()
    cassette = (
        world_evolve_event(dt_scale=1.0, steps=1),  # mutates before the failure
        # valid kind, nonexistent zone → fails at apply time, mid-cassette
        KnotEvent(kind="evolve", parameters={"zone": "Nowhere", "dt_scale": 1.0}),
    )
    with pytest.raises(TransactionError):
        CertifiedTransaction.execute(
            game.world, cassette, ledger=None, require_certificate=False
        )
    assert game.physics_hash() == pre_hash, "failed fast-path commit leaked state"


def test_stir_field_growth_is_capped():
    """Regression: ship seed 52 bricked at turn 73 after 58 STIRs — h grew
    unboundedly (~11.8) until RK4 overflowed and e1 went inf. STIR_H_MAX
    caps the accumulated transverse field."""
    import numpy as np

    from septacrypt_core.scenario.params import STIR_H_MAX

    game = GameSession(mode="ship", seed=52, enable_ledger=False, attention_budget=None)
    for _ in range(80):
        game.stir()
    for cluster in game.world.zones.values():
        h = np.array(cluster._h, dtype=float)
        assert float(np.max(h[:, 0])) <= STIR_H_MAX + 1e-12
        assert np.all(np.isfinite(cluster.e1)) and np.all(np.isfinite(cluster.e2))


def test_non_finite_state_never_commits():
    """A cassette that drives the substrate non-finite must roll back, not
    commit inf/NaN (which silently bricked worlds before)."""
    import numpy as np

    from septacrypt_core.ledger.events import set_fields_event

    game = GameSession(mode="ship", seed=5, enable_ledger=False)
    game.wait()
    pre_hash = game.physics_hash()
    zone = game.world.active_zone
    n = game.world.zones[zone].n_qubits
    # Fields far past the empirical RK4 blow-up point, then a world step.
    violent = set_fields_event(zone, [[50.0, 0.0, 0.0]] * n)
    step = world_evolve_event(dt_scale=1.0, steps=5)
    with pytest.raises(TransactionError):
        CertifiedTransaction.execute(
            game.world, (violent, step), ledger=None, require_certificate=False
        )
    assert game.physics_hash() == pre_hash
    for cluster in game.world.zones.values():
        assert np.all(np.isfinite(cluster.e1)) and np.all(np.isfinite(cluster.e2))


def test_fast_path_perf_gate():
    game = GameSession(mode="ship", seed=1, enable_ledger=False, attention_budget=None)
    game.wait()  # warm-up
    n = 500
    start = time.perf_counter()
    for _ in range(n):
        game.wait()
    elapsed = time.perf_counter() - start
    per_step_ms = elapsed / n * 1000.0
    print(f"\nuncertified ship wait: {per_step_ms:.2f} ms/step over {n} steps "
          f"(pre-fast-path baseline was ~50-70 ms)")
    # 10 ms is the regression alarm (old path was ~50-70 ms); typical is ~2 ms
    # on an idle box, but this must not flake under parallel CPU load.
    assert per_step_ms < 10.0, f"fast path too slow: {per_step_ms:.2f} ms/step"

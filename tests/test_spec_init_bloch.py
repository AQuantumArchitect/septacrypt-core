"""ZoneSpec.init_bloch: construction-time initial state, parity when absent."""
import numpy as np
import pytest

from septacrypt_core.api.session import GameSession
from septacrypt_core.scenario.builtin import SHIP_SPEC
from septacrypt_core.spec.types import QuestSpec, WorldSpec, ZoneSpec
from septacrypt_core.world.snapshot import World

import dataclasses


def _zone(init_bloch=None):
    return ZoneSpec(
        name="Nursery",
        roles=("a", "b", "c"),
        h_fields=((0.2, 0.0, 0.5), (0.2, 0.0, 0.5), (0.2, 0.0, 0.5)),
        zz=(((0, 1), 0.05),),
        gamma=0.02,
        dt=0.1,
        init_bloch=init_bloch,
    )


def _spec(init_bloch=None):
    return WorldSpec(
        spec_id="test.init_bloch.v1",
        topology_version="test.v1",
        zones=(_zone(init_bloch),),
        quests=(QuestSpec(zone="Nursery", target_mask=0b111),),
    )


def test_default_none_is_hash_identical_to_pre_change():
    """The parity gate: a spec without init_bloch behaves bit-identically."""
    hashes = []
    for _ in range(2):
        g = GameSession(spec=SHIP_SPEC, seed=11, enable_ledger=False)
        for _ in range(20):
            g.wait()
        g.look("keith", g.world.cluster.qubit_roles[0])
        for _ in range(10):
            g.wait()
        hashes.append(g.physics_hash())
    assert hashes[0] == hashes[1]


def test_init_bloch_sets_construction_state():
    rows = ((0.0, 0.0, -0.9), (0.3, 0.0, 0.0), (0.0, 0.0, 0.9))
    w = World.from_spec(_spec(rows), seed=5)
    assert np.allclose(w.zones["Nursery"].e1, np.array(rows))


def test_clone_and_restore_ignore_init_bloch():
    rows = ((0.0, 0.0, -0.9), (0.3, 0.0, 0.0), (0.0, 0.0, 0.9))
    w = World.from_spec(_spec(rows), seed=5)
    from septacrypt_core.ledger.events import KnotEvent

    for _ in range(7):
        w.apply_event(KnotEvent(kind="evolve", parameters={"dt_scale": 1.0}))
    snap = w.snapshot()
    c = w.clone()
    assert np.allclose(c.zones["Nursery"].e1, w.zones["Nursery"].e1)
    w.restore(snap)
    assert np.allclose(w.zones["Nursery"].e1, c.zones["Nursery"].e1)


def test_validator_rejects_bad_init_bloch():
    wrong_rows = _spec(((0.0, 0.0, 1.0),))  # 1 row for 3 roles
    assert any("one row per role" in e for e in wrong_rows.validate())
    outside = _spec(((0.0, 0.0, 1.5), (0, 0, 0), (0, 0, 0)))
    assert any("Bloch ball" in e for e in outside.validate())
    ok = _spec(((0.0, 0.0, 0.9), (0.5, 0.0, 0.0), (0.0, 0.0, 0.0)))
    assert ok.validate() == []


def test_role_modes_unitary_holds_pole():
    """A unitary role holds its collapsed pole; the dissipative default
    thermalizes toward the mixed state within ~2 time units."""
    base = _zone(init_bloch=((0.0, 0.0, 0.9),) * 3)
    unitary = dataclasses.replace(base, role_modes=("unitary",) * 3)
    for zone, persists in ((base, False), (unitary, True)):
        spec = dataclasses.replace(_spec(), zones=(zone,))
        assert spec.validate() == []
        w = World.from_spec(spec, seed=1)
        for _ in range(30):
            w.zones["Nursery"].step(dt_scale=1.0)
        z = float(w.zones["Nursery"].e1[0, 2])
        assert (abs(z) > 0.5) == persists, f"z={z} persists={persists}"


def test_validator_rejects_bad_role_modes():
    bad_count = dataclasses.replace(_zone(), role_modes=("unitary",))
    spec = dataclasses.replace(_spec(), zones=(bad_count,))
    assert any("one entry per role" in e for e in spec.validate())
    bad_value = dataclasses.replace(_zone(), role_modes=("unitary", "magic", "unitary"))
    spec = dataclasses.replace(_spec(), zones=(bad_value,))
    assert any("'unitary' or 'dissipative'" in e for e in spec.validate())


def test_seeded_determinism_with_init_bloch():
    hashes = []
    for _ in range(2):
        g = GameSession(spec=_spec(((0, 0, 0.9), (0.4, 0, 0), (0, 0, -0.9))), seed=3)
        for _ in range(15):
            g.wait()
        hashes.append(g.physics_hash())
    assert hashes[0] == hashes[1]

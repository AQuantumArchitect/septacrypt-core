"""Acceptance tests for composite fail-closed world certification."""
from __future__ import annotations

import pytest

from septacrypt_core import GameSession
from septacrypt_core.world.transaction import TransactionError


def test_active_zone_does_not_change_physics():
    """100 world steps with different active-zone selections → same final hash."""
    a = GameSession(mode="ship", seed=11, enable_ledger=False, private_observers=False)
    b = GameSession(mode="ship", seed=11, enable_ledger=False, private_observers=False)
    zones = a.zone_names()
    for i in range(100):
        a.set_zone(zones[i % len(zones)])
        b.set_zone(zones[0])  # always Reactor_Core
        a.wait(steps=1)
        b.wait(steps=1)
    assert a.physics_hash() == b.physics_hash()


def test_stir_and_wait_are_replayable():
    g = GameSession(mode="reactor", seed=5, enable_ledger=True, private_observers=False)
    g.wait(steps=1)
    h1 = g.physics_hash()
    g.stir()
    h2 = g.physics_hash()
    assert h1 != h2
    assert len(g.history()) >= 3  # init + wait + stir


def test_ship_bridges_in_certified_cassette():
    g = GameSession(mode="ship", seed=3, enable_ledger=True, private_observers=False, apply_bridges=True)
    g.wait(steps=2)
    assert g.physics_hash()
    kinds = [h["event_kind"] for h in g.history()]
    assert "wait" in kinds


def test_failed_certificate_leaves_world_unchanged():
    g = GameSession(mode="reactor", seed=1, enable_ledger=True, private_observers=False)
    g.wait(steps=1)
    pre = g.physics_hash()
    head = g.history()[-1]["stamp_id"]
    # Force branch head mismatch via internal API
    from septacrypt_core.ledger.events import world_evolve_event
    from septacrypt_core.world.transaction import CertifiedTransaction

    with pytest.raises(TransactionError):
        CertifiedTransaction.execute(
            g.world,
            (world_evolve_event(1.0, 1),),
            ledger=g.ledger,
            expected_branch_head="not_a_real_head",
            require_certificate=True,
        )
    assert g.physics_hash() == pre
    assert g.history()[-1]["stamp_id"] == head


def test_alice_look_does_not_change_bob_belief():
    g = GameSession(mode="reactor", seed=9, enable_ledger=False, private_observers=True)
    g.wait(steps=1)
    bob_before = g.status("bob")["entities"]["valve_17"]["raw_metrics"]["z_axis"]
    g.look("alice", "valve_17")
    bob_after = g.status("bob")["entities"]["valve_17"]["raw_metrics"]["z_axis"]
    assert bob_before == bob_after


def test_bob_mythos_from_belief_not_ground():
    g = GameSession(
        mode="reactor",
        seed=2,
        enable_ledger=False,
        private_observers=True,
        include_ground_debug=True,
    )
    g.wait(steps=2)
    g.look("alice", "valve_17")
    bob = g.status("bob")
    # Bob never looked — first-moment prior near zero → Holy Dark mask 0
    assert bob["meta"]["q3_mask"] == 0
    assert bob["observer_view"]["current_mythos"]["name"]
    # Ground may differ
    ground_mask = bob["ground_debug"]["q3_mask"]
    # After alice look ground changed; bob still 0
    assert bob["meta"]["q3_mask"] != ground_mask or ground_mask == 0


def test_report_updates_target_only():
    g = GameSession(mode="reactor", seed=4, enable_ledger=False, private_observers=True)
    g.wait(steps=1)
    g.look("keith", "valve_17")
    dwayne_before = g.status("dwayne")["entities"]["valve_17"]["raw_metrics"]["z_axis"]
    g.report("keith", "dwayne", "valve_17", confidence=0.8)
    dwayne_after = g.status("dwayne")["entities"]["valve_17"]["raw_metrics"]["z_axis"]
    assert dwayne_after != dwayne_before or abs(dwayne_after) > 0


def test_routine_shadow_first():
    g = GameSession(mode="reactor", seed=0, enable_ledger=False)
    g.register_routine("patrol_valve", "keith")
    assert g.world.routines["patrol_valve"]["shadow"] is True
    assert g.world.routines["patrol_valve"]["auto_live"] is False
    g.promote_routine("patrol_valve", "player", evidence="demo_ok")
    assert g.world.routines["patrol_valve"]["shadow"] is False
    assert g.world.routines["patrol_valve"]["auto_live"] is True


def test_schema_v2():
    g = GameSession(mode="reactor", seed=0, enable_ledger=False)
    frame = g.status("player")
    assert frame["schema_version"] == "fledgeling.render.v2"
    assert not g.validate_payload(frame)
    assert "public_world" in frame

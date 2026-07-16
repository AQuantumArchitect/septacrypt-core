"""Handoff-surface smoke tests for GameSession."""
from septacrypt_core import GameSession, validate_render_state
from septacrypt_core.scenario.params import REACTOR_ROLES


def test_reactor_look_wait_ledger_and_schema():
    g = GameSession(
        mode="reactor",
        seed=42,
        enable_ledger=True,
        attention_budget=10.0,
        private_observers=False,
    )
    g.wait(steps=2)
    frame = g.look("player", REACTOR_ROLES[0])
    assert frame["schema_version"]
    assert not validate_render_state(frame)
    assert frame["meta"]["ledger_head"]
    hist = g.history()
    assert len(hist) >= 2
    assert any(h["event_kind"] == "look" for h in hist)


def test_seeded_look_deterministic():
    a = GameSession(mode="reactor", seed=7, enable_ledger=False, attention_budget=None, private_observers=False)
    b = GameSession(mode="reactor", seed=7, enable_ledger=False, attention_budget=None, private_observers=False)
    a.wait(steps=1)
    b.wait(steps=1)
    fa = a.look("p", "valve_17")
    fb = b.look("p", "valve_17")
    assert (
        fa["entities"]["valve_17"]["raw_metrics"]["z_axis"]
        == fb["entities"]["valve_17"]["raw_metrics"]["z_axis"]
    )


def test_ship_bridges_and_quests():
    g = GameSession(mode="ship", seed=1, enable_ledger=False, apply_bridges=True, private_observers=False)
    g.wait(steps=1, zone="Reactor_Core")
    full = g.status("player", full_ship=True)
    assert full["zones"] is not None
    assert "Navigation" in full["zones"]
    assert g.quest_status()


def test_private_observers_isolated():
    g = GameSession(
        mode="reactor",
        seed=3,
        enable_ledger=False,
        private_observers=True,
        attention_budget=None,
    )
    g.wait(steps=1)
    g.look("keith", "valve_17")
    k = g.status("keith")
    d = g.status("dwayne")
    assert k["entities"]["valve_17"]["semantic"]["view"] == "private"
    assert d["entities"]["valve_17"]["semantic"]["view"] == "private"
    # dwayne did not auto-update
    assert d["entities"]["valve_17"]["raw_metrics"]["z_axis"] == 0.0


def test_stir_runs():
    g = GameSession(mode="reactor", seed=0, enable_ledger=False, private_observers=False)
    g.stir()
    assert g.turn >= 1

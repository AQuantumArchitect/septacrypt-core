"""WorldSpec gates: hash-parity with legacy modes, validation, custom worlds."""
import pytest

from septacrypt_core.api.session import GameSession
from septacrypt_core.scenario.builtin import REACTOR_SPEC, SHIP_SPEC
from septacrypt_core.spec import BridgeSpec, QuestSpec, WorldSpec, ZoneSpec, load_spec


def _drive(game: GameSession, turns: int = 50) -> list:
    """Mixed seeded play; returns physics hash checkpoints."""
    hashes = []
    roles = list(game.world.zones[game.world.active_zone].qubit_roles)
    for i in range(turns):
        if i % 7 == 3:
            game.look("parity", roles[i % len(roles)])
        elif i % 11 == 5:
            game.stir()
        else:
            game.wait()
        if i % 10 == 9:
            hashes.append(game.physics_hash())
    return hashes


@pytest.mark.parametrize(
    "mode,spec", [("ship", SHIP_SPEC), ("reactor", REACTOR_SPEC)]
)
def test_spec_hash_parity_with_legacy_mode(mode, spec):
    legacy = GameSession(mode=mode, seed=77, enable_ledger=False, attention_budget=None)
    from_spec = GameSession(spec=spec, seed=77, enable_ledger=False, attention_budget=None)
    assert _drive(legacy) == _drive(from_spec), f"{mode} spec diverged from legacy mode"


def test_builtin_specs_validate():
    assert REACTOR_SPEC.validate() == []
    assert SHIP_SPEC.validate() == []


def test_load_spec_ref():
    spec = load_spec("septacrypt_core.scenario.builtin:SHIP_SPEC")
    assert spec is SHIP_SPEC
    with pytest.raises(ValueError):
        load_spec("septacrypt_core.scenario.builtin:NOPE")
    with pytest.raises(ValueError):
        load_spec("no-colon")


def test_v1_rejects_non_three_role_zones():
    bad = WorldSpec(
        spec_id="bad.v1",
        topology_version="topology.custom.v1",
        zones=(
            ZoneSpec(
                name="Z",
                roles=("a", "b"),
                h_fields=((0.1, 0.0, 0.0), (0.1, 0.0, 0.0)),
                zz=(((0, 1), 0.5),),
                gamma=0.02,
                dt=0.1,
            ),
        ),
    )
    errors = bad.validate()
    assert any("exactly 3" in e for e in errors)
    with pytest.raises(ValueError):
        GameSession(spec=bad, seed=1)


CUSTOM_SPEC = WorldSpec(
    spec_id="test.greenhouse.v1",
    topology_version="topology.greenhouse.v1",
    zones=(
        ZoneSpec(
            name="Greenhouse",
            roles=("lamp", "mister", "thermostat"),
            h_fields=((0.2, 0.0, 0.0), (0.1, 0.0, 0.0), (0.1, 0.0, 0.0)),
            zz=(((0, 1), 0.7), ((1, 2), 0.3)),
            gamma=0.02,
            dt=0.1,
        ),
        ZoneSpec(
            name="Cellar",
            roles=("valve", "pump", "gauge"),
            h_fields=((0.15, 0.0, 0.0), (0.15, 0.0, 0.0), (0.1, 0.0, 0.0)),
            zz=(((0, 1), 0.5),),
            gamma=0.03,
            dt=0.1,
        ),
    ),
    bridges=(BridgeSpec("Greenhouse", "thermostat", "Cellar", "gauge", 0.1),),
    quests=(QuestSpec("Greenhouse", 0b101),),
    attention=20.0,
)


def test_custom_spec_plays_certified():
    """A never-before-seen world must work on the FULL certified path —
    including clone dispatch (World.clone for spec worlds) and replay."""
    game = GameSession(spec=CUSTOM_SPEC, seed=5)  # ledger ON
    assert game.mode == "test.greenhouse.v1"
    assert game.attention_budget == 20.0  # spec attention applied
    assert set(game.zones) == {"Greenhouse", "Cellar"}
    game.wait()
    game.look("tester", "lamp", zone="Greenhouse")
    game.stir()
    assert len(game.history()) >= 3
    quests = game.quest_status()
    assert quests[0]["zone"] == "Greenhouse" and quests[0]["target_mask"] == 0b101
    state = game.status("tester")
    assert game.validate_payload(state) == []


def test_custom_spec_seed_determinism():
    h = []
    for _ in range(2):
        g = GameSession(spec=CUSTOM_SPEC, seed=9, enable_ledger=False)
        g.wait()
        g.look("d", "pump", zone="Cellar")
        g.wait()
        h.append(g.physics_hash())
    assert h[0] == h[1]

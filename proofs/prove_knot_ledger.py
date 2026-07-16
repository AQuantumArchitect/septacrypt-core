from septacrypt_core.ledger.roots import generate_state_root, verify_state_root
from septacrypt_core.ledger.checkpoint import Checkpoint, replay_overlay
from septacrypt_core.ledger.dag import KnotLedger
from septacrypt_core.ledger.stamp import KnotStamp

def run_proof():
    print("--- Running Phase 2 Proof: Knot Ledger DAG ---\n")

    # 1. Test Canonical State Roots (Tamper Detection)
    base_state = {"pump": "working", "valve_17": "open", "temp": 45.5}
    root1 = generate_state_root(base_state)
    root2 = generate_state_root({"valve_17": "open", "temp": 45.5, "pump": "working"}) # Scrambled order

    assert root1 == root2, "Canonical serialization failed: order altered root."
    print("[PASS] Deterministic state roots generated.")

    tampered_state = {"pump": "working", "valve_17": "closed", "temp": 45.5}
    assert not verify_state_root(tampered_state, root1), "Tamper detection failed!"
    print("[PASS] Tamper detection functional (altered state rejected).")

    # 2. Test Checkpoint & Replay Overlay
    cp_base = Checkpoint.create("cp_001", 0.0, base_state)
    cp_replayed = replay_overlay(cp_base, ["close_valve"])

    assert "close_valve" in cp_replayed.state_data["applied_events"], "Event overlay failed."
    assert cp_base.state_root != cp_replayed.state_root, "State root failed to update post-replay."
    print("[PASS] Checkpoint and deterministic overlay replay successful.")

    # 3. Test Append-Only DAG and Branching
    ledger = KnotLedger()

    # Anchor Stamp
    stamp_A = KnotStamp(
        stamp_id="pending", parent_ids=(), branch_id="main", event_kind="init",
        actor_id=None, observer_id="keith", chronological_time=0.0,
        berry_coordinate={"loop": 0}, scale_address=("reactor",),
        pre_state_root=root1, post_state_root=root1, transition_certificate_id="cert_0",
        truth_mode="observed", confidence=1.0, spirit_vector=None
    )
    sealed_a_id = ledger.append_stamp(stamp_A)

    # Branching
    ledger.branch(parent_stamp_id=sealed_a_id, new_branch_id="what_if")

    # New event on branch
    stamp_B = KnotStamp(
        stamp_id="pending", parent_ids=(sealed_a_id,), branch_id="what_if", event_kind="valve_close",
        actor_id="dwayne", observer_id="dwayne", chronological_time=1.0,
        berry_coordinate={"loop": 1}, scale_address=("reactor", "valve_17"),
        pre_state_root=root1, post_state_root=cp_replayed.state_root, transition_certificate_id="cert_1",
        truth_mode="acted", confidence=1.0, spirit_vector=None
    )
    ledger.append_stamp(stamp_B)

    # Verify Histories
    main_history = ledger.get_history("main")
    what_if_history = ledger.get_history("what_if")

    assert len(main_history) == 1, "Main branch history corrupted."
    assert len(what_if_history) == 2, "What-if branch history corrupted."
    assert main_history[0].stamp_id == what_if_history[0].stamp_id, "Branch prefix sharing failed!"

    print("[PASS] DAG Branching successful. Prefix is correctly shared.")
    print("\n[PASS] Phase 2 Knot Ledger DAG is structurally sound.")

if __name__ == "__main__":
    run_proof()

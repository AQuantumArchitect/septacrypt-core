from septacrypt_core.geometry.address import ScaleAddress
from septacrypt_core.ledger.certificate import mint_empty_certificate
from septacrypt_core.ledger.checkpoint import Checkpoint, legacy_dict_overlay
from septacrypt_core.ledger.dag import KnotLedger
from septacrypt_core.ledger.roots import generate_state_hash, verify_state_hash
from septacrypt_core.ledger.stamp import KnotStamp, TransitionCertificate



def run_proof():
    print("--- Running Phase 2 Proof: Knot Ledger DAG (bookkeeping) ---\n")
    print("Note: this proof covers content hashes + DAG structure.")
    print("Dynamical replay is proven in prove_witnessed_knot.py.\n")

    # 1. Deterministic content hashes (not Merkle trees)
    base_state = {"pump": "working", "valve_17": "open", "temp": 45.5}
    root1 = generate_state_hash(base_state)
    root2 = generate_state_hash({"valve_17": "open", "temp": 45.5, "pump": "working"})

    assert root1 == root2, "Canonical serialization failed: order altered hash."
    print("[PASS] Deterministic state content hashes generated.")

    tampered_state = {"pump": "working", "valve_17": "closed", "temp": 45.5}
    assert not verify_state_hash(tampered_state, root1), "Tamper detection failed!"
    print("[PASS] Tamper detection functional (altered state rejected).")

    # 2. Legacy dict overlay (bookkeeping only — not substrate dynamics)
    cp_base = Checkpoint.create("cp_001", 0.0, base_state)
    cp_replayed = legacy_dict_overlay(cp_base, ["close_valve"])

    assert "close_valve" in cp_replayed.state_data["applied_events"], "Event overlay failed."
    assert cp_base.state_hash != cp_replayed.state_hash, "State hash failed to update post-overlay."
    print("[PASS] Legacy dict overlay bookkeeping works (not physics).")

    # 3. Append-only DAG with certificates (empty/init certs for bookkeeping stamps)
    ledger = KnotLedger()

    stamp_A = KnotStamp(
        stamp_id="pending",
        parent_ids=(),
        branch_id="main",
        event_kind="init",
        actor_id=None,
        observer_id="keith",
        chronological_time=0.0,
        berry_coordinate={"schema": "berry.v1", "path_signature": "init"},
        scale_address=ScaleAddress(("reactor",)),
        pre_state_root=root1,
        post_state_root=root1,
        transition_certificate_id="pending",
        truth_mode="observed",
        confidence=1.0,
        spirit_vector=None,
    )
    cert_A = mint_empty_certificate(Checkpoint.create("a", 0.0, base_state))
    # Align empty cert roots with the bookkeeping hashes used on the stamp
    cert_A = TransitionCertificate(

        dynamics_version=cert_A.dynamics_version,
        pre_state_root=root1,
        post_state_root=root1,
        event_digest=cert_A.event_digest,
        chronological_interval=(0.0, 0.0),
        residual=0.0,
        tolerance=cert_A.tolerance,
        rng_commitment=cert_A.rng_commitment,
        replay_cassette=cert_A.replay_cassette,
        affected_surface=cert_A.affected_surface,
        hidden_conditions=cert_A.hidden_conditions,
    )
    sealed_a_id = ledger.append_stamp(
        stamp_A,
        certificate=cert_A,
        expected_branch_head=None,
    )

    ledger.branch(parent_stamp_id=sealed_a_id, new_branch_id="what_if")

    stamp_B = KnotStamp(
        stamp_id="pending",
        parent_ids=(sealed_a_id,),
        branch_id="what_if",
        event_kind="valve_close",
        actor_id="dwayne",
        observer_id="dwayne",
        chronological_time=1.0,
        berry_coordinate={"schema": "berry.v1", "path_signature": "branch"},
        scale_address=ScaleAddress(("reactor", "valve_17")),
        pre_state_root=root1,
        post_state_root=cp_replayed.state_hash,
        transition_certificate_id="pending",
        truth_mode="acted",
        confidence=1.0,
        spirit_vector=None,
    )
    cert_B = TransitionCertificate(
        dynamics_version=cert_A.dynamics_version,
        pre_state_root=root1,
        post_state_root=cp_replayed.state_hash,
        event_digest=cert_A.event_digest,
        chronological_interval=(0.0, 1.0),
        residual=0.0,
        tolerance=cert_A.tolerance,
        rng_commitment=cert_A.rng_commitment,
        replay_cassette="[]",
        affected_surface=("valve_17",),
        hidden_conditions=cert_A.hidden_conditions,
    )
    ledger.append_stamp(
        stamp_B,
        certificate=cert_B,
        expected_branch_head=sealed_a_id,
    )

    main_history = ledger.get_history("main")
    what_if_history = ledger.get_history("what_if")

    assert len(main_history) == 1, "Main branch history corrupted."
    assert len(what_if_history) == 2, "What-if branch history corrupted."
    assert main_history[0].stamp_id == what_if_history[0].stamp_id, "Branch prefix sharing failed!"

    # Reject head hijack on main (wrong expected_branch_head)
    try:
        bad = KnotStamp(
            stamp_id="pending",
            parent_ids=(sealed_a_id,),
            branch_id="main",
            event_kind="hijack",
            actor_id=None,
            observer_id=None,
            chronological_time=2.0,
            berry_coordinate={},
            scale_address=ScaleAddress(("reactor",)),
            pre_state_root=root1,
            post_state_root=root1,
            transition_certificate_id="pending",
            truth_mode="acted",
            confidence=1.0,
            spirit_vector=None,
        )
        hijack_cert = TransitionCertificate(
            dynamics_version=cert_A.dynamics_version,
            pre_state_root=root1,
            post_state_root=root1,
            event_digest=cert_A.event_digest,
            chronological_interval=(0.0, 2.0),
            residual=0.0,
            tolerance=cert_A.tolerance,
            rng_commitment=cert_A.rng_commitment,
            replay_cassette="[]",
            affected_surface=(),
            hidden_conditions=cert_A.hidden_conditions,
        )
        ledger.append_stamp(bad, certificate=hijack_cert, expected_branch_head="not_the_head")
        raise AssertionError("expected_branch_head mismatch should have raised")
    except ValueError as e:
        assert "expected_branch_head" in str(e), str(e)
        print("[PASS] Branch head enforcement rejects hijack.")


    print("[PASS] DAG Branching successful. Prefix is correctly shared.")
    print("\n[PASS] Phase 2 Knot Ledger DAG is structurally sound.")


if __name__ == "__main__":
    run_proof()

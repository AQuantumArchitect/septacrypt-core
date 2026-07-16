from septacrypt_core.dynamics.transition import QuantumState3Qubit, TransitionVerifier
from septacrypt_core.ledger.replay import RetroSolver

def run_proof():
    print("--- Running Phase 5 Proof: Symbolic Retro Paths & Population Check ---\n")
    print("Claim: finds Septacrypt-legal symbolic Hamming-1 paths (graph grammar).")
    print("Not claimed: dynamical realizability under the cumulant substrate.")
    print("See prove_witnessed_knot.py for physics-gated certificates.\n")

    # 1. Verify Q3 Adjacency (Strict Graph constraints)
    # 0b010 (Might) to 0b000 (Holy Dark) -> Hamming distance 1 (Valid)
    assert TransitionVerifier.verify_step(0b010, 0b000), "Failed to recognize valid Q3 transition."

    # 0b010 (Might) to 0b101 (Glory) -> Hamming distance 3 (Invalid direct transition)
    assert not TransitionVerifier.verify_step(0b010, 0b101), "Allowed physically impossible teleportation!"
    print("[PASS] Q3 Adjacency verifier correctly guards physical transitions.")

    # 2. Population / coherence-magnitude match (necessary, not full local-gauge equivalence)
    state_1 = QuantumState3Qubit.from_classical_state(0b010)

    matrix_gauge_shifted = [[0.0j for _ in range(8)] for _ in range(8)]
    matrix_gauge_shifted[2][2] = 1.0 + 0.0j
    state_2 = QuantumState3Qubit(matrix_gauge_shifted)

    assert state_1.populations_and_coherence_magnitudes_match(state_2), (
        "Population/magnitude match failed on identical pure states!"
    )
    print("[PASS] Population + coherence-magnitude check agrees on identical pure states.")
    print("       (Not a full local-unitary gauge test; see dynamics/transition.py docstring.)")


    # 3. Test Microscope-Style Retro Insertion
    # Anchor A: Valve is Open (0b010 - Might)
    # Anchor D: Valve is Closed and Pump is Off (0b000 - Holy Dark)
    anchor_a = 0b010
    anchor_d = 0b000

    # Solve the gap
    allowed_states = [0b000, 0b001, 0b010, 0b011, 0b100, 0b101, 0b110, 0b111]
    solver = RetroSolver(allowed_states)

    # Generate causal neighborhood cone
    cone = solver.build_causal_cone(anchor_a, max_depth=2)
    print(f"1. Causal cone around Anchor A ({bin(anchor_a)}) constructed. Neighbors: {[bin(k) for k in cone[anchor_a]]}")

    # Find valid insertion paths
    valid_paths = solver.solve_insertion(anchor_a, anchor_d, max_steps=2)

    print(f"2. Found {len(valid_paths)} physically valid timeline paths:")
    for path in valid_paths:
        path_str = " -> ".join(f"[{bin(state)}]" for state in path)
        print(f"   * {path_str}")

    # Assertions
    assert len(valid_paths) > 0, "Failed to find any valid transition paths!"
    # The direct path [0b010 -> 0b000] is valid since it is a 1-bit flip
    assert [0b010, 0b000] in valid_paths, "Failed to locate optimal 1-step physical path."

    # Ensure no path in the list contains illegal teleportation steps
    for path in valid_paths:
        for i in range(len(path) - 1):
            assert TransitionVerifier.verify_step(path[i], path[i+1]), f"Illegal step found in path: {path[i]} -> {path[i+1]}"

    print("\n[PASS] Symbolic retro solver honors strict Q3 graph boundaries.")
    print("[PASS] Phase 5 symbolic path grammar is complete (dynamics: witnessed_knot).")


if __name__ == "__main__":
    run_proof()

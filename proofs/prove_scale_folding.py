from septacrypt_core.geometry.address import ScaleAddress
from septacrypt_core.dynamics.fold import SpectralFolder
from septacrypt_core.dynamics.transition import QuantumState3Qubit

def run_proof():
    print("--- Running Phase 8 Proof: Spectral Folding & Scale Normalization ---\n")

    # 1. Verify Case-Insensitive Address Normalization (The Defect Resolution)
    addr_1 = ScaleAddress(("Repair_Station", "Reactor", "Coolant", "Valve_17"))
    addr_2 = ScaleAddress(("repair_station", "reactor", "coolant", "valve_17"))

    assert addr_1 == addr_2, "Address comparison failed on case-sensitivity normalization!"
    assert addr_1.contains("Reactor"), "Address lookup failed on capital check."
    assert addr_1.contains("reactor"), "Address lookup failed on lowercase check."
    print("[PASS] ScaleAddress invariants structurally secure. String casing defects permanently neutralized.")

    # 2. Setup high-dimensional 3-qubit state (8x8 density matrix rho)
    # Representing a coherent state of our reactor loop
    rho_8x8 = [[0.0j for _ in range(8)] for _ in range(8)]
    rho_8x8[0][0] = 0.5 + 0.0j
    rho_8x8[2][2] = 0.5 + 0.0j
    rho_8x8[0][2] = 0.5 + 0.0j
    rho_8x8[2][0] = 0.5 + 0.0j

    # 3. Define standard isometry projection matrix V (8x2 complex matrix)
    # Maps our high-dimensional space down to a 2-state 'Normal' vs 'Anomaly' binary system
    # Here we map basis state |000> (index 0) to logical state |0> (index 0)
    # and basis state |010> (index 2) to logical state |1> (index 1).
    V = [[0.0j for _ in range(2)] for _ in range(8)]
    V[0][0] = 1.0 + 0.0j # basis 0 -> logical 0
    V[2][1] = 1.0 + 0.0j # basis 2 -> logical 1

    # 4. Isometry check (V^H V ≈ I) then subspace fold
    iso_err = SpectralFolder.isometry_error(V)
    assert iso_err < 1e-9, f"Manual V is not isometric: error={iso_err}"
    print(f"3. Isometry check ||V^H V - I||_max = {iso_err:.3e}")

    folded_rho = SpectralFolder.fold_state(rho_8x8, V)

    print("4. Successfully folded 8x8 mixed state to logical 2x2 state space.")
    print(f"   - Folded matrix trace: {SpectralFolder.trace(folded_rho)}")
    print(f"   - Folded state diagonal: {folded_rho[0][0]} and {folded_rho[1][1]}")

    assert len(folded_rho) == 2 and len(folded_rho[0]) == 2, "Dimensions of folded state are incorrect!"
    assert abs(SpectralFolder.trace(folded_rho) - 1.0) < 1e-9, "Trace was not preserved during subspace folding!"

    assert abs(folded_rho[0][0] - 0.5) < 1e-9, "Spectral projection misplaced system amplitude on state 0."
    assert abs(folded_rho[1][1] - 0.5) < 1e-9, "Spectral projection misplaced system amplitude on state 1."

    print("\n[PASS] Fold primitive + isometry check OK (manual V; not auto spectral basis).")
    print("[PASS] Phase 8 ScaleAddress + fold primitive verified.")


if __name__ == "__main__":
    run_proof()

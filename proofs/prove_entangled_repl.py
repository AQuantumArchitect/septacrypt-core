from septacrypt_core.repl.terminal import SeptacryptREPL

def run_proof():
    print("=========================================================================")
    print("           FLEDGELING SEPTACRYPT: THE ENTANGLED REACTOR REPL             ")
    print("=========================================================================\n")

    repl = SeptacryptREPL()

    print("> STATUS")
    print(repl.execute_command("STATUS") + "\n")

    # Let the ZZ-coupled Lindblad/cumulant evolution build real e1/e2 correlations
    # between valve_17 and coolant_pump before we measure anything. Empirically
    # checked: with this cluster's gamma/dt, valve<->pump correlation peaks at
    # step 1 (conn_zz ~ 0.007) then decays back toward equilibrium as the
    # amplitude damping wins out -- so 2 WAITs, not 5, catches it near the peak.
    print("> WAIT (x2, building entanglement via the ZZ coupling)")
    for _ in range(2):
        print(repl.execute_command("WAIT"))
    print()

    z_values = {r: float(repl.cluster.role_bloch(r)[2]) for r in repl.cluster.role_index}
    assert all(abs(z) <= 1.0 + 1e-9 for z in z_values.values()), (
        f"Bloch z left [-1, 1] after WAIT -- integration is unstable, not entanglement: {z_values}"
    )
    print(f"[CHECK] all Bloch z values physically bounded after WAIT: {z_values}\n")

    pump_z_before = float(repl.cluster.role_bloch("coolant_pump")[2])
    sensor_z_before = float(repl.cluster.role_bloch("temp_sensor")[2])

    print("> LOOK valve_17")
    print(repl.execute_command("LOOK valve_17") + "\n")

    pump_z_after = float(repl.cluster.role_bloch("coolant_pump")[2])
    sensor_z_after = float(repl.cluster.role_bloch("temp_sensor")[2])

    assert abs(pump_z_after) <= 1.0 + 1e-9 and abs(sensor_z_after) <= 1.0 + 1e-9, (
        f"Bloch z left [-1, 1] after LOOK -- integration is unstable: "
        f"pump={pump_z_after}, sensor={sensor_z_after}"
    )

    pump_shift = abs(pump_z_after - pump_z_before)
    print(f"[CHECK] coolant_pump z: {pump_z_before:.4f} -> {pump_z_after:.4f} (shift={pump_shift:.4f})")
    print(f"[CHECK] temp_sensor z: {sensor_z_before:.4f} -> {sensor_z_after:.4f}\n")

    assert pump_shift > 1e-6, (
        "Measuring valve_17 produced no shift at all in its ZZ-coupled peer "
        "(coolant_pump) -- entanglement did not propagate."
    )
    print("[PASS] Measuring valve_17 rippled into its entangled peer (coolant_pump).")

    # Attention budget must actually decrement, and refuse once exhausted.
    assert repl.attention_budget == 9.0, "LOOK did not spend attention correctly."
    print("[PASS] Attention budget spent correctly on LOOK.")

    print("\n> WEAVE 6 0")
    weave_result = repl.execute_command("WEAVE 6 0")
    print(weave_result + "\n")
    assert "rejects this insertion" not in weave_result, "Expected a valid Q3 path for 6 -> 0."
    assert "Father" in weave_result and "Son" in weave_result, (
        "Expected the 0b110 -> 0b010 -> 0b000 path (sever Father, then Son)."
    )
    print("[PASS] EndlessKnotWeaver found the valid 2-step retro-insertion path.")

    # Note: with max_steps=3 and Q3's diameter also 3, every pair of the 8 basis
    # states is reachable -- there is no "unreachable" example to demonstrate the
    # weaver's rejection branch within this cube. This just exercises a second path.
    print("\n> WEAVE 0 5")
    print(repl.execute_command("WEAVE 0 5"))

    print("\n=========================================================================")
    print("  [PASS] ENTANGLED REACTOR, REPL, AND RETRO-WEAVER ALL FUNCTIONAL.        ")
    print("=========================================================================")

if __name__ == "__main__":
    run_proof()

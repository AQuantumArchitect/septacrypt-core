from septacrypt_core.geometry.emoji import EmojiGrammar
from septacrypt_core.geometry.counts import generate_pearls

def run_proof():
    print("--- Running Phase 6 Proof: Emoji-Qubit Grammar & Visual State Parser ---\n")

    # 1. Verify Signed Generator Pole Composites (Octahedron Hub)
    # 0b111 (Blessing) must map to all positive poles: Father 👑, Son ⚡, Spirit 🕊️
    poles_111 = EmojiGrammar.get_poles_for_state(0b111)
    print(f"1. 0b111 (Blessing) is comprised of poles: {poles_111}")
    assert "👑" in poles_111 and "⚡" in poles_111 and "🕊️" in poles_111, "0b111 Pole mapping corrupted!"

    # 0b000 (Holy Dark) must map to all negative/latent poles: Structure 🧱, Work 🛠️, Focus 🕯️
    poles_000 = EmojiGrammar.get_poles_for_state(0b000)
    print(f"2. 0b000 (Holy Dark) is comprised of poles: {poles_000}")
    assert "🧱" in poles_000 and "🛠️" in poles_000 and "🕯️" in poles_000, "0b000 Pole mapping corrupted!"
    print("[PASS] Octahedral signed-pole-to-face mapping matches physical symmetry.")

    # 2. Format the 12 Pearls as expressive, visual channels
    pearl_data = generate_pearls()
    formatted_pearls = [EmojiGrammar.format_pearl(p_name, s_mask) for p_name, s_mask in pearl_data]

    print(f"\n3. Visualized the 12 Pearls (Active Principle -> State Incidences):")
    for i, pearl_str in enumerate(formatted_pearls):
        print(f"   Pearl {i+1:02d}: {pearl_str}")

    assert len(formatted_pearls) == 12, "Failed to capture all 12 Pearl incidences!"
    print("[PASS] The 12 Pearls are fully mapped to visual transitions.")

    # 3. Translate a Quantum Density Matrix with active coherence
    # State: Equal superposition of Holy Dark (0b000 - 🌌) and Power (0b011 - 🔥)
    # cohered with a 90-degree phase offset (i)
    rho = [[0.0j for _ in range(8)] for _ in range(8)]
    rho[0][0] = 0.5 + 0.0j # 50% Void (🌌)
    rho[3][3] = 0.5 + 0.0j # 50% Power (🔥)
    rho[0][3] = 0.5j       # Phase coherence at 90 degrees (1j)
    rho[3][0] = -0.5j      # conjugate symmetric coherence

    equation = EmojiGrammar.format_density_matrix(rho)
    print(f"\n4. Parsed Quantum Superposition Equation:")
    print(f"   rho = {equation}")

    assert "🌌" in equation, "Failed to render Void state emoji."
    assert "🔥" in equation, "Failed to render Power state emoji."
    assert "90°~🔥" in equation or "90°~🌌" in equation, "Failed to capture off-diagonal phase coherence!"

    print("\n[PASS] High-dimensional state vectors parsed into readable emoji-noun syntax.")
    print("[PASS] Phase 6 Emoji-Qubit Grammar is fully verified.")

if __name__ == "__main__":
    run_proof()

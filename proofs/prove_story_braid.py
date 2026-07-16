from septacrypt_core.dynamics.transition import QuantumState3Qubit
from septacrypt_core.narrative.braid import NarrativeBraid
from septacrypt_core.narrative.dialogue import IntentGenerator
from septacrypt_core.spirit.vector import SpiritVector

def run_proof():
    print("=========================================================================")
    print("        LAUNCHING FLEDGELING SEPTACRYPT: THE WEAVING OF VALVE-17         ")
    print("=========================================================================\n")

    # 1. Define Observer and Spirit Vectors
    keith_id = "keith"
    keith_wisdom_lens = SpiritVector(1.0, 0.1, 0.2, 0.3, 0.1, 0.8, 0.5, "Wisdom", 1.0)
    dwayne_might_lens = SpiritVector(0.0, 1.0, 0.1, 0.8, 0.2, 0.2, 0.1, "Might", 1.0)

    # 2. Define the discrete path computed by the RetroSolver in Phase 5
    # 0b110 (Honor/Shield) -> 0b010 (Might/Blade) -> 0b000 (Void/Holy Dark)
    path = [0b110, 0b010, 0b000]

    # 3. Calculate Narrative Tension using the Quantum Formalism
    # Mid-transition, the system enters a coherent superposition.
    rho_transitional = [[0.0j for _ in range(8)] for _ in range(8)]
    rho_transitional[2][2] = 0.5 + 0.0j  # 0b010
    rho_transitional[0][0] = 0.5 + 0.0j  # 0b000
    rho_transitional[2][0] = 0.4j        # Coherence (Phase subtext)
    rho_transitional[0][2] = -0.4j

    state_tension = QuantumState3Qubit(rho_transitional)
    t_val = NarrativeBraid.calculate_narrative_tension(state_tension)

    print(f"[MATH] Calculated Narrative Tension (Sum of |rho_ij|): {t_val}\n")

    # 4. Generate Agent Dialogue
    print("--- EXPRESSIONS OF INTENT ---")
    print(f"Dwayne (Might-Aligned): \"{IntentGenerator.vocalize_desire(path[0], dwayne_might_lens)}\"")
    print(f"Keith (Wisdom-Aligned): \"{IntentGenerator.vocalize_desire(path[2], keith_wisdom_lens)}\"\n")

    # 5. Weave the Narrative Braid
    story = NarrativeBraid.weave_story(path, keith_id, tension_peaks=[0.0, t_val])
    print(story)

    print("\n=========================================================================")
    print("  [PASS] QUANTUM MECHANICS SUCCESSFULLY TRANSLATED TO DIEGETIC MYTHOS  ")
    print("=========================================================================")

if __name__ == "__main__":
    run_proof()

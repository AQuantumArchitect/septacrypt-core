"""The interactive Fledgeling terminal — WAIT (evolve), LOOK (collapse one
component via a real weak measurement, rippling to its entangled peers),
WEAVE (retro-insert a timeline path), STATUS.

Operates directly on a CumulantCluster, not through GameHost. GameHost.beliefs()
needs a registered DomainSpec (register_world raises ValueError with none), and
routing our hand-picked ZZ couplings through that declarative pipeline is a
separate, larger task than this REPL — see scenario/reactor.py's docstring.
"""
import random

from ..scenario.reactor import build_entangled_reactor, ROLES
from ..narrative.weaver import EndlessKnotWeaver
from ..narrative.lexicon import LoreLexicon
from ..geometry.atlas import bloch_to_septacrypt


class SeptacryptREPL:
    def __init__(self):
        self.cluster = build_entangled_reactor()
        self.attention_budget = 10.0

    def get_current_q3_state(self) -> int:
        """Reads all 3 roles' Bloch vectors and collapses them to a Q3 state mask.
        Order matches geometry/atlas.py's axis convention: father, son, spirit —
        i.e. valve_17 (structure) = father, coolant_pump (energy) = son,
        temp_sensor (information) = spirit."""
        vectors = [
            tuple(self.cluster.role_bloch("valve_17")),
            tuple(self.cluster.role_bloch("coolant_pump")),
            tuple(self.cluster.role_bloch("temp_sensor")),
        ]
        return bloch_to_septacrypt(vectors)

    def execute_command(self, cmd_string: str) -> str:
        parts = cmd_string.strip().split()
        if not parts:
            return ""

        cmd = parts[0].upper()

        if cmd == "WAIT":
            # dt_scale=5.0 (effective step = cluster.dt * 5.0 = 0.5) was empirically
            # confirmed to blow up this RK4 integration within 2-3 steps (|z| -> 1e3+,
            # nonsense for a Bloch coordinate bounded in [-1,1]). dt_scale=1.0 (effective
            # step = 0.1, matching the cluster's own configured dt) stays bounded.
            self.cluster.step(dt_scale=1.0)
            state_mask = self.get_current_q3_state()
            lore = LoreLexicon.get_state_lore(state_mask)
            return f"[TIME] The manifold drifts. Current resonance: {lore['emoji']} {lore['name']}."

        elif cmd == "LOOK":
            if len(parts) < 2:
                return f"Usage: LOOK <component> (one of {', '.join(ROLES)})"
            role = parts[1].lower()
            if role not in self.cluster.role_index:
                return f"[ERROR] Unknown component '{role}'. Try one of {', '.join(ROLES)}."
            if self.attention_budget < 1.0:
                return "[FOG] You lack the attention to pierce the aether."
            self.attention_budget -= 1.0

            idx = self.cluster.role_index[role]
            z_before = float(self.cluster.role_bloch(role)[2])
            # Bloch z -> outcome probability (same (z+1)/2 convention GameHost.beliefs() uses).
            p_plus = (z_before + 1.0) / 2.0
            outcome = 1.0 if random.random() < p_plus else -1.0

            # Real Belavkin weak measurement (strength=1.0 = a hard projective collapse).
            # This is the mechanism that actually propagates the collapse to entangled
            # peers through the e2 cross-correlations — a manual e1[:, 2] snap never
            # touches e2 and would leave peers completely unaffected.
            self.cluster.measure_qubit(idx, record_z=outcome, strength=1.0)

            state_mask = self.get_current_q3_state()
            lore = LoreLexicon.get_state_lore(state_mask)
            peer_report = ", ".join(
                f"{r}: z={self.cluster.role_bloch(r)[2]:.3f}" for r in ROLES if r != role
            )
            return (
                f"[COLLAPSE] You pierce the fog around {role}. Outcome: z={outcome:+.0f}.\n"
                f"[COLLAPSE] Reality snaps toward {lore['emoji']} {lore['name']}.\n"
                f"[RIPPLE] Entangled peers shift -- {peer_report}\n"
                f"[FOG] {self.attention_budget:.0f} attention remains."
            )

        elif cmd == "WEAVE":
            if len(parts) < 3:
                return "Usage: WEAVE <start_mask> <end_mask> (e.g., WEAVE 6 0)"
            try:
                start = int(parts[1])
                end = int(parts[2])
            except ValueError:
                return "[ERROR] Masks must be integers (0-7)."
            if not (0 <= start <= 7 and 0 <= end <= 7):
                return "[ERROR] Masks must be in range 0-7."
            return EndlessKnotWeaver.weave_insertion(start, end)

        elif cmd == "STATUS":
            state_mask = self.get_current_q3_state()
            lore = LoreLexicon.get_state_lore(state_mask)
            per_role = ", ".join(f"{r}: z={self.cluster.role_bloch(r)[2]:.3f}" for r in ROLES)
            return (
                f"[STATUS] Ground logic senses {lore['emoji']} {lore['name']}. "
                f"({per_role}) Attention: {self.attention_budget:.0f}"
            )

        return f"Unknown command: {cmd}. Try WAIT, LOOK <component>, WEAVE <a> <b>, or STATUS."

"""Interactive terminal — thin CLI over GameSession."""
from __future__ import annotations

from ..api.session import GameSession
from ..scenario.reactor import ROLES


class SeptacryptREPL:
    def __init__(self, seed: int | None = 0):
        self.game = GameSession(
            mode="reactor",
            seed=seed,
            enable_ledger=True,
            private_observers=False,
            attention_budget=10.0,
        )

    @property
    def cluster(self):
        return self.game.cluster

    @property
    def attention_budget(self):
        return self.game.attention_budget

    @attention_budget.setter
    def attention_budget(self, value):
        self.game.attention_budget = value

    def get_current_q3_state(self) -> int:
        return self.game._q3_mask()

    def execute_command(self, cmd_string: str) -> str:
        parts = cmd_string.strip().split()
        if not parts:
            return ""

        cmd = parts[0].upper()

        if cmd == "WAIT":
            state = self.game.wait()
            lore = state["meta"]["current_mythos"]
            return f"[TIME] The manifold drifts. Current resonance: {lore['emoji']} {lore['name']}."

        if cmd == "LOOK":
            if len(parts) < 2:
                return f"Usage: LOOK <component> (one of {', '.join(ROLES)})"
            role = parts[1].lower()
            if role not in self.game.cluster.role_index:
                return f"[ERROR] Unknown component '{role}'. Try one of {', '.join(ROLES)}."
            before = self.game.attention_budget
            state = self.game.look("player", role)
            if before is not None and self.game.attention_budget == before:
                return "[FOG] You lack the attention to pierce the aether."
            lore = state["meta"]["current_mythos"]
            z = state["entities"][role]["raw_metrics"]["z_axis"]
            peers = ", ".join(
                f"{r}: z={state['entities'][r]['raw_metrics']['z_axis']:.3f}"
                for r in ROLES
                if r != role
            )
            return (
                f"[COLLAPSE] You pierce the fog around {role}. Outcome reflected in state.\n"
                f"[COLLAPSE] Reality snaps toward {lore['emoji']} {lore['name']}.\n"
                f"[RIPPLE] Peers -- {peers}\n"
                f"[FOG] {self.game.attention_budget:.0f} attention remains.\n"
                f"[LEDGER] head={state['meta'].get('ledger_head')}"
            )

        if cmd == "WEAVE":
            if len(parts) < 3:
                return "Usage: WEAVE <start_mask> <end_mask> (e.g., WEAVE 6 0)"
            try:
                start = int(parts[1])
                end = int(parts[2])
            except ValueError:
                return "[ERROR] Masks must be integers (0-7)."
            if not (0 <= start <= 7 and 0 <= end <= 7):
                return "[ERROR] Masks must be in range 0-7."
            return self.game.weave(start, end)

        if cmd == "STATUS":
            state = self.game.status("player")
            lore = state["meta"]["current_mythos"]
            per_role = ", ".join(
                f"{r}: z={state['entities'][r]['raw_metrics']['z_axis']:.3f}" for r in ROLES
            )
            return (
                f"[STATUS] {lore['emoji']} {lore['name']}. ({per_role}) "
                f"Attention: {self.game.attention_budget:.0f} "
                f"Ledger: {state['meta'].get('ledger_head')}"
            )

        if cmd == "HISTORY":
            lines = self.game.history()
            if not lines:
                return "[LEDGER] empty"
            return "\n".join(
                f"{h['stamp_id']} {h['event_kind']} obs={h['observer_id']} berry={h['berry_sig']}"
                for h in lines
            )

        if cmd == "STIR":
            self.game.stir("player")
            return "[STIR] Transverse kick applied to unlock poles."

        return (
            "Unknown command. Try WAIT, LOOK <component>, WEAVE <a> <b>, "
            "STATUS, HISTORY, or STIR."
        )

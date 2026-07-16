"""The Fledgeling Kernel API -- a clean, JSON-serializable presentation surface
over the entangled reactor cluster, for a game engine (Godot/Blender) or UI
client to poll every frame.

Does not route through GameHost.engine/field (same reasoning as scenario/reactor.py
and repl/terminal.py: that needs a real registered DomainSpec, which is separate,
larger work). `host` is kept only for its lightweight `.turn` counter, which works
on a bare unregistered GameHost since it never touches `.engine`.
"""
import random
from typing import Any, Dict, List

import numpy as np

from umwelt.host.api import GameHost

from ..scenario.reactor import ROLES, build_entangled_reactor
from ..narrative.lexicon import LoreLexicon
from ..geometry.atlas import bloch_to_septacrypt

# Matches geometry/atlas.py's axis convention: father, son, spirit.
_AXIS_ROLE_ORDER = ("valve_17", "coolant_pump", "temp_sensor")


class FledgelingKernelAPI:
    """
    The unified presentation surface for Fledgeling.
    Provides raw quantum metrics for procedural shaders (Godot/Blender)
    and semantic lore for UI/Dialogue rendering.
    """
    def __init__(self, host: GameHost, domain_cluster_name: str = "Repair_Station"):
        self.host = host
        self.cluster_name = domain_cluster_name
        self.story_log: List[str] = []
        self.cluster = build_entangled_reactor()

    def get_cluster(self):
        return self.cluster

    @staticmethod
    def _cluster_tension(cluster) -> float:
        """Sum of |connected zz-correlation| across all qubit pairs -- the cumulant
        analog of 'off-diagonal coherence magnitude'. cluster.e2 is a (n,n,3,3)
        cumulant tensor, not a flat density matrix, so it can't be fed directly
        into NarrativeBraid.calculate_narrative_tension_from_raw (which assumes
        an NxN matrix of scalar entries -- confirmed by testing it: doing so
        raises TypeError on the final round(), since e2[i][j] is itself a 3x3
        block, not a complex number)."""
        n = cluster.n_qubits
        tension = 0.0
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                conn = cluster.e2[i, j] - np.outer(cluster.e1[i], cluster.e1[j])
                tension += float(abs(conn[2, 2]))
        return round(tension, 5)

    def _current_q3_mask(self, cluster) -> int:
        bloch_vecs = [cluster.role_bloch(role) for role in _AXIS_ROLE_ORDER]
        return bloch_to_septacrypt(bloch_vecs)

    def fetch_render_state(self, observer_id: str) -> Dict[str, Any]:
        """
        The master frame-update payload. Game engines call this to render the scene.
        """
        cluster = self.get_cluster()

        global_tension = self._cluster_tension(cluster)
        lore = LoreLexicon.get_state_lore(self._current_q3_mask(cluster))

        entities_payload = {}
        for role in cluster.qubit_roles:
            bloch = cluster.role_bloch(role)
            x, y, z = float(bloch[0]), float(bloch[1]), float(bloch[2])
            radius = (x ** 2 + y ** 2 + z ** 2) ** 0.5

            entities_payload[role] = {
                "raw_metrics": {
                    "z_axis": z,           # Classical state (-1 to 1). Maps to animation frames.
                    "radius": radius,      # Confidence (0 to 1). Inverse maps to object blur/fog.
                    "phase_x": x,          # Quantum coherence X.
                    "phase_y": y,          # Quantum coherence Y.
                },
                "semantic": {
                    "inferred_state": "active" if z > 0 else "latent",
                },
            }

        return {
            "meta": {
                "observer": observer_id,
                "turn": self.host.turn,
                "global_tension": global_tension,
                "current_mythos": lore,
            },
            "entities": entities_payload,
            "narrative_log": self.story_log[-5:],  # Last 5 narrative events for UI chatbox
        }

    def command_measure(self, observer_id: str, target_role: str) -> Dict[str, Any]:
        """The 'LOOK' action. Collapses the fog via a real Belavkin weak measurement
        (CumulantCluster.measure_qubit), which propagates to entangled peers through
        the e2 cross-correlations -- not a manual e1 snap, which would only touch
        the measured qubit and never ripple to anything else."""
        cluster = self.get_cluster()
        idx = cluster.role_index.get(target_role)
        if idx is not None:
            z_before = float(cluster.role_bloch(target_role)[2])
            p_plus = (z_before + 1.0) / 2.0
            outcome = 1.0 if random.random() < p_plus else -1.0
            cluster.measure_qubit(idx, record_z=outcome, strength=1.0)

            lore = LoreLexicon.get_state_lore(self._current_q3_mask(cluster))
            self.story_log.append(
                f"{observer_id.capitalize()} pierced the fog of {target_role}. "
                f"The manifold snapped to {lore['emoji']}."
            )

        return self.fetch_render_state(observer_id)

    def command_evolve(self, dt_scale: float = 1.0) -> Dict[str, Any]:
        """Advances the Lindblad/cumulant engine, drifting the state and building
        tension. dt_scale=1.0 (not 5.0) -- empirically confirmed stable for this
        cluster's gamma/dt/coupling constants; 5.0 blows the RK4 integration up
        past |z|=1000 within 2-3 steps (see repl/terminal.py's WAIT for the same fix)."""
        cluster = self.get_cluster()
        cluster.step(dt_scale=dt_scale)
        return self.fetch_render_state("system")

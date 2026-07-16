import random
from typing import Tuple
from .transition import QuantumState3Qubit

class MeasurementEngine:
    """
    The core gameplay mechanic. Observing a system forces it to resolve its superposition,
    collapsing into a pure classical basis state based on its probability distribution.
    """
    @staticmethod
    def measure_computational_basis(rho: QuantumState3Qubit, rng_seed: int = None) -> Tuple[int, QuantumState3Qubit]:
        """
        Simulates a measurement in the standard Z-basis.
        Returns the observed classical state mask and the new collapsed pure state.
        """
        if rng_seed is not None:
            random.seed(rng_seed)

        probabilities = rho.get_diagonal()

        # Ensure probabilities sum to 1.0 (handling minor float imprecision)
        total_p = sum(probabilities)
        if total_p == 0:
            raise ValueError("Cannot measure a null state space.")

        normalized_probs = [p / total_p for p in probabilities]

        roll = random.random()
        cumulative = 0.0

        for state_mask, p in enumerate(normalized_probs):
            cumulative += p
            if roll <= cumulative:
                # The wave function collapses to this specific pure state
                collapsed_state = QuantumState3Qubit.from_classical_state(state_mask)
                return state_mask, collapsed_state

        # Fallback for extreme float rounding errors
        return 7, QuantumState3Qubit.from_classical_state(7)

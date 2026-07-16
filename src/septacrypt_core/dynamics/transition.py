import math
from typing import List, Tuple, Dict, Any

class QuantumState3Qubit:
    """
    Represents a 3-qubit quantum state using an 8x8 density matrix (rho)
    to handle mixed states and coherence. Written in pure Python to ensure
    zero external environment dependencies.
    """
    def __init__(self, matrix: List[List[complex]] = None):
        if matrix is None:
            # Default to Ground/Void state |000><000|
            self.matrix = [[0.0j for _ in range(8)] for _ in range(8)]
            self.matrix[0][0] = 1.0 + 0.0j
        else:
            self.matrix = matrix

    @classmethod
    def from_classical_state(cls, state_mask: int) -> 'QuantumState3Qubit':
        """
        Creates a pure state representing one of the 8 basis states (0b000 to 0b111).
        """
        if not (0 <= state_mask <= 7):
            raise ValueError("State mask must be between 0 and 7.")
        matrix = [[0.0j for _ in range(8)] for _ in range(8)]
        matrix[state_mask][state_mask] = 1.0 + 0.0j
        return cls(matrix)

    def get_diagonal(self) -> List[float]:
        """
        Extracts the diagonal populations (measurement probabilities).
        """
        return [self.matrix[i][i].real for i in range(8)]

    def populations_and_coherence_magnitudes_match(
        self, other: "QuantumState3Qubit", tolerance: float = 1e-6
    ) -> bool:
        """
        Necessary (not always sufficient) check: equal diagonal populations and equal
        off-diagonal coherence *magnitudes*. This is weaker than true local-phase
        gauge equivalence (rho' = U_local rho U_local^H); different phase-loop
        structures can share magnitudes without being related by local unitaries.
        """
        for i in range(8):
            for j in range(8):
                val_self = self.matrix[i][j]
                val_other = other.matrix[i][j]
                if i == j:
                    if abs(val_self.real - val_other.real) > tolerance:
                        return False
                else:
                    if abs(abs(val_self) - abs(val_other)) > tolerance:
                        return False
        return True

    def is_gauge_equivalent(self, other: "QuantumState3Qubit", tolerance: float = 1e-6) -> bool:
        """Deprecated name for populations_and_coherence_magnitudes_match (not full gauge)."""
        return self.populations_and_coherence_magnitudes_match(other, tolerance)



class TransitionVerifier:
    """
    Enforces the physical graph constraints of the Septacrypt Q3 hypercube.
    """
    @staticmethod
    def is_q3_adjacent(state_a: int, state_b: int) -> bool:
        """
        Strict Graph Theory Check: Are the two states connected by an edge on Q3?
        True if and only if their Hamming distance is exactly 1 (single-bit flip).
        """
        xor_val = state_a ^ state_b
        return xor_val != 0 and (xor_val & (xor_val - 1)) == 0

    @classmethod
    def verify_step(cls, from_mask: int, to_mask: int) -> bool:
        """
        Rejects illegal non-local teleportations across state space.
        """
        return cls.is_q3_adjacent(from_mask, to_mask)

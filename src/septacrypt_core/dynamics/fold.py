from typing import List


class SpectralFolder:
    """
    Subspace projection fold primitive: rho_eff = (V^H rho V) / Tr(...).

    V is currently supplied by the caller (manual basis selector). This is not
    yet automatic spectral folding from Hamiltonian / Lindblad eigenspaces.
    """

    @staticmethod
    def conjugate_transpose(matrix: List[List[complex]]) -> List[List[complex]]:
        """Computes the conjugate transpose (adjoint) V^H of a complex matrix."""
        rows = len(matrix)
        cols = len(matrix[0])
        return [[matrix[r][c].conjugate() for r in range(rows)] for c in range(cols)]

    @staticmethod
    def matmul(A: List[List[complex]], B: List[List[complex]]) -> List[List[complex]]:
        """Standard complex matrix multiplication."""
        rows_A, cols_A = len(A), len(A[0])
        rows_B, cols_B = len(B), len(B[0])
        if cols_A != rows_B:
            raise ValueError(f"Incompatible matrix dimensions for multiplication: {cols_A} vs {rows_B}")

        result = [[0.0j for _ in range(cols_B)] for _ in range(rows_A)]
        for i in range(rows_A):
            for j in range(cols_B):
                s = 0.0j
                for k in range(cols_A):
                    s += A[i][k] * B[k][j]
                result[i][j] = s
        return result

    @staticmethod
    def trace(matrix: List[List[complex]]) -> complex:
        """Computes the diagonal sum of a square matrix."""
        n = len(matrix)
        return sum(matrix[i][i] for i in range(n))

    @classmethod
    def isometry_error(cls, V: List[List[complex]]) -> float:
        """Max abs deviation of V^H V from identity (0 = perfect isometry columns)."""
        V_dagger = cls.conjugate_transpose(V)
        gram = cls.matmul(V_dagger, V)
        n = len(gram)
        err = 0.0
        for i in range(n):
            for j in range(n):
                target = 1.0 + 0.0j if i == j else 0.0j
                err = max(err, abs(gram[i][j] - target))
        return float(err)

    @classmethod
    def assert_isometry(cls, V: List[List[complex]], tolerance: float = 1e-9) -> None:
        err = cls.isometry_error(V)
        if err > tolerance:
            raise ValueError(f"V is not an isometry: ||V^H V - I||_max = {err} > {tolerance}")

    @classmethod
    def fold_state(
        cls,
        rho: List[List[complex]],
        V: List[List[complex]],
        *,
        require_isometry: bool = True,
        isometry_tolerance: float = 1e-9,
    ) -> List[List[complex]]:
        """
        Projects high-dimensional density matrix rho down to a low-dimensional state space.
        Applies: rho_eff = (V^H . rho . V) / Tr(V^H . rho . V).
        """
        if require_isometry:
            cls.assert_isometry(V, isometry_tolerance)

        V_dagger = cls.conjugate_transpose(V)

        temp = cls.matmul(V_dagger, rho)
        unnormalized_projected = cls.matmul(temp, V)

        tr = cls.trace(unnormalized_projected)
        if abs(tr) < 1e-12:
            raise ValueError("Zero trace encountered during projection fold. Check isometry definition.")

        folded_rho = [[val / tr for val in row] for row in unnormalized_projected]
        return folded_rho


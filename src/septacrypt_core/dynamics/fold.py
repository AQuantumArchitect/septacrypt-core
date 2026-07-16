from typing import List

class SpectralFolder:
    """
    Performs dimensional reduction on high-dimensional quantum states
    via isometric projections. Written in pure Python to ensure
    zero dependencies and absolute math precision.
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
    def fold_state(cls, rho: List[List[complex]], V: List[List[complex]]) -> List[List[complex]]:
        """
        Projects high-dimensional density matrix rho down to a low-dimensional state space.
        Applies: rho_eff = (V^H . rho . V) / Tr(V^H . rho . V).
        """
        V_dagger = cls.conjugate_transpose(V)

        # Step 1: V^H . rho
        temp = cls.matmul(V_dagger, rho)
        # Step 2: V^H . rho . V
        unnormalized_projected = cls.matmul(temp, V)

        # Step 3: Compute trace for normalization to preserve probability interpretation
        tr = cls.trace(unnormalized_projected)
        if abs(tr) < 1e-12:
            raise ValueError("Zero trace encountered during projection fold. Check isometry definition.")

        # Step 4: Scale elements by 1/Tr
        folded_rho = [[val / tr for val in row] for row in unnormalized_projected]
        return folded_rho

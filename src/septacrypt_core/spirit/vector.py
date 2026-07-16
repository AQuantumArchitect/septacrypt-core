from dataclasses import dataclass, replace
from typing import Dict, List, Tuple, Any

@dataclass(frozen=True)
class SpiritVector:
    wisdom: float
    might: float
    wealth: float
    power: float
    glory: float
    honor: float
    blessing: float
    frame_id: str
    confidence: float

    def dot(self, other: 'SpiritVector') -> float:
        """Computes semantic alignment score between vectors."""
        return (
            self.wisdom * other.wisdom +
            self.might * other.might +
            self.wealth * other.wealth +
            self.power * other.power +
            self.glory * other.glory +
            self.honor * other.honor +
            self.blessing * other.blessing
        )

class SpiritFrameRegistry:
    """
    Holds different cultural or agent interpretive lenses.
    Maps our 7D vector down to a navigable 3D projection.
    """
    DEFAULT_AXES = {
        "001": "wisdom",
        "010": "might",
        "100": "wealth",
        "011": "power",
        "101": "glory",
        "110": "honor",
        "111": "blessing"
    }

    @staticmethod
    def project_to_3d(vector: SpiritVector) -> Tuple[float, float, float]:
        """
        Projects 7D vector into a 3D coordinate system (x, y, z)
        by grouping intellectual, operational, and material coordinates.
        """
        x = vector.wisdom + 0.5 * vector.power + 0.5 * vector.glory
        y = vector.might + 0.5 * vector.power + 0.5 * vector.honor
        z = vector.wealth + 0.5 * vector.glory + 0.5 * vector.honor + vector.blessing
        return (round(x, 2), round(y, 2), round(z, 2))


class SpiritScorer:
    """
    Ranks physically valid history candidates based on agent or cultural frames.
    Hard physical gates are respected first; spirit coordinates serve as preference filters.
    """
    @staticmethod
    def score_candidate_path(
        path: List[int],
        bias_frame: SpiritVector,
        state_values: Dict[int, SpiritVector]
    ) -> float:
        """
        Calculates cumulative path resonance.
        Formula: sum(state_spirit_vector . bias_frame)
        """
        total_score = 0.0
        for state in path:
            vector = state_values.get(state)
            if vector:
                total_score += vector.dot(bias_frame)
        return round(total_score, 3)

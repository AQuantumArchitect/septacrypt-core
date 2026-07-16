from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional

@dataclass(frozen=True)
class CompositeNode:
    """
    An immutable tree structure defining components, capacities, resource vectors,
    and system boundaries at a specific recursive tier.
    """
    entity_type: str
    entity_id: str
    children: Tuple['CompositeNode', ...] = ()
    requirements: Tuple[str, ...] = ()
    productions: Tuple[str, ...] = ()
    invariants: Tuple[str, ...] = ()
    spirit_priors: Optional[Dict[str, float]] = None

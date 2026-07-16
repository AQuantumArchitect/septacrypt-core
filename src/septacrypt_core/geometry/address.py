from typing import Tuple, Iterator

class ScaleAddress:
    """
    An immutable, normalized hierarchical location coordinate.
    Enforces case-insensitivity and structural containment checking.
    """
    def __init__(self, segments: Tuple[str, ...]):
        # Preserve stripped original casing for display and positional access
        self._display_segments = tuple(s.strip() for s in segments)
        # Normalize all segments to lowercase and strip whitespace for comparison/hashing
        self.segments = tuple(s.strip().lower() for s in segments)
        self.display_path = "/".join(self._display_segments)

    def contains(self, segment: str) -> bool:
        """Enforces case-insensitive containment checking."""
        return segment.strip().lower() in self.segments

    def is_subpath_of(self, other: 'ScaleAddress') -> bool:
        """Returns True if self is a prefix/parent path of the other address."""
        if len(self.segments) > len(other.segments):
            return False
        return other.segments[:len(self.segments)] == self.segments

    def __getitem__(self, index):
        return self._display_segments[index]

    def __len__(self) -> int:
        return len(self._display_segments)

    def __iter__(self) -> Iterator[str]:
        return iter(self._display_segments)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScaleAddress):
            return False
        return self.segments == other.segments

    def __hash__(self) -> int:
        return hash(self.segments)

    def __repr__(self) -> str:
        return f"ScaleAddress({self.segments})"

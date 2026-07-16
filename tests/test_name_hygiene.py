"""ADR-001: ledger vocabulary is Knot-*; plain belief-face names are umwelt's.

Old names keep working for one release but must warn.
"""
import warnings

from septacrypt_core.ledger.stamp import KnotIntent, KnotObservation


def test_deprecated_aliases_warn():
    import septacrypt_core.ledger.stamp as stamp

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert stamp.Observation is KnotObservation
        assert stamp.Intent is KnotIntent
    kinds = [w.category for w in caught]
    assert kinds.count(DeprecationWarning) == 2


def test_no_plain_belief_face_definitions():
    """septacrypt-core must not (re)define umwelt's belief-face classes."""
    import septacrypt_core

    for name in ("GameHost", "WorldSession"):
        assert not hasattr(septacrypt_core, name)

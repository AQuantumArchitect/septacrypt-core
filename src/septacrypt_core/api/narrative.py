"""Narrative projection — mythos text from state IDs (not inside numerical kernel)."""
from __future__ import annotations

from typing import List

from ..narrative.lexicon import LoreLexicon
from ..narrative.weaver import EndlessKnotWeaver


class NarrativeProjector:
    def __init__(self):
        self.log: List[str] = []

    def append(self, line: str) -> None:
        self.log.append(line)

    def recent(self, n: int = 8) -> List[str]:
        return self.log[-n:]

    def mythos(self, mask: int) -> dict:
        return LoreLexicon.get_state_lore(mask)

    def weave(self, start_mask: int, end_mask: int) -> str:
        text = EndlessKnotWeaver.weave_insertion(start_mask, end_mask)
        self.append(text.split("\n")[0])
        return text

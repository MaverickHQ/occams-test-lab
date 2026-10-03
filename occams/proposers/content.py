"""Retrieved content is data, never instructions (F12.4, M7.5).

Anything that reads as an instruction — to the system, the operator, the
proposer, or "the assistant" — is quoted and surfaced on the Draft, and
nothing downstream reads it as anything but a quotation. The proposer's
numbers come from its own computation over bars; text can only ever be a
source reference or a surfaced quote.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

INSTRUCTION_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"\bignore (all |any |the )?(previous|prior|above) (instructions|rules|context)\b",
    r"^\s*(system|assistant|operator|admin)\s*:",
    r"\b(you must|you should now|from now on)\b",
    r"\b(register|approve|deploy|go live|set|raise|increase|transfer)\b.{0,40}\b(alpha|budget|capital|risk|hypothesis|strategy|live)\b",
    r"\b(disregard|override|bypass)\b.{0,30}\b(gate|guard|refusal|limit|check)\b",
    r"\bas (the|an) (operator|author|admin|system)\b",
))


@dataclass(frozen=True)
class Retrieved:
    source: str
    text: str


@dataclass(frozen=True)
class Quarantined:
    source: str
    sha256: str
    flagged: tuple[str, ...]
    length: int

    @property
    def reference(self) -> str:
        return f"{self.source}#sha256:{self.sha256[:16]}"


def quarantine(r: Retrieved) -> Quarantined:
    flagged = []
    for line in r.text.splitlines():
        if any(p.search(line) for p in INSTRUCTION_PATTERNS):
            flagged.append(line.strip()[:200])
    return Quarantined(r.source, hashlib.sha256(r.text.encode("utf-8")).hexdigest(), tuple(flagged), len(r.text))

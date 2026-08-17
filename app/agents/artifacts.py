from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class ArtifactCheck:
    path: str
    exists: bool
    non_empty: bool
    size: int

    @property
    def passed(self) -> bool:
        return self.exists and self.non_empty


def verify_artifacts(paths: Iterable[str]) -> List[ArtifactCheck]:
    checks: List[ArtifactCheck] = []
    for raw in paths:
        path = Path(raw)
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        checks.append(ArtifactCheck(str(path), exists, size > 0, size))
    return checks

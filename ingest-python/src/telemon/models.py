from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass(frozen=True)
class Observation:
    ts_utc: str
    service_id: str
    iso2: str
    metric: str
    value: int
    source: str
    confidence: float = 0.6
    raw: Optional[dict[str, Any]] = None

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

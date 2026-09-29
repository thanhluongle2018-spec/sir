from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NotifyPayload:
    title: str
    body: str
    url: str | None = None
    image_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class NotifyResult:
    ok: bool
    message: str = ""
    error: str | None = None

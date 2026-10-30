"""Canonical typed refusal record."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, NoReturn, Tuple, TypeVar, TYPE_CHECKING, cast

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")
F = TypeVar("F")

import re
import unicodedata

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return unicodedata.normalize("NFC", value.strip())


def _require_identifier(value: Any, field: str) -> str:
    normalized = _require_text(value, field)
    if _IDENTIFIER.fullmatch(normalized) is None:
        raise ValueError(f"{field} must be a canonical identifier")
    return normalized


@dataclass(frozen=True)
class Refusal:
    code: str
    message: str
    locus: str = ""
    details: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _require_identifier(self.code, "code"))
        object.__setattr__(self, "message", _require_text(self.message, "message"))
        if self.locus:
            object.__setattr__(self, "locus", _require_text(self.locus, "locus"))
        normalized = tuple((_require_text(k, "detail key"), str(v)) for k, v in self.details)
        if len({key for key, _ in normalized}) != len(normalized):
            raise ValueError("refusal detail keys must be unique")
        object.__setattr__(self, "details", tuple(sorted(normalized)))

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "locus": self.locus,
            "details": {key: value for key, value in self.details},
        }

"""Canonical immutable Err result variant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, NoReturn, Tuple, TypeVar, TYPE_CHECKING, cast

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")
F = TypeVar("F")

if TYPE_CHECKING:
    from .result import Result


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

    @property
    def is_ok(self) -> bool:
        return False

    @property
    def is_err(self) -> bool:
        return True

    def unwrap(self) -> NoReturn:
        raise ValueError(f"cannot unwrap Err: {self.error}")

    def unwrap_err(self) -> E:
        return self.error

    def map(self, function: Callable[[T], U]) -> "Err[E]":
        del function
        return self

    def map_error(self, function: Callable[[E], F]) -> "Err[F]":
        return Err(function(self.error))

    def bind(self, function: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        del function
        return cast("Result[U, E]", self)

    def and_then(self, function: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        del function
        return cast("Result[U, E]", self)

    def recover(self, function: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        return function(self.error)

"""Canonical immutable Ok result variant."""

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
class Ok(Generic[T]):
    value: T

    @property
    def is_ok(self) -> bool:
        return True

    @property
    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_err(self) -> NoReturn:
        raise ValueError("cannot unwrap_err from Ok")

    def map(self, function: Callable[[T], U]) -> "Ok[U]":
        return Ok(function(self.value))

    def map_error(self, function: Callable[[E], F]) -> "Ok[T]":
        del function
        return self

    def bind(self, function: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return function(self.value)

    def and_then(self, function: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return function(self.value)

    def recover(self, function: Callable[[E], "Result[T, F]"]) -> "Ok[T]":
        del function
        return self

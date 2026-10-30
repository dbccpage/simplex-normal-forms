"""Stable public surface for the single canonical Result implementation."""

from __future__ import annotations
from typing import Callable, Iterable, List, Tuple, TypeVar, Union, cast
from .ok import Ok
from .err import Err
from .refusal import Refusal

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")

Result = Union[Ok[T], Err[E]]


def sequence(results: Iterable[Result[T, E]]) -> Result[Tuple[T, ...], E]:
    """Combine an iterable of Results into a Result containing a tuple of values."""
    values: List[T] = []
    for r in results:
        if r.is_err:
            return cast(Err[E], r)
        values.append(r.unwrap())
    return Ok(tuple(values))


def traverse(items: Iterable[T], function: Callable[[T], Result[U, E]]) -> Result[Tuple[U, ...], E]:
    """Map each item to a Result and accumulate into a tuple."""
    values: List[U] = []
    for item in items:
        r = function(item)
        if r.is_err:
            return cast(Err[E], r)
        values.append(r.unwrap())
    return Ok(tuple(values))


__all__ = ["Err", "Ok", "Refusal", "Result", "sequence", "traverse"]

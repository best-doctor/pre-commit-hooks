from __future__ import annotations
from typing import List, Iterable, TypeVar, Optional, Union

T = TypeVar('T')


def flat(some_list: Iterable[Iterable]) -> List:
    return [item for sublist in some_list for item in sublist]


def max_with_default(items: Iterable[T], default: Optional[T] = None) -> Union[T, int]:
    default = default or 0
    items = list(items)
    if not items and default is not None:
        return default
    return max(items)

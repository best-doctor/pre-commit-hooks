from __future__ import annotations

import typing


class SupportsLessThan(typing.Protocol):
    def __lt__(self, __other: typing.Any) -> bool:
        ...


T = typing.TypeVar('T', bound=SupportsLessThan)


def flat(some_list: typing.Iterable[typing.Iterable]) -> typing.List:
    return [item for sublist in some_list for item in sublist]


def max_with_default(
    items: typing.Iterable[T], default: typing.Optional[T] = None
) -> typing.Union[T, int]:
    default = default or 0
    items = list(items)
    if not items and default is not None:
        return default
    return max(items)

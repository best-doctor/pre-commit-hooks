from __future__ import annotations

import typing


def task(*args: list, **kwargs: dict) -> typing.Callable:
    def wrapper(func: typing.Callable) -> typing.Any:
        return func

    if callable(args[0]):
        return args[0]

    return wrapper


class AsyncTaskResult(typing.TypedDict):
    data: typing.Any
    errors: list
    warnings: list

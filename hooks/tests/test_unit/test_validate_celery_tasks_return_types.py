from __future__ import annotations

import pytest

from hooks.validate_celery_tasks_return_types import validate_return_types

VALID_CONTENT = """
@app.task(name='foo')
def foo() -> None:
    return 1

@app.task(name='bar')
def bar() -> AsyncTaskResult:
    return 1

@app.task(name='baz')
def baz() -> AsyncTaskResult | None:
    return 1
"""

INVALID_CONTENT = """
@app.task(name='foo')
def foo() -> int:
    return 1
"""


@pytest.mark.parametrize(
    ['file_content', 'errors_count'],
    (
        [VALID_CONTENT, 0],
        [INVALID_CONTENT, 1],
    ),
    ids=['valid', 'invalid'],
)
def test_validate_return_types(file_content, errors_count):
    errors = validate_return_types(file_content)
    assert len(errors) == errors_count

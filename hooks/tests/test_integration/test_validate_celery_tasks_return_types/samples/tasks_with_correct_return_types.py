from __future__ import annotations

from hooks.tests.test_integration.test_validate_celery_tasks_return_types.samples import app
from hooks.tests.test_integration.test_validate_celery_tasks_return_types.samples.app import AsyncTaskResult


@app.task(name='foo')
def foo() -> None:
    return 1


@app.task(name='bar')
def bar() -> AsyncTaskResult:
    return 1


@app.task
def baz() -> AsyncTaskResult | None:
    return 1


@app.task
def foobaz() -> None | AsyncTaskResult:
    return 1

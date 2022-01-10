from __future__ import annotations

from hooks.tests.test_integration.test_validate_celery_tasks_return_types.samples import app
from hooks.tests.test_integration.test_validate_celery_tasks_return_types.samples.app import AsyncTaskResult


@app.task(name='foo')
def foo() -> int:
    return 1


@app.task(name='bar')
def bar() -> str | None:
    return 'bar'


@app.task
def baz() -> AsyncTaskResult | str:
    return AsyncTaskResult() or 'foo'

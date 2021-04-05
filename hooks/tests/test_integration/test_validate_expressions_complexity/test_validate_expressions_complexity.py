from __future__ import annotations

import pathlib

from hooks.validate_expressions_complexity import get_file_errors

SAMPLE_FILE = pathlib.Path(__file__).parent / 'samples' / 'sample.py'


def test_get_file_errors():
    errors = list(get_file_errors(str(SAMPLE_FILE), max_expression_complexity=1.5, ignore_django_orm_queries=True))

    assert errors == []

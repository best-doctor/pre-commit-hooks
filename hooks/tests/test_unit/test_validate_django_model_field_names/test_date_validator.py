from __future__ import annotations

import pytest

from hooks.validate_django_model_field_names import date_validator


@pytest.mark.parametrize(
    ('field_name', 'expected_is_valid'), [
        ('finished_date', True),
        ('date', False),
        ('date_finished', False),
        ('finished_at', False),
    ]
)
def test_date_validator(field_name, expected_is_valid):
    assert date_validator.validate(field_name) is expected_is_valid

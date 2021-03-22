from __future__ import annotations

import pytest

from hooks.validate_django_model_field_names import datetime_validator


@pytest.mark.parametrize(
    ('field_name', 'expected_is_valid'), [
        ('finished_at', True),
        ('should_start_at', True),
        ('at', False),
        ('finished_date', False),
    ]
)
def test_datetime_validator(field_name, expected_is_valid):
    assert datetime_validator.validate(field_name) is expected_is_valid

from __future__ import annotations

import pytest

from hooks.validate_django_model_field_names import boolean_validator, date_validator, datetime_validator, get_validator


@pytest.mark.parametrize(
    ('field_type', 'expected_validator'), [
        ('DateField', date_validator),
        ('MyDateField', date_validator),
        ('MyDateExtraField', date_validator),
        ('DateTimeField', datetime_validator),
        ('MyDateTimeField', datetime_validator),
        ('DateTimeExtraField', datetime_validator),
        ('BooleanField', boolean_validator),
        ('NullBooleanField', boolean_validator),
        ('NullBooleanExtraField', boolean_validator),
        ('DateSerializer', None),
        ('CharField', None),
    ]
)
def test_get_validator(field_type, expected_validator):
    assert get_validator(field_type) is expected_validator

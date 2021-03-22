from __future__ import annotations

import pytest

from hooks.validate_django_model_field_names import boolean_validator


@pytest.mark.parametrize(
    ('field_name', 'expected_is_valid'), [
        ('is_accepted', True),
        ('was_migrated_from_specialties', True),
        ('has_public_link_access', True),
        ('needs_plastic_cards', True),
        ('should_allow_dispatch_for_disabled', True),
        ('franchise_was_changed', True),
        ('accepted', False),
        ('allow_dispatch_for_disabled', False),
        ('available_for_adults', False),
        ('need_med_consent', False),
        ('pay_lock', False),
    ]
)
def test_boolean_validator(field_name, expected_is_valid):
    assert boolean_validator.validate(field_name) is expected_is_valid

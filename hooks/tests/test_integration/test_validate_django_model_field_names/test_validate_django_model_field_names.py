from __future__ import annotations

from pathlib import Path

from hooks.utils.ast_helpers import iterate_files_in
from hooks.validate_django_model_field_names import Error, date_validator, datetime_validator, validate

SAMPLES_DIR = Path(__file__).parent.resolve() / 'samples'


def _date_error(rel_path, lineno, field_name):
    return Error(str(SAMPLES_DIR / rel_path), lineno, field_name, 'DateField', date_validator)


def _datetime_error(rel_path, lineno, field_name, field_type='DateTimeField'):
    return Error(str(SAMPLES_DIR / rel_path), lineno, field_name, field_type, datetime_validator)


def test_validate_models_module():
    samples_files = iterate_files_in(SAMPLES_DIR / 'package_a', [], 'py')

    errors = validate(samples_files)

    assert sorted(errors) == [
        _date_error('package_a/models.py', 11, 'date_bad'),
        _datetime_error('package_a/models.py', 13, 'bad_datetime'),
        _date_error('package_a/models.py', 19, 'date_bad'),
        _datetime_error('package_a/models.py', 21, 'bad_datetime'),
        _datetime_error('package_a/models.py', 23, 'my_bad_datetime', 'MyDateTimeExtraField'),
    ]


def test_validate_models_package():
    samples_files = iterate_files_in(SAMPLES_DIR / 'package_b', [], 'py')

    errors = validate(samples_files)

    assert sorted(errors) == [
        _date_error('package_b/models/model_a.py', 6, 'date_bad'),
        _datetime_error('package_b/models/model_a.py', 8, 'bad_datetime'),
        _date_error('package_b/models/model_b.py', 6, 'date_bad'),
        _datetime_error('package_b/models/model_b.py', 8, 'bad_datetime'),
    ]

from __future__ import annotations

import pathlib

import pytest

from hooks.validate_celery_tasks_return_types import main

SAMPLES_DIR = pathlib.Path(__file__).parent.resolve() / 'samples'


@pytest.fixture()
def mocked_get_input_files(mocker):
    return mocker.patch(
        'hooks.validate_celery_tasks_return_types.get_input_files'
    )


def test_failing_file(mocked_get_input_files, capsys):
    mocked_get_input_files.return_value = [
        SAMPLES_DIR / 'tasks_with_incorrect_return_types.py'
    ]

    ret = main()
    captured = capsys.readouterr()
    errors = captured.out.split('\n')[:-1]

    assert len(errors) == 3
    assert all(['Invalid return type' in error for error in errors])

    assert ret == 1


def test_passing_file(mocked_get_input_files):
    mocked_get_input_files.return_value = [
        SAMPLES_DIR / 'tasks_with_correct_return_types.py'
    ]

    ret = main()

    assert ret == 0

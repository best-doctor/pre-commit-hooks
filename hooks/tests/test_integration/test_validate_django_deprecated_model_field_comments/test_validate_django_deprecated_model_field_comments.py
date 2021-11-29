from __future__ import annotations

import pathlib

import pytest

from hooks.validate_django_deprecated_model_field_comments import (
    DEFAULT_DEPRECATION_COMMENT_MARKER_REGEX,
    DEFAULT_VALID_DEPRECATION_COMMENT_REGEX,
    main,
)

SAMPLES_DIR = pathlib.Path(__file__).parent.resolve() / 'samples'


@pytest.fixture()
def mocked_get_input_models_files(mocker):
    return mocker.patch(
        'hooks.validate_django_deprecated_model_field_comments.get_input_models_files'
    )


def test_failing_file(mocked_get_input_models_files):
    args = [
        f'--valid-deprecation-comment-regex={DEFAULT_VALID_DEPRECATION_COMMENT_REGEX}',
        f'--deprecation-comment-marker-regex={DEFAULT_DEPRECATION_COMMENT_MARKER_REGEX}',
    ]
    mocked_get_input_models_files.return_value = [
        SAMPLES_DIR / 'models_with_invalid_deprecated_field_comments.py'
    ]

    ret = main(args)

    assert ret == 1


def test_passing_file(mocked_get_input_models_files):
    args = [
        f'--valid-deprecation-comment-regex={DEFAULT_VALID_DEPRECATION_COMMENT_REGEX}',
        f'--deprecation-comment-marker-regex={DEFAULT_DEPRECATION_COMMENT_MARKER_REGEX}',
    ]
    mocked_get_input_models_files.return_value = [
        SAMPLES_DIR / 'models_with_valid_deprecated_field_comments.py'
    ]

    ret = main(args)

    assert ret == 0

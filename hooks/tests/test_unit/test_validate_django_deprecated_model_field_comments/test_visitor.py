from __future__ import annotations

import re
import textwrap

import libcst as cst
import pytest

from hooks.validate_django_deprecated_model_field_comments import (
    DEFAULT_DEPRECATION_COMMENT_MARKER_REGEX,
    DEFAULT_VALID_DEPRECATION_COMMENT_REGEX,
    DeprecatedModelFieldValidator,
    Error,
)

VALID_DEPRECATION_COMMENT_PATTERN = re.compile(DEFAULT_VALID_DEPRECATION_COMMENT_REGEX)
DEPRECATION_COMMENT_MARKER_PATTERN = re.compile(DEFAULT_DEPRECATION_COMMENT_MARKER_REGEX)
MODEL_FILE_PATH = 'some_app/models.py'


@pytest.mark.parametrize(
    ('source', 'expected_errors'),
    [
        (
            """\
            class TestClass:
                foo = 'bar'  # deprecated
            """,
            [],
        ),
        (
            """\
            class TestModel(models.Model):
                foo = models.CharField(max_len=128, null=True)  # null_for_compatibility
            """,
            [],
        ),
        (
            """\
            class TestModel(models.Model):
                foo = models.CharField(  # deprecated TICKET-1234 20.11.2021, use bar instead
                    max_len=128, null=True
                )  # null_for_compatibility

                bar = models.ForeignKey(  # null_for_compatibility
                    to='Bar',
                    null=True,
                    on_delete=models.PROTECT
                )
            """,
            [],
        ),
        (
            """\
            class TestModel(models.Model):
                foo = models.CharField(  # deprecated at 20.11.2021
                    max_len=128, null=True
                )  # null_for_compatibility
            """,
            [
                Error(
                    model_file_path=MODEL_FILE_PATH,
                    line=2,
                    col=4,
                    field='foo'
                )
            ],
        ),
        (
            """\
            class TestModel(models.Model):
                foo = models.CharField(  # null_for_compatibility
                    max_len=128, null=True
                )  # deprecated TICKET-1234 20.11.2021, use bar instead

                bar = models.ForeignKey(  # null_for_compatibility
                    to='Bar',
                    null=True,
                    on_delete=models.PROTECT
                )
            """,
            [],
        ),
        (
            """\
            class TestModel(models.Model):
                foo = models.CharField(  # null_for_compatibility
                    max_len=128, null=True
                )  # deprecated at 20.11.2021
            """,
            [
                Error(
                    model_file_path=MODEL_FILE_PATH,
                    line=2,
                    col=4,
                    field='foo'
                )
            ],
        ),
    ],
    ids=[
        'not-a-django-model',
        'no-deprecation-comments',
        'valid-leading-deprecation-comment',
        'invalid-leading-deprecation-comment',
        'valid-trailing-deprecation-comment',
        'invalid-trailing-deprecation-comment',
    ],
)
def test_deprecated_model_field_validator(source, expected_errors):
    source = textwrap.dedent(source)
    validator = DeprecatedModelFieldValidator(
        model_file_path=MODEL_FILE_PATH,
        valid_deprecation_comment_pattern=VALID_DEPRECATION_COMMENT_PATTERN,
        deprecation_comment_marker_pattern=DEPRECATION_COMMENT_MARKER_PATTERN,
    )

    validator.run_for_module(module=cst.parse_module(source))

    assert validator.errors == expected_errors

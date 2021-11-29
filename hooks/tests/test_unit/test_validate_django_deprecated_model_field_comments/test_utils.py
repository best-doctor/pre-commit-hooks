from __future__ import annotations

import textwrap

import libcst as cst
import pytest

from hooks.validate_django_deprecated_model_field_comments import (
    get_leading_comment,
    get_model_field_name,
    get_trailing_comment,
)


@pytest.mark.parametrize(
    ('source', 'expected_result'),
    [
        ('first_name = models.CharField()', 'first_name'),
        ('visit: Visit = models.ForeignKey(to=Visit)', 'visit'),
    ],
)
def test_get_model_field_name(source, expected_result):
    node = cst.parse_statement(source)

    assert get_model_field_name(node) == expected_result


@pytest.mark.parametrize(
    ('source', 'expected_result'),
    [
        (
            """
            visit = models.ForeignKey(  # null_for_compatibility # allowed_cascade
                to='Visit',
                on_delete=models.CASCADE,
                null=True
            )
            """,
            '# null_for_compatibility # allowed_cascade',
        ),
        (
            """
            visit = models.ForeignKey(  # null_for_compatibility
                to='Visit',
                on_delete=models.CASCADE,
                null=True
            )
            """,
            '# null_for_compatibility',
        ),
        (
            """
            visit = models.ForeignKey(
                to='Visit',
                on_delete=models.CASCADE,
                null=True
            )
            """,
            None,
        ),
    ],
)
def test_get_leading_comment(source, expected_result):
    node = cst.parse_statement(textwrap.dedent(source))

    assert get_leading_comment(node) == expected_result


@pytest.mark.parametrize(
    ('source', 'expected_result'),
    [
        (
            """
            visit = models.ForeignKey(
                to='Visit',
                on_delete=models.CASCADE,
                null=True
            )  # null_for_compatibility # allowed_cascade
            """,
            '# null_for_compatibility # allowed_cascade',
        ),
        (
            """
            visit = models.ForeignKey(
                to='Visit',
                on_delete=models.CASCADE,
                null=True
            )  # null_for_compatibility
            """,
            '# null_for_compatibility',
        ),
        (
            """
            visit = models.ForeignKey(
                to='Visit',
                on_delete=models.CASCADE,
                null=True
            )
            """,
            None,
        ),
    ],
)
def test_get_trailing_comment(source, expected_result):
    node = cst.parse_statement(textwrap.dedent(source))

    assert get_trailing_comment(node) == expected_result

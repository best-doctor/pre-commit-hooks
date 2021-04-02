from __future__ import annotations

import ast

import pytest

from hooks.validate_settings_variables import (
    LineError,
    Reasons,
    exclude_lines_with_noqa,
    get_line_numbers_of_wrong_assignments,
)


@pytest.mark.parametrize(
    'file_line, expected_result', [
        ("""
        DICT = {
            'VAR': 'value',
            'VAR': os.getenv('value', ''),
            'VAR': values.Value('value', ''),
        }
        """,
            [
                LineError(2, Reasons.STRAIGHT_ASSIGNMENT),
                LineError(3, Reasons.GETENV),
            ],
         ),
        ("""
        DICT = {
            'VAR': os.environ['value'],
            'VAR': os.environ.get('value', ''),
            'VAR': getenv('value', ''),
            'VAR': os.getenv('value', ''),
        }
        """,
            [
                LineError(2, Reasons.GETENV),
                LineError(3, Reasons.GETENV),
                LineError(4, Reasons.GETENV),
                LineError(5, Reasons.GETENV),
            ],
         ),
        ("""
        class Foo:
            VAR = 'value'
            VAR = os.getenv('value', '')
            VAR = logging.getLogger('value')
        """,
            [
                LineError(2, Reasons.STRAIGHT_ASSIGNMENT),
                LineError(3, Reasons.GETENV),
            ],
         ),
        ("""
        LIST = [
            'value',
            ]
        """,
            [
                LineError(1, Reasons.STATIC_OBJECT),
            ],
         ),
        ("""
        LIST = [
            values.Value(None),
            ]
        """,
         []),
        ("""
        LIST = [
            'value',
            os.getenv('value', ''),
            ]
        """,
            [
                LineError(2, Reasons.STRAIGHT_ASSIGNMENT),
                LineError(3, Reasons.GETENV),
            ],
         ),
    ],
)
def test_get_numbers_of_wrong_lines(file_line, expected_result):
    content = ast.parse(file_line.strip()).body[0]

    assert get_line_numbers_of_wrong_assignments(content, content, content, 0) == expected_result


@pytest.mark.parametrize(
    'file_content, expected_result', [
        ("""
        DICT = {  # noqa: static object
            'VAR': 'value',
            'VAR': 'value',
            'VAR': 'value' # noqa,
        }
        """,
            {2}),
        ("""
        class Foo:
            VAR = 'value'
            VAR = 'value' # noqa: allowed straight assignment
            VAR = 'value' # noqa
        """,
            {4}),
    ],
)
def test_exclude_lines_with_noqa(file_content, expected_result, tmpdir):
    file_path = tmpdir.mkdir('sub').join('settings_file.txt')
    file_path.write(file_content)

    assert exclude_lines_with_noqa(file_path) == expected_result

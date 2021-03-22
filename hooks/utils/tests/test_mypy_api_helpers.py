from __future__ import annotations

import pytest

from hooks.utils.mypy_api_helpers import is_path_should_be_skipped


@pytest.mark.parametrize(
    'path, dirs_to_exclude, expected_result',
    [
        ('hello/world/', ['hello/world/'], True),
        ('hello/world/', ['hello'], True),
        ('hello/world/', ['/world', 'world'], True),
        ('hello/world/', ['world'], True),
        ('hello/world/', ['/world/'], False),
    ],
)
def test_is_path_should_be_skipped_success_case(path, dirs_to_exclude, expected_result):

    assert expected_result == is_path_should_be_skipped(path, dirs_to_exclude)

from __future__ import annotations

import pytest
from redbaron import RedBaron

from hooks.validate_django_null_true_comments import has_valid_comment


@pytest.mark.parametrize(
    'comment, expected_result', [
        (None, False),
        ('# pretends to be valid comment', False),
        ('# null_by_my_will', False),
        ('# null_by_design', True),
        ('# null_for_compatibility', True),
        ('# null_by_design: DB has no NULLs but they could appear in the future', True),
        ('# null_for_compatibility_remove_when_feature_X_is_ready', True),
    ],
)
def test_null_true_has_valid_comment(comment, expected_result):
    if comment is not None:
        comment = RedBaron(comment).find('comment')

    assert has_valid_comment(comment) is expected_result

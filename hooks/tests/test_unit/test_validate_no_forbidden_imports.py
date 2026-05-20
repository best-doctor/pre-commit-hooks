from __future__ import annotations

import ast

import pytest

from hooks.validate_no_forbidden_imports import get_import_errors_in_ast_tree, is_import_in_list


@pytest.mark.parametrize(
    'imported_name, forbidden_imports, expected_result',
    [
        ('foo', ['foo'], True),
        ('foo', ['foo.bar'], True),
        ('foo', ['foo.bar.baz'], True),
        ('bar', ['foo'], False),
        ('foo', ['bar'], False),
        ('foo.bar', ['foo.baz'], False),
    ],
)
def test__is_import_in_list__matches_forbidden_import(
    imported_name, forbidden_imports, expected_result,
):
    assert is_import_in_list(
        imported_name, forbidden_imports) == expected_result


def test__get_import_errors_in_ast_tree__reports_forbidden_import():
    ast_tree = ast.parse('import forbidden_pkg\nfrom other import bar\n')
    forbidden_imports = ['forbidden_pkg']

    errors = get_import_errors_in_ast_tree(
        '/app/module.py', ast_tree, forbidden_imports)

    assert errors == ['/app/module.py:1 Forbidden import']

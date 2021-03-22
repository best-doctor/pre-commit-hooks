from __future__ import annotations

import ast

import pytest

from hooks.utils.ast_helpers import (
    get_var_names_from_assignment, get_var_names_from_funcdef,
    get_full_imported_name, is_django_orm_query,
    _is_classdef_has_base_classes,
)


@pytest.mark.parametrize(
    'assigment, variables_names',
    [
        ('a = 1', ['a']),
        ('a: int = 1', ['a']),
    ],
)
def test_get_var_names_from_assignment_success_case(assigment, variables_names):
    assign_node = ast.parse(assigment).body[0]
    actual_result = get_var_names_from_assignment(assign_node)
    assert [r[0] for r in actual_result] == variables_names


@pytest.mark.parametrize(
    'def_str, variables_names',
    [
        ('def foo(): pass', []),
        ('def foo(a): pass', ['a']),
        ('def foo(a, b=1): pass', ['a', 'b']),
        ('def foo(a, b: int = 1): pass', ['a', 'b']),
    ],
)
def test_get_var_names_from_funcdef_success_case(def_str, variables_names):
    funcdef_node = ast.parse(def_str).body[0]
    actual_result = get_var_names_from_funcdef(funcdef_node)
    assert [r[0] for r in actual_result] == variables_names


@pytest.mark.parametrize(
    'import_str, imported_names',
    [
        ('import foo', ['foo']),
        ('import foo.bar', ['foo.bar']),
        ('import foo, bar', ['foo', 'bar']),
        ('from foo import bar', ['foo.bar']),
        ('from foo import bar, baz', ['foo.bar', 'foo.baz']),
    ],
)
def test_get_full_imported_name_success_case(import_str, imported_names):
    import_node = ast.parse(import_str).body[0]
    actual_result = get_full_imported_name(import_node)
    assert actual_result == imported_names


@pytest.mark.parametrize(
    'import_str, imported_names',
    [
        ('Clinic.objects.filter(pk=12).first()', True),
        ('qs.prefetch_related().distinct()', True),
        ('Clinic.objects.all().select_related()', True),
        ('clinic.get_franchise_object()', False),
        ('somedict.get("foo")', False),
    ],
)
def test_is_django_orm_query_success_case(import_str, imported_names):
    actual_result = is_django_orm_query(ast.parse(import_str).body[0])
    assert actual_result == imported_names


@pytest.mark.parametrize(
    'classdef_node, base_classess, module_name, classdef_check',
    [
        ('class Foo: pass', {''}, '', False),
        ('class Foo: pass', {'Foo'}, '', False),
        ('class Foo(Hello): pass', {'Hello'}, '', True),
        ('class Foo(Hello): pass', {'Foo'}, '', False),
        ('class Foo(super.Kek): pass', {'Kek'}, 'super', True),
    ],
)
def test__is_classdef_has_base_classes_success_case(classdef_node, base_classess, module_name, classdef_check):
    classdef_node = ast.parse(classdef_node).body[0]

    actual_result = _is_classdef_has_base_classes(classdef_node, base_classess, module_name)

    assert actual_result == classdef_check

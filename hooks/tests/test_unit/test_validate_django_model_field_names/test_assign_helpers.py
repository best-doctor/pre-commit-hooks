from __future__ import annotations

import ast

import pytest

from hooks.validate_django_model_field_names import get_assign_target_name, get_call_func_name


@pytest.mark.parametrize(
    'assignment, expected_name',
    [
        ('field = models.CharField()', 'field'),
        ('field: str = models.CharField()', 'field'),
        ('self.field = models.CharField()', None),
    ],
)
def test__get_assign_target_name__extracts_name_from_assignment(assignment, expected_name):
    assign_node = ast.parse(assignment).body[0]

    assert get_assign_target_name(assign_node) == expected_name


@pytest.mark.parametrize(
    'call_expression, expected_func_name',
    [
        ('models.DateField()', 'DateField'),
        ('models.fields.DateTimeField()', 'DateTimeField'),
        ('get_field()', 'get_field'),
        ('foo()()', None),
    ],
)
def test__get_call_func_name__extracts_field_constructor_name(call_expression, expected_func_name):
    call_node = ast.parse(f'field = {call_expression}').body[0].value

    assert get_call_func_name(call_node) == expected_func_name

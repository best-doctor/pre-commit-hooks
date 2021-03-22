from __future__ import annotations

import ast
import typing

from hooks.utils.ast_helpers import (
    _is_classdef_has_base_classes,
    function_def_has_decorator,
    get_assign_name,
    get_ast_tree_with_content,
    get_classdef_assignments,
    get_classdef_methods,
)
from hooks.utils.pre_commit import get_input_files

OptionalError = typing.Optional[str]
Errors = typing.List[str]


def is_api_filepath(filepath: str) -> bool:
    return '/api/' in filepath and '/rest_in_peace/' not in filepath


def is_serializer_or_view_filepath(filepath: str) -> bool:
    if not filepath.endswith('.py'):
        return False
    for part in ('serializers', 'views', 'viewsets'):
        if f'/{part}/' in filepath or filepath.endswith(f'/{part}.py'):
            return True
    return False


def _is_class(node: ast.AST) -> bool:
    return isinstance(node, ast.ClassDef)


def _is_api_serializer(node: ast.AST, file_path: str) -> bool:
    serializer_file = 'serializers.py' in file_path or 'serializers/' in file_path
    return (
        serializer_file
        and _is_class(node)
        and hasattr(node, 'name')
        and typing.cast(ast.ClassDef, node).name != 'Meta'
    )


def _is_api_view(node: ast.AST) -> bool:
    return _is_class(node) and is_view(typing.cast(ast.ClassDef, node))


def _is_api_viewset(node: ast.AST) -> bool:
    return _is_class(node) and is_viewset(typing.cast(ast.ClassDef, node))


def _is_restdoctor_api_element(node: ast.AST, file_path: str) -> bool:
    return _is_api_serializer(node, file_path) or _is_api_view(node) or _is_api_viewset(node)


def iterate_api_files() -> typing.Iterator[str]:
    return (
        filepath for filepath in get_input_files()
        if is_api_filepath(filepath) and is_serializer_or_view_filepath(filepath)
    )


def is_viewset(classdef_node: ast.ClassDef) -> bool:
    base_models_classes_names = {
        'ModelViewSet',
        'ReadOnlyModelViewSet',
        'GenericViewSet',
    }
    return _is_classdef_has_base_classes(
        classdef_node, base_models_classes_names, 'restdoctor.rest_framework.viewsets')


def is_view(classdef_node: ast.ClassDef) -> bool:
    base_models_classes_names = {
        'RetrieveAPIView',
        'ListAPIView',
        'SerializerClassMapApiView',
        'GenericAPIView',
    }
    return _is_classdef_has_base_classes(
        classdef_node, base_models_classes_names, 'restdoctor.rest_framework.views')


def is_serializer(classdef_node: ast.ClassDef) -> bool:
    base_models_classes_names = {
        'Serializer',
        'ModelSerializer',
        'BaseSerializer',
    }
    return _is_classdef_has_base_classes(
        classdef_node, base_models_classes_names, 'restdoctor.rest_framework.serializers')


def check_docstring(node: typing.Union[ast.ClassDef, ast.FunctionDef], *args: typing.Any) -> Errors:
    """
    Проверяет, что у View/ViewSet и Serializer есть докстринги.
    """
    if not ast.get_docstring(node):
        return [f':{node.lineno} {node.name} missed docstring']
    return []


def _check_help_text(function_node: ast.Call) -> OptionalError:
    function_kwargs_names = [keyword.arg for keyword in function_node.keywords]

    if 'help_text' in function_kwargs_names:
        return None

    for function_node_arg in function_node.args:
        if isinstance(function_node_arg, ast.Call):
            return _check_help_text(function_node_arg)

    return f':{function_node.lineno} missing `help_text` attribute'


def check_help_text_attribute_in_serializer_fields(node: ast.ClassDef, file_path: str) -> Errors:
    """Проверяет, что для атрибутов сериализаторов определен help_text."""
    if _is_api_serializer(node, file_path) is False:
        return []

    errors = []

    for assign in get_classdef_assignments(node):
        assign_value = assign.value
        if isinstance(assign_value, ast.Call) is False:
            continue

        assign_error = _check_help_text(typing.cast(ast.Call, assign_value))
        if assign_error:
            errors.append(assign_error)

    return errors


def _check_classdef_hasattr(node: ast.ClassDef, attribute: str) -> bool:
    for assign in get_classdef_assignments(node):
        assign_targets_names = [target.id for target in assign.targets]  # type: ignore

        if attribute in assign_targets_names:
            return True

    return False


def check_schema_tags_presence_in_views_and_viewsets(node: ast.ClassDef, file_path: str) -> Errors:
    """Проверяет наличие параметра schema_tags для вьюх и вьюсетов."""
    schema_tags_attribute = 'schema_tags'

    if _is_api_serializer(node, file_path):
        return []

    if _check_classdef_hasattr(node, schema_tags_attribute):
        return []

    return [f'{node.name} missed schema tags attribute']


def check_viewset_has_serializer_class_map(
    node: ast.ClassDef, file_path: str
) -> Errors:
    """Проверяет, что у ViewSet определен serializer_class_map."""
    serializer_class_map_attirbute = 'serializer_class_map'

    if _is_api_viewset(node) is False:
        return []

    if _check_classdef_hasattr(node, serializer_class_map_attirbute):
        return []

    return [f':{node.lineno} {node.name} missed `serializer_class_map` attribute']


def check_viewset_lookup_field_has_valid_value(node: ast.ClassDef, file_path: str) -> Errors:
    """Проверяет, что ViewSet.lookup_field != ‘id’."""
    allowed_lookup_fields = ['uuid']
    if _is_api_viewset(node) is False:
        return []

    for assign in get_classdef_assignments(node):
        if get_assign_name(assign) != 'lookup_field':
            continue

        if isinstance(assign.value, ast.Constant) is False:
            continue

        assign_value = assign.value.value  # type: ignore
        if assign_value not in allowed_lookup_fields:
            error = (
                f':{node.lineno} {node.name} viewset has forbidden `lookup_field`. '
                f'Choose from: {allowed_lookup_fields}'
            )
            return [error]

    return []


def get_serializer_field_method(node: ast.ClassDef, field_name: str) -> ast.FunctionDef:
    function_defs = [
        body_node for body_node in node.body if isinstance(body_node, ast.FunctionDef) is True
    ]

    for function_def in function_defs:
        if function_def.name == f'get_{field_name}':  # type: ignore
            return typing.cast(ast.FunctionDef, function_def)


def _is_allowed_return_type(return_node: typing.Union[ast.Name, ast.Subscript]) -> bool:
    allowed_return_types = ['str']

    if isinstance(return_node, ast.Name):
        return return_node.id in allowed_return_types

    if isinstance(return_node, ast.Subscript):
        return return_node.slice.value.id in allowed_return_types  # type: ignore

    return False


def check_schema_wrapper_for_serializer_method_field(node: ast.ClassDef, file_path: str) -> Errors:
    """SerializerMethodField должны быть обернуты в SchemaWrapper (если функция возвращает не str)."""
    if _is_api_serializer(node, file_path) is False:
        return []

    errors = []

    for assign in get_classdef_assignments(node):
        assign_value = assign.value
        if isinstance(assign_value, ast.Call) is False:
            continue

        if assign_value.func.id != 'SerializerMethodField':  # type: ignore
            continue

        assign_field_name = get_assign_name(assign)
        serializer_field_method = get_serializer_field_method(node, assign_field_name)
        if serializer_field_method is None:
            continue

        return_node = serializer_field_method.returns
        if _is_allowed_return_type(return_node) is False:  # type: ignore
            errors.append(f':{assign.lineno} {node.name} serializer {assign_field_name} field missing SchemaWrapper')

    return errors


def check_docstrings_for_api_action_handlers(node: ast.ClassDef, file_path: str) -> Errors:
    """Проверяет, что методы action в апи имееют докстринги."""
    errors = []

    for function_def in get_classdef_methods(node):
        function_has_action_decorator = (
            function_def_has_decorator(function_def, 'action')
            or function_def_has_decorator(function_def, 'drf_action')
        )

        if function_has_action_decorator:
            errors.extend(check_docstring(function_def))

    return errors


def check_docstrings_for_views_dispatch_methods(node: ast.ClassDef, file_path: str) -> Errors:
    """Проверяет, что dispatch методы вьюх имеют докстринги."""
    if _is_api_view(node) is False:
        return []

    errors = []
    methods_to_check = ['get', 'put', 'post', 'patch', 'delete']

    for function_def in get_classdef_methods(node):
        if function_def.name in methods_to_check:
            errors.extend(check_docstring(function_def))

    return errors


def check_doctstrings_viewsets_dispatch_methods(node: ast.ClassDef, file_path: str) -> Errors:
    """Проверяет, что dispatch методы вьюсетов имеют докстринги."""
    if _is_api_viewset(node) is False:
        return []

    errors = []
    methods_to_check = ['list', 'retrieve', 'create', 'update', 'partial_update', 'delete']

    for function_def in get_classdef_methods(node):
        if function_def.name in methods_to_check:
            errors.extend(check_docstring(function_def))

    return errors


def check_schema_annotations(
    api_element_node: ast.ClassDef, file_path: str,
) -> typing.Tuple[bool, typing.List[str]]:
    """
    Проверка правильности аннотаций для генерации схемы.

    [X] параметр schema_tags для вьюх и вьюсетов (check_schema_tags_presence_in_views_and_viewsets)
    [X] есть докстринги у View/ViewSet и Serializer (check_docstring)
    [X] help_text для атрибутов сериализаторов (check_help_text_attribute_in_serializer_fields)
    [X] у ViewSet определен serializer_class_map (check_viewset_has_serializer_class_map)
    [X] у ViewSet lookup_field != ‘id’ (check_viewset_lookup_field_has_valid_value)
    [X] SerializerMethodField должны быть обернуты в SchemaWrapper (если функция возвращает не str)
    [X] docstring-и для action-методов вьюх и вьюсетов (get/put/post/patch/delete, кастомные action)
    """
    checkers: typing.List[typing.Callable[[ast.ClassDef, str], Errors]] = [
        check_docstring,
        check_doctstrings_viewsets_dispatch_methods,
        check_docstrings_for_views_dispatch_methods,
        check_docstrings_for_api_action_handlers,
        check_schema_wrapper_for_serializer_method_field,
        check_schema_tags_presence_in_views_and_viewsets,
        check_help_text_attribute_in_serializer_fields,
        check_viewset_has_serializer_class_map,
        check_viewset_lookup_field_has_valid_value,
    ]

    node_errors = []

    for checker in checkers:
        node_errors.extend(checker(api_element_node, file_path))

    has_errors = len(node_errors) > 0
    return has_errors, node_errors


def main() -> typing.Optional[int]:
    has_errors = False
    for pyfilepath in iterate_api_files():
        ast_tree, file_content = get_ast_tree_with_content(pyfilepath)
        if ast_tree is None or file_content is None:
            continue
        for node in ast.walk(ast_tree):
            if _is_restdoctor_api_element(node, pyfilepath):
                node_has_errors, errors = check_schema_annotations(
                    typing.cast(ast.ClassDef, node), pyfilepath)
                for error in errors:
                    print(f'{pyfilepath}:{error}')  # noqa: T001
                has_errors = has_errors or node_has_errors
    if has_errors:
        return 1


if __name__ == '__main__':
    exit(main())

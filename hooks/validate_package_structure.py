"""
Валидатор структуры модуля.

Вот что он проверяет:
[x] в models.py только модели
[ ] admin – модуль или в нём только model admin
[ ] аналогично zbs_admin
[ ] graphql – только графкуэльные штуки
[ ] tests – тесты на штуки, которые объявлены в этом модуле
[x] Все Enum в enums.py
[x] в urls.py есть urlpatterns и в нём path, а не url
[x] во views.py только классовые вьюхи
[ ] в модуле не больше 20 py файлов (без миграций и тестов)
[x] Нет файлов с суффиксом _utils/_helpers (им место в в utils)
[x] нет пустых файлов кроме инитов
[ ] миграции не импортируют модели
[ ] миграций не больше 30
"""

from __future__ import annotations

import ast
import os

from typing import Callable, List, Optional


from hooks.utils.ast_helpers import (
    get_ast_tree, is_django_model_definition, is_enum_definition,
    get_not_ok_base_nodes_from, logger_ast_nodes_conditional, get_assignments_to,
    has_import_of_function_from_package, get_check_decorators_includes,
)
from hooks.utils.pre_commit import get_input_files, get_modules_files, is_django_model_file


def has_only_models_in_models_submodule(module_name: str, module_path: str, module_files: List[str]) -> List[str]:
    logger_object_name = 'logger'

    allowed_ast_nodes = {
        ast.Import,
        ast.ImportFrom,
        ast.If,
    }

    conditionals_ast_nodes = logger_ast_nodes_conditional(logger_object_name)

    conditionals_ast_nodes.extend([
        (  # определения моделей
            ast.ClassDef,
            is_django_model_definition,
        ),
        (  # пропуск определений классов по декоратору
            ast.ClassDef,
            get_check_decorators_includes({'pass_check_is_django_model_definition'}),
        ),
        (  # определения депрекейтед функций
            ast.FunctionDef,
            get_check_decorators_includes({'deprecated'}),
        ),
    ])

    errors: List[str] = []

    for filepath in module_files:
        if not is_django_model_file(filepath):
            continue

        ast_tree = get_ast_tree(filepath)
        if ast_tree is None:
            continue

        for bad_node in get_not_ok_base_nodes_from(ast_tree, allowed_ast_nodes, conditionals_ast_nodes):
            errors.append(
                f'{filepath}:{bad_node.lineno} Wrong instruction for models '
                f'submodule (models should contains only models)',
            )
    return errors


def all_enums_in_enums_py_module(module_name: str, module_path: str, module_files: List[str]) -> List[str]:
    allowed_enums_filename = 'enums.py'
    errors = []
    for filepath in module_files:
        filename = os.path.basename(filepath)
        if filename == allowed_enums_filename:
            continue
        ast_tree = get_ast_tree(filepath)
        if ast_tree is None:
            continue
        for classdef in [n for n in ast_tree.body if isinstance(n, ast.ClassDef)]:
            if is_enum_definition(classdef):
                errors.append(f'{filepath}:{classdef.lineno} Enums should live in {allowed_enums_filename}')
    return errors


def has_no_submodules_with_blacklisted_suffixes(
    module_name: str, module_path: str, module_files: List[str],
) -> List[str]:
    errors = []
    for filepath in module_files:
        relative_path = os.path.relpath(filepath, module_path)
        is_forbidden = relative_path.endswith('_utils.py') or relative_path.endswith('_helpers.py')
        is_tests = relative_path.startswith('tests/')

        if is_forbidden and not is_tests:
            errors.append(f'{filepath} should be moved to utils subdirectory and remove suffix from filename')

        return errors


def has_no_empty_py_files(module_name: str, module_path: str, module_files: List[str]) -> List[str]:
    max_filesize_to_check_bytes = 100
    allowed_empty_file = {'__init__.py'}
    errors: List[str] = []
    for filename in module_files:
        if (
            os.path.getsize(filename) > max_filesize_to_check_bytes
            or os.path.basename(filename) in allowed_empty_file
        ):
            continue
        with open(filename, 'r') as file_handler:
            file_content = file_handler.read()
        if not file_content.strip():
            errors.append(f'{filename} empty files are not allowed')
    return errors


def views_py_has_only_class_views(module_name: str, module_path: str, module_files: List[str]) -> List[str]:
    views_py_filename = 'views.py'
    logger_object_name = 'logger'

    allowed_ast_nodes = {
        ast.Import,
        ast.ImportFrom,
        ast.If,
        ast.ClassDef,
        ast.Assign,
    }

    conditionals_ast_nodes = logger_ast_nodes_conditional(logger_object_name)

    errors: List[str] = []

    for filepath in module_files:
        filename = os.path.basename(filepath)
        if views_py_filename != filename:
            continue

        ast_tree = get_ast_tree(filepath)
        if ast_tree is None:
            continue

        functions = get_not_ok_base_nodes_from(ast_tree, allowed_ast_nodes, conditionals_ast_nodes)

        errors.extend([
            f'{filepath}:{func.lineno} Only class views allowed in {views_py_filename}'
            for func in functions
        ])

    return errors


def urls_py_has_urlpatterns(module_name: str, module_path: str, module_files: List[str]) -> List[str]:
    urls_py_filename = 'urls.py'
    target_assignment_name = 'urlpatterns'

    errors: List[str] = []

    for filepath in module_files:
        filename = os.path.basename(filepath)
        if urls_py_filename != filename or os.path.relpath(filepath, module_path).startswith('tests/'):
            continue

        ast_tree = get_ast_tree(filepath)
        if ast_tree is None:
            continue

        if not get_assignments_to(ast_tree, target_assignment_name):
            errors.append(f'{filepath} does not contain "{target_assignment_name}" assignment')

    return errors


def no_url_calls(module_name: str, module_path: str, module_files: List[str]) -> List[str]:
    errors: List[str] = []

    for filepath in module_files:
        ast_tree = get_ast_tree(filepath)
        if ast_tree is None:
            continue

        if has_import_of_function_from_package(ast_tree, 'django.conf.urls', 'url'):
            url_calls = [
                ast_node for ast_node in ast.walk(ast_tree)
                if (
                    isinstance(ast_node, ast.Call)
                    and isinstance(ast_node.func, ast.Name)
                    and ast_node.func.id == 'url'
                )
            ]

            for url_call in url_calls:
                errors.append(f'{filepath}:{url_call.lineno} url() call is deprecated, use path() instead')

    return errors


def main() -> Optional[int]:
    exit_zero = True
    module_validators: List[Callable[[str, str, List[str]], List[str]]] = [
        has_only_models_in_models_submodule,
        all_enums_in_enums_py_module,
        has_no_submodules_with_blacklisted_suffixes,
        has_no_empty_py_files,
        views_py_has_only_class_views,
        urls_py_has_urlpatterns,
        no_url_calls,
    ]
    errors: List[str] = []
    for module_name, module_path, module_files in get_modules_files(get_input_files(dirs_to_exclude=[])):
        for validator in module_validators:
            errors += validator(module_name, module_path, module_files)

    for error in errors:
        print(error)  # noqa: T001
    if errors and not exit_zero:
        return 1


if __name__ == '__main__':
    exit(main())

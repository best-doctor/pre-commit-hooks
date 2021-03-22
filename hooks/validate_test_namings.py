from __future__ import annotations

import ast
import collections
from typing import List, DefaultDict, Union, Optional

from hooks.utils.ast_helpers import AnyFuncdef
from hooks.utils.pre_commit import get_input_test_files


def get_ast_tree(pyfilepath: str) -> Optional[ast.Module]:
    with open(pyfilepath, 'r') as file_handler:
        try:
            file_content = file_handler.read()
        except UnicodeDecodeError:
            return None
    ast_tree = ast.parse(file_content)
    return ast_tree


def get_funcdefs(ast_tree: ast.Module) -> List[AnyFuncdef]:
    return [n for n in ast_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def funcdef_with_fixture(test_funcdef: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool:
    for decorator in test_funcdef.decorator_list:
        fixture_without_argument = isinstance(decorator, ast.Attribute) and decorator.attr == 'fixture'
        fixture_with_argument = (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == 'fixture'
        )
        if fixture_with_argument or fixture_without_argument:
            return True

    return False


def get_tests_with_wrong_naming() -> DefaultDict[str, List]:
    tests_with_wrong_naming: DefaultDict[str, List] = collections.defaultdict(list)
    for test_filename in get_input_test_files():
        ast_tree = get_ast_tree(pyfilepath=test_filename)
        if ast_tree is None:
            continue

        funcdefs_list = get_funcdefs(ast_tree)
        for test_funcdef in funcdefs_list:
            if test_funcdef.name.startswith('test_') or test_funcdef.name.startswith('_'):
                continue

            wrong_funcdef_without_fixture = funcdef_with_fixture(test_funcdef=test_funcdef)
            if not wrong_funcdef_without_fixture:
                tests_with_wrong_naming[test_filename].append(test_funcdef.name)

    return tests_with_wrong_naming


def main() -> Optional[int]:
    tests_with_wrong_naming = get_tests_with_wrong_naming()
    for test_filename, test_funcdef_list in tests_with_wrong_naming.items():
        print(test_filename, '\n', test_funcdef_list)  # noqa: T001
    if tests_with_wrong_naming:
        return 1


if __name__ == '__main__':
    exit(main())

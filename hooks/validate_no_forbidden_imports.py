from __future__ import annotations

import ast
from typing import List, Optional

from hooks.utils.ast_helpers import get_ast_tree, get_full_imported_name
from hooks.utils.mypy_api_helpers import get_list_param_from_config
from hooks.utils.pre_commit import get_input_files


def is_import_in_list(imported_name: str, forbidden_imports: List[str]) -> bool:
    if imported_name in forbidden_imports:
        return True
    for forbidden_import in forbidden_imports:
        if forbidden_import.startswith(f'{imported_name}.'):
            return True


def get_import_errors_in_ast_tree(pyfilepath: str, ast_tree: ast.AST, forbidden_imports: List[str]) -> List[str]:
    errors: List[str] = []
    imports = [n for n in ast.walk(ast_tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    for import_node in imports:
        for import_name in get_full_imported_name(import_node):
            if is_import_in_list(import_name, forbidden_imports):
                errors.append(f'{pyfilepath}:{import_node.lineno} Forbidden import')
    return errors


def main() -> Optional[int]:
    forbidden_imports = get_list_param_from_config('setup.cfg', 'project_structure', 'forbidden_imports')
    if not forbidden_imports:
        return None

    errors: List[str] = []

    for pyfilepath in get_input_files():
        ast_tree: Optional[ast.Module] = get_ast_tree(pyfilepath)
        if ast_tree is None:
            continue

        errors += get_import_errors_in_ast_tree(pyfilepath, ast_tree, forbidden_imports)

    for error in errors:
        print(error)  # noqa: T001
    if errors:
        return 1


if __name__ == '__main__':
    exit(main())

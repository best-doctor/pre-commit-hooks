from __future__ import annotations

import ast
from typing import Optional

from hooks.utils.ast_helpers import get_ast_tree_with_content, get_variable_node_by_name
from hooks.utils.pre_commit import get_input_files


def is_django_object_type_node(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.ClassDef)
        and 'DjangoObjectType' in (base.id for base in node.bases if isinstance(base, ast.Name))
    )


def are_model_fields_implicitly_exposed(node: ast.AST) -> bool:
    fields_explicit_definition_variable = get_variable_node_by_name(node, 'only_fields')
    if fields_explicit_definition_variable:
        if isinstance(fields_explicit_definition_variable.value, (ast.List, ast.Tuple)):
            if fields_explicit_definition_variable.value.elts:
                return False
    return True


def main() -> Optional[int]:
    has_errors = False
    for pyfilepath in get_input_files():
        ast_tree_results = get_ast_tree_with_content(pyfilepath)
        ast_tree, file_content = ast_tree_results
        if ast_tree is None or file_content is None:
            continue
        for node in ast.walk(ast_tree):
            if not is_django_object_type_node(node):
                continue

            if are_model_fields_implicitly_exposed(node):
                print('{0}:{1} "{2}" implicitly exposes all model\'s fields'.format(  # noqa: T001
                    pyfilepath, node.lineno, node.name,  # type: ignore
                ))

    if has_errors:
        return 1


if __name__ == '__main__':
    exit(main())

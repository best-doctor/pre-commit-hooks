from __future__ import annotations

import ast
from typing import Optional

from hooks.utils.ast_helpers import get_ast_tree_with_content
from hooks.utils.pre_commit import get_input_files


def main() -> Optional[int]:
    has_errors = False
    for pyfilepath in get_input_files():
        ast_tree_results = get_ast_tree_with_content(pyfilepath)
        ast_tree, file_content = ast_tree_results
        if ast_tree is None or file_content is None:
            continue
        for assert_node in [n for n in ast.walk(ast_tree) if isinstance(n, ast.Assert)]:
            has_errors = True
            print(  # noqa: T001
                '{0}:{1} assert usage detected'.format(
                    pyfilepath, assert_node.lineno,
                ),
            )

    if has_errors:
        return 1


if __name__ == '__main__':
    exit(main())

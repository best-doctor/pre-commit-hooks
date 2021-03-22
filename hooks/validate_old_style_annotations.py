from __future__ import annotations

import ast
import itertools
from typing import Optional

from hooks.utils.ast_helpers import get_ast_tree_with_content
from hooks.utils.pre_commit import get_input_files


def main() -> Optional[int]:
    has_errors = False
    for pyfilepath in get_input_files():
        ast_tree, file_content = get_ast_tree_with_content(pyfilepath)
        if ast_tree is None or file_content is None:
            continue
        for annotated in itertools.chain(
            [n.annotation for n in ast.walk(ast_tree) if isinstance(n, ast.AnnAssign)],
            [n.annotation for n in ast.walk(ast_tree) if isinstance(n, ast.arg) and n.annotation],
            [n.returns for n in ast.walk(ast_tree) if isinstance(n, ast.FunctionDef) and n.returns],
        ):
            if isinstance(annotated, ast.Str):
                has_errors = True
                print(  # noqa: T001
                    '{0}:{1} old style annotation'.format(
                        pyfilepath, annotated.lineno,
                    ),
                )

    if has_errors:
        return 1


if __name__ == '__main__':
    exit(main())

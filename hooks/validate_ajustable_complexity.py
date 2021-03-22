from __future__ import annotations

import ast
from typing import List, Optional, Tuple

from hooks.utils.ast_helpers import extract_all_variable_names, get_all_funcdefs, get_ast_tree_with_content
from hooks.utils.complexity import get_node_mccabe_complexity
from hooks.utils.mypy_api_helpers import get_list_param_from_config, get_param_from_config
from hooks.utils.pre_commit import get_input_files


def get_max_complexity_for_path(
    pyfilepath: str,
    per_path_max_complexity: List[Tuple[str, int]],
    default_max_allowed_complexity: int,
) -> int:
    for path, complexity in per_path_max_complexity:
        if path in pyfilepath:
            return complexity
    return default_max_allowed_complexity


def main() -> Optional[int]:
    variable_names_blacklist = {
        # from https://github.com/wemake-services/wemake-python-styleguide/
        'val',
        'vals',
        'var',
        'vars',
        'variable',
        'contents',
        'handle',
        'file',
        'objs',
        'some',
        'do',
        'no',
        'true',
        'false',
        'foo',
        'bar',
        'baz',
        'data',
        'result',
        'results',
        'item',
        'items',
        'value',
        'values',
        'content',
        'obj',
        'info',
        'handler',
    }
    default_max_allowed_complexity = int(get_param_from_config(
        'setup.cfg',
        'flake8',
        'adjustable-default-max-complexity',
    ) or 8) + 1
    per_path_max_complexity = [
        (r.split(': ')[0], int(r.split(': ')[1]) + 1)
        for r in get_list_param_from_config('setup.cfg', 'flake8', 'per-path-max-complexity')
    ]
    complexity_penalty = 2

    errors = []
    for pyfilepath in get_input_files():
        ast_tree_results: Tuple[Optional[ast.AST], Optional[str]] = get_ast_tree_with_content(pyfilepath)
        ast_tree, file_content = ast_tree_results
        if ast_tree is None or file_content is None:
            continue
        file_lines = file_content.split('\n')
        funcdefs = get_all_funcdefs(ast_tree)
        for funcdef in funcdefs:
            vars_in_function = [
                v for v in extract_all_variable_names(funcdef)
                if '# noqa' not in file_lines[v[1].lineno - 1]
            ]
            all_vars_in_function = {v[0] for v in vars_in_function}
            blacklisted_vars_amount = (
                len(all_vars_in_function.intersection(variable_names_blacklist))
                + len([v for v in all_vars_in_function if len(v) == 1 and v not in ['_']])
            )
            current_max_complexity = get_max_complexity_for_path(
                pyfilepath,
                per_path_max_complexity,
                default_max_allowed_complexity,
            )
            max_complexity = current_max_complexity - blacklisted_vars_amount * complexity_penalty
            def_line = file_lines[funcdef.lineno - 1]
            current_complexity = get_node_mccabe_complexity(funcdef)
            if current_complexity > max_complexity and '# noqa' not in def_line:
                errors.append(
                    (pyfilepath, funcdef.lineno, funcdef.name, current_complexity, max_complexity),
                )
    if errors:
        for path, line_no, func_name, comlexity, max_comlexity in errors:
            print('{0}:{1} {2} is too complex ({3} > {4})'.format(  # noqa: T001
                path,
                line_no,
                func_name,
                comlexity,
                max_comlexity,
            ))
        return 1


if __name__ == '__main__':
    exit(main())

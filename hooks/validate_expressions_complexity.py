from __future__ import annotations

import ast
import io
import itertools
from typing import Any, Dict, Iterator, List

from hooks.utils.ast_helpers import get_ast_tree_with_content, is_django_orm_query, iterate_over_expressions
from hooks.utils.pre_commit import get_input_files


class BaseAstNodeError(Exception):
    def __init__(self, message: str, node: ast.AST) -> None:
        super().__init__(message)
        self.node = node


class UnknownAstNodeError(BaseAstNodeError):
    pass


NODE_TYPES_BY_CLASS = [
    (ast.Assert, 'assert'),
    (ast.Assign, 'assign'),
    (ast.Attribute, 'attribute'),
    ((ast.AugAssign, ast.AnnAssign), 'featured_assign'),
    (ast.BinOp, 'binary_op'),
    (ast.BoolOp, 'bool_op'),
    (ast.Call, 'call'),
    (ast.Compare, 'compare'),
    (ast.comprehension, 'base_comprehension'),
    (ast.Delete, 'delete'),
    (ast.Dict, 'dict'),
    (ast.DictComp, 'dict_comprehension'),
    (
        (
            ast.Expr, ast.Return, ast.Starred, ast.Index,
            ast.Yield, ast.YieldFrom, ast.FormattedValue,
            ast.Await,
        ),
        'item_with_value',
    ),
    (ast.Global, 'global'),
    (ast.IfExp, 'if_expr'),
    (ast.JoinedStr, 'fstring'),
    (ast.Lambda, 'lambda'),
    ((ast.List, ast.Set, ast.Tuple), 'sized'),
    ((ast.ListComp, ast.GeneratorExp, ast.SetComp), 'simple_comprehensions'),
    (
        (
            ast.Name, ast.Import, ast.Str, ast.Num, ast.NameConstant, ast.Bytes, ast.Nonlocal,
            ast.ImportFrom, ast.Pass, ast.Raise, ast.Break, ast.Continue, type(None),
            ast.Ellipsis,
        ),
        'simple_type',
    ),
    (ast.NamedExpr, 'walrus'),
    (ast.Subscript, 'subscript'),
    (ast.Slice, 'slice'),
    (ast.UnaryOp, 'unary_op'),
]

NODE_COMPLEXITY_BY_TYPE = {
    'assert': 1,
    'assign': 1,
    'attribute': 1,
    'featured_assign': 1,
    'binary_op': 1,
    'bool_op': 1,
    'call': .5,
    'compare': 1,
    'base_comprehension': 0,
    'delete': 1,
    'dict': 1,
    'dict_comprehension': 1,
    'item_with_value': 0,
    'global': 1,
    'if_expr': 1,
    'fstring': 2,
    'lambda': 1,
    'sized': 1,
    'simple_comprehensions': 1,
    'simple_type': 0,
    'subscript': 1,
    'slice': 1,
    'unary_op': 1,
    'walrus': 1,
}


NODE_TYPE_SUBNODE_GETTERS = {
    'assert': lambda node: [node.test],
    'assign': lambda node: node.targets + [node.value],
    'attribute': lambda node: [node.value],
    'featured_assign': lambda node: [node.target, node.value],
    'binary_op': lambda node: [node.left, node.right],
    'bool_op': lambda node: node.values,
    'call': lambda node: node.args + [node.func],
    'compare': lambda node: node.comparators + [node.left],
    'base_comprehension': lambda node: node.ifs + [node.target, node.iter],
    'delete': lambda node: node.targets,
    'dict': lambda node: itertools.chain(node.keys, node.values),
    'dict_comprehension': lambda node: node.generators + [node.key, node.value],
    'item_with_value': lambda node: [node.value],
    'global': lambda node: [],
    'if_expr': lambda node: [node.test, node.body, node.orelse],
    'fstring': lambda node: node.values,
    'lambda': lambda node: [node.body],
    'sized': lambda node: node.elts,
    'simple_comprehensions': lambda node: node.generators + [node.elt],
    'simple_type': lambda node: [],
    'subscript': lambda node: [node.value, node.slice],
    'slice': lambda node: [node.lower, node.upper, node.step],
    'unary_op': lambda node: [node.operand],
    'walrus': lambda node: [node.target, node.value],
}


def get_complexity_increase_for_node_type(node_type_sid: str) -> float:
    return NODE_COMPLEXITY_BY_TYPE[node_type_sid]


def _get_sub_nodes(node: Any, node_type_sid: str) -> List[ast.AST]:
    return NODE_TYPE_SUBNODE_GETTERS[node_type_sid](node)


def get_expression_part_info(node: ast.AST) -> Dict[str, Any]:
    for types, node_type_name in NODE_TYPES_BY_CLASS:
        if isinstance(node, types):  # type: ignore
            return {
                'type': node_type_name,
                'subnodes': _get_sub_nodes(node, node_type_name),
            }
    else:
        raise UnknownAstNodeError(
            f'unknown expression type {type(node)}',
            node=node
        )


def get_expression_complexity(node: ast.AST) -> float:
    info = get_expression_part_info(node)
    score_addon = get_complexity_increase_for_node_type(info['type'])
    return max(
        (
            get_expression_complexity(n)
            for n in info['subnodes']
        ),
        default=0
    ) + score_addon


def format_exception(exception: BaseAstNodeError, filepath: str, file_lines: List[str]) -> str:
    node = exception.node
    line = file_lines[node.lineno-1]
    error_message = io.StringIO()
    error_message.write(f'{exception} in {filepath}:{node.lineno}\n')
    error_message.write(line)
    error_message.write('\n')
    error_message.write(' ' * node.col_offset)
    error_message.write('^' * ((node.end_col_offset or len(line)) - node.col_offset))
    return error_message.getvalue()


def get_file_errors(
    pyfilepath: str,
    max_expression_complexity: int,
    ignore_django_orm_queries: bool,
) -> Iterator[str]:
    ast_tree, file_content = get_ast_tree_with_content(pyfilepath)
    if ast_tree is None or file_content is None:
        return

    file_lines = file_content.split('\n')
    for expression in iterate_over_expressions(ast_tree):
        if is_django_orm_query(expression) and ignore_django_orm_queries:
            continue
        try:
            complexity = get_expression_complexity(expression)
        except UnknownAstNodeError as exc:
            formatted_error_message = format_exception(exc, pyfilepath, file_lines)
            yield formatted_error_message
        else:
            if (
                complexity > max_expression_complexity
                and '# noqa' not in file_lines[expression.lineno - 1]
            ):
                yield '{0}:{1} expression is too complex ({2}>{3})'.format(
                    pyfilepath, expression.lineno,
                    complexity, max_expression_complexity,
                )


def main() -> int:
    has_errors = False

    for pyfilepath in get_input_files():
        for error_message in get_file_errors(
            pyfilepath,
            max_expression_complexity=9,
            ignore_django_orm_queries=True,
        ):
            has_errors = True
            print(error_message)  # noqa: T001

    return int(has_errors)


if __name__ == '__main__':
    exit(main())

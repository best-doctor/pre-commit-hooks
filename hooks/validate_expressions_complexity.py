from __future__ import annotations

import ast
from typing import Dict, Any, List, Optional

import itertools


from hooks.utils.ast_helpers import (
    get_ast_tree_with_content, iterate_over_expressions, is_django_orm_query,
)
from hooks.utils.list_utils import max_with_default
from hooks.utils.pre_commit import get_input_files


def _get_sub_nodes(node: Any, node_type_sid: str) -> List[ast.AST]:
    subnodes_map = {
        'unary_op': lambda n: [n.operand],
        'item_with_value': lambda n: [n.value],
        'assert': lambda n: [n.test],
        'delete': lambda n: node.targets,
        'assign': lambda n: node.targets + [node.value],
        'featured_assign': lambda n: [n.target, n.value],
        'call': lambda n: node.args + [n.func],
        'sized': lambda n: node.elts,
        'dict': lambda n: itertools.chain(node.keys, node.values),
        'dict_comprehension': lambda n: node.generators + [n.key, n.value],
        'simple_comprehensions': lambda n: node.generators + [n.elt],
        'base_comprehension': lambda n: node.ifs + [n.target, n.iter],
        'compare': lambda n: node.comparators + [n.left],
        'subscript': lambda n: [n.value, n.slice],
        'slice': lambda n: [n.lower, n.upper, n.step],
        'binary_op': lambda n: [n.left, n.right],
        'lambda': lambda n: [n.body],
        'if_expr': lambda n: [n.test, n.body, n.orelse],
        'bool_op': lambda n: n.values,
        'fstring': lambda n: n.values,
        'attribute': lambda n: [n.value],
        'simple_type': lambda n: [],
        'global': lambda n: [],
    }
    return subnodes_map[node_type_sid](node)


def get_expression_part_info(node: ast.AST) -> Dict[str, Any]:
    types_map = [
        (ast.UnaryOp, 'unary_op'),
        (
            (
                ast.Expr, ast.Return, ast.Starred, ast.Index,
                ast.Yield, ast.YieldFrom, ast.FormattedValue,
            ),
            'item_with_value',
        ),
        (ast.Assert, 'assert'),
        (ast.Delete, 'delete'),
        (ast.Assign, 'assign'),
        ((ast.AugAssign, ast.AnnAssign), 'featured_assign'),
        (ast.Call, 'call'),
        ((ast.List, ast.Set, ast.Tuple), 'sized'),
        (ast.Dict, 'dict'),
        (ast.DictComp, 'dict_comprehension'),
        ((ast.ListComp, ast.GeneratorExp, ast.SetComp), 'simple_comprehensions'),
        (ast.comprehension, 'base_comprehension'),
        (ast.Compare, 'compare'),
        (ast.Subscript, 'subscript'),
        (ast.Slice, 'slice'),
        (ast.BinOp, 'binary_op'),
        (ast.Lambda, 'lambda'),
        (ast.IfExp, 'if_expr'),
        (ast.BoolOp, 'bool_op'),
        (ast.Attribute, 'attribute'),
        (ast.JoinedStr, 'fstring'),
        (
            (
                ast.Name, ast.Import, ast.Str, ast.Num, ast.NameConstant, ast.Bytes, ast.Nonlocal,
                ast.ImportFrom, ast.Pass, ast.Raise, ast.Break, ast.Continue, type(None),
                ast.Ellipsis,
            ),
            'simple_type',
        ),
        (ast.Global, 'global'),
    ]
    node_type_sid = None
    for types, node_type_name in types_map:
        if isinstance(node, types):  # type: ignore
            node_type_sid = node_type_name
            break
    else:
        raise AssertionError('should always get node type')

    return {
        'type': node_type_sid,
        'subnodes': _get_sub_nodes(node, node_type_sid),
    }


def get_complexity_increase_for_node_type(node_type_sid: str) -> float:
    nodes_scores_map = {
        'unary_op': 1,
        'item_with_value': 0,
        'assert': 1,
        'delete': 1,
        'assign': 1,
        'featured_assign': 1,
        'call': .5,
        'sized': 1,
        'dict': 1,
        'dict_comprehension': 1,
        'simple_comprehensions': 1,
        'base_comprehension': 0,
        'compare': 1,
        'subscript': 1,
        'slice': 1,
        'binary_op': 1,
        'lambda': 1,
        'if_expr': 1,
        'bool_op': 1,
        'attribute': 1,
        'simple_type': 0,
        'fstring': 2,
        'global': 1,
    }
    return nodes_scores_map[node_type_sid]


def get_expression_complexity(node: ast.AST) -> float:
    info = get_expression_part_info(node)
    score_addon = get_complexity_increase_for_node_type(info['type'])
    if not info['subnodes']:
        return score_addon
    return max_with_default(get_expression_complexity(n) for n in info['subnodes']) + score_addon


def main() -> Optional[int]:
    max_expression_complexity = 9
    ignore_django_orm_queries = True

    has_errors = False
    for pyfilepath in get_input_files():
        ast_tree_results = get_ast_tree_with_content(pyfilepath)
        ast_tree, file_content = ast_tree_results
        if ast_tree is None or file_content is None:
            continue
        file_lines = file_content.split('\n')
        for expression in iterate_over_expressions(ast_tree):
            if ignore_django_orm_queries and is_django_orm_query(expression):
                continue
            complexity = get_expression_complexity(expression)
            if complexity > max_expression_complexity and '# noqa' not in file_lines[expression.lineno - 1]:
                has_errors = True
                print(  # noqa: T001
                    '{0}:{1} ({2}>{3})'.format(
                        pyfilepath, expression.lineno,
                        complexity, max_expression_complexity,
                    ),
                )

    if has_errors:
        return 1


if __name__ == '__main__':
    exit(main())

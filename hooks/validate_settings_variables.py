from __future__ import annotations

import ast
import tokenize
import typing

from hooks.utils.ast_helpers import get_ast_tree_with_content
from hooks.utils.pre_commit import get_input_files

NOQA_FOR_SETTINGS_VARIABLES = ['# noqa: allowed straight assignment', '# noqa: static object']


def is_node_static(node: ast.AST) -> bool:
    if isinstance(node, (ast.List, ast.Dict, ast.Tuple)):
        child_nodes_with_straight_assignment = 0
        for child_node in ast.iter_child_nodes(node):
            if isinstance(child_node, (ast.Constant, ast.BinOp, ast.Load, ast.Store, ast.Starred)):
                child_nodes_with_straight_assignment += 1
            else:
                child_nodes_with_straight_assignment += is_node_static(child_node)
        return child_nodes_with_straight_assignment == len(list(ast.iter_child_nodes(node)))
    else:
        return False


def is_child_node_a_dict_value(child_idx: int, parent: ast.AST) -> bool:
    """В словаре детские ноды идут в таком порядке: все ключи, затем все значения."""
    return child_idx >= (len(list(ast.iter_child_nodes(parent)))) // 2


def is_node_straight_assignment(node: ast.AST, parent: ast.AST, child_idx: int) -> bool:
    is_node_straight_assignment = False
    if not len(list(ast.iter_child_nodes(node))):
        if isinstance(parent, (ast.List, ast.Assign, ast.Tuple)) and (
            isinstance(node, (ast.Constant, ast.BinOp))
        ):
            is_node_straight_assignment = True

        elif isinstance(parent, (ast.Dict)) and (
            isinstance(node, (ast.Constant, ast.BinOp)) and (
                is_child_node_a_dict_value(child_idx, parent))
        ):
            is_node_straight_assignment = True
    return is_node_straight_assignment


def is_node_getenv_call(node: ast.AST, parent: ast.AST, child_idx: int) -> bool:
    """
    Check that we don't use os.getenv to get settings value.
    """
    if not (
        isinstance(parent, (ast.List, ast.Assign, ast.Tuple))
        or (
            isinstance(parent, (ast.Dict))
            and is_child_node_a_dict_value(child_idx, parent)
        )
    ):
        return False
    # os.environ['foo']
    if isinstance(node, ast.Subscript):
        target_node = node.value
        if (
                isinstance(target_node, ast.Attribute)
                and target_node.value.id == 'os'   # type: ignore
                and target_node.attr == 'environ'
        ):
            return True
    if not isinstance(node, ast.Call):
        return False
    # getenv('foo', '')
    if isinstance(node.func, ast.Name):
        return node.func.id == 'getenv'
    elif isinstance(node.func, ast.Attribute):
        target_node = node.func
        # os.getenv('foo', '')
        if isinstance(target_node.value, ast.Name):
            if target_node.value.id == 'os':
                if target_node.attr == 'getenv':
                    return True
        # os.environ.get('foo', '')
        else:
            if target_node.value.value.id == 'os':  # type: ignore
                if target_node.value.attr == 'environ':  # type: ignore
                    return True
    return False


def get_line_numbers_of_wrong_assignments(
    node: ast.AST,
    ast_content: typing.Optional[str],
    parent: ast.AST,
    child_idx: int,
) -> typing.Tuple[typing.Set[int], typing.Set[int], typing.Set[int]]:
    lines_with_straight_assignment: typing.Set[int] = set()
    lines_with_static_objects: typing.Set[int] = set()
    lines_with_getenv: typing.Set[int] = set()

    if is_node_getenv_call(node, parent, child_idx):
        lines_with_getenv.add(node.lineno)
    if isinstance(node, (ast.Call)):
        return set(), set(), lines_with_getenv

    if is_node_static(node):
        lines_with_static_objects.add(node.lineno)

    if is_node_straight_assignment(node, parent, child_idx):
        lines_with_straight_assignment.add(node.lineno)
    elif not is_node_static(node):
        child_idx = 0
        for child_node in ast.iter_child_nodes(node):
            (
                child_in_straight_assignment,
                child_in_static_objects,
                child_in_getenv,
            ) = get_line_numbers_of_wrong_assignments(
                child_node, ast_content, node, child_idx
            )
            lines_with_straight_assignment.update(child_in_straight_assignment)
            lines_with_static_objects.update(child_in_static_objects)
            lines_with_getenv.update(child_in_getenv)
            child_idx += 1

    lines_with_static_objects = lines_with_static_objects.difference(lines_with_straight_assignment)
    return lines_with_straight_assignment, lines_with_static_objects, lines_with_getenv


def exclude_lines_with_noqa(filepath: str) -> typing.Set[int]:
    with tokenize.open(filepath) as f:
        line_numbers_with_noqa: typing.Set[int] = set()
        for line in tokenize.generate_tokens(f.readline):
            for noqa in NOQA_FOR_SETTINGS_VARIABLES:
                if tokenize.COMMENT in line and noqa in line.string:
                    line_numbers_with_noqa.add(line.start[0])
    return line_numbers_with_noqa


def main() -> typing.Optional[int]:
    settings_files = [
        filepath
        for filepath in get_input_files()
        if 'settings/' in filepath and not filepath.endswith('/__init__.py')
    ]

    straight_assignment_error = False
    for settings_filepath in settings_files:
        ast_tree, ast_content = get_ast_tree_with_content(settings_filepath)
        if ast_tree is None:
            continue

        lines_with_noqa = exclude_lines_with_noqa(settings_filepath)
        (
            lines_with_straight_assignment,
            lines_with_static_objects,
            lines_with_getenv,
        ) = get_line_numbers_of_wrong_assignments(ast_tree, ast_content, ast_tree, 0)
        lines_with_straight_assignment = lines_with_straight_assignment.difference(lines_with_noqa)
        lines_with_static_objects = lines_with_static_objects.difference(lines_with_noqa)
        lines_with_getenv = lines_with_getenv.difference(lines_with_noqa)

        for line_number in sorted(lines_with_straight_assignment):
            print(f'{settings_filepath}:{line_number} : straight assignment')  # noqa: T001
            straight_assignment_error = True
        for line_number in sorted(lines_with_static_objects):
            print(f'{settings_filepath}:{line_number} : static object')  # noqa: T001
            straight_assignment_error = True

    if straight_assignment_error:
        return 1


if __name__ == '__main__':
    exit(main())

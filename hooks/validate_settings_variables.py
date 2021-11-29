from __future__ import annotations

import ast
import dataclasses
import enum
import tokenize
import typing
from collections import deque

from hooks.utils.ast_helpers import get_ast_tree_with_content
from hooks.utils.pre_commit import get_input_files

NOQA_FOR_SETTINGS_VARIABLES = [
    '# noqa: allowed straight assignment',
    '# noqa: static object',
]


class Reasons(enum.Enum):
    STRAIGHT_ASSIGNMENT = 'straight assignment'
    STATIC_OBJECT = 'static object'
    GETENV = 'getenv usage'


@dataclasses.dataclass(frozen=True)
class LineError:
    lineno: int
    reason: Reasons

    def __str__(self) -> str:
        return f'{self.lineno} : {self.reason}'


def is_node_static(node: ast.AST) -> bool:
    if isinstance(node, (ast.List, ast.Dict, ast.Tuple)):
        child_nodes_with_straight_assignment = 0
        for child_node in ast.iter_child_nodes(node):
            if isinstance(
                child_node, (ast.Constant, ast.BinOp, ast.Load, ast.Store, ast.Starred)
            ):
                child_nodes_with_straight_assignment += 1
            else:
                child_nodes_with_straight_assignment += is_node_static(child_node)
        return child_nodes_with_straight_assignment == len(
            list(ast.iter_child_nodes(node))
        )
    else:
        return False


def is_child_node_a_dict_value(child_idx: int, parent: ast.AST) -> bool:
    """В словаре детские ноды идут в таком порядке: все ключи, затем все значения."""
    return child_idx >= (len(list(ast.iter_child_nodes(parent)))) // 2


def is_node_straight_assignment(node: ast.AST, parent: ast.AST, child_idx: int) -> bool:
    if len(list(ast.iter_child_nodes(node))):
        return False

    if isinstance(parent, (ast.List, ast.Assign, ast.Tuple)) and (
        isinstance(node, (ast.Constant, ast.BinOp))
    ):
        return True

    elif isinstance(parent, (ast.Dict)) and (
        isinstance(node, (ast.Constant, ast.BinOp))
        and (is_child_node_a_dict_value(child_idx, parent))
    ):
        return True
    return False


@dataclasses.dataclass
class AstRule:
    # тут должен быть тип ast.AST, но я не смог заставить mypy с ним работать
    ast_type: typing.Any
    attrs: typing.Dict[str, typing.Union[str, 'AstRule']]


def check_rule(root_rule: AstRule, root_node: ast.AST) -> bool:
    stack: typing.Deque[typing.Tuple[AstRule, ast.AST]] = deque()
    stack.append((root_rule, root_node))
    while stack:
        rule, node = stack.pop()
        if not isinstance(node, rule.ast_type):
            return False
        for name, value in rule.attrs.items():
            if isinstance(value, AstRule):
                child_node = getattr(node, name, None)
                if child_node is None:
                    return False
                stack.append((value, child_node))
            else:
                if value != getattr(node, name, None):
                    return False
    return True


GETENV_RULES = [
    # os.environ['foo']
    # "Subscript(value=Attribute(value=Name(id='os', ctx=Load()), attr='environ', "
    # "ctx=Load()), slice=Index(value=Constant(value='foo', kind=None)), "
    # 'ctx=Load())'
    AstRule(
        ast.Subscript,
        {
            'value': AstRule(
                ast.Attribute,
                {
                    'attr': 'environ',
                    'value': AstRule(ast.Name, {'id': 'os'}),
                },
            ),
        },
    ),
    # getenv('foo', '')
    # "Call(func=Name(id='getenv', ctx=Load()), args=[Constant(value='foo', "
    # "kind=None), Constant(value='', kind=None)], keywords=[])"
    AstRule(
        ast.Call,
        {
            'func': AstRule(
                ast.Name,
                {'id': 'getenv'},
            ),
        },
    ),
    # os.getenv('foo', '')
    # "Call(func=Attribute(value=Name(id='os', ctx=Load()), attr='getenv', "
    # "ctx=Load()), args=[Constant(value='foo', kind=None), Constant(value='', "
    # 'kind=None)], keywords=[])'
    AstRule(
        ast.Call,
        {
            'func': AstRule(
                ast.Attribute,
                {
                    'attr': 'getenv',
                    'value': AstRule(
                        ast.Name,
                        {'id': 'os'},
                    ),
                },
            ),
        },
    ),
    # os.environ.get('foo', '')
    # "Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), "
    # "attr='environ', ctx=Load()), attr='get', ctx=Load()), "
    # "args=[Constant(value='foo', kind=None), Constant(value='', kind=None)], "
    # 'keywords=[])'
    AstRule(
        ast.Call,
        {
            'func': AstRule(
                ast.Attribute,
                {
                    'value': AstRule(
                        ast.Attribute,
                        {
                            'attr': 'environ',
                            'value': AstRule(
                                ast.Name,
                                {
                                    'id': 'os',
                                },
                            ),
                        },
                    ),
                },
            ),
        },
    ),
]


def find_node_with_getenv_call(node: ast.AST, parent: ast.AST, child_idx: int) -> typing.Optional[ast.AST]:
    """
    Find node, where getenv is called.
    """
    for n in ast.walk(node):
        if any([check_rule(rule, n) for rule in GETENV_RULES]):
            return n
    return None


def find_line_errors(
    node: ast.AST,
    ast_content: typing.Optional[str],
    parent: ast.AST,
    child_idx: int = 0,
) -> typing.Iterator[LineError]:
    bad_node = find_node_with_getenv_call(node, parent, child_idx)
    if bad_node:
        yield LineError(bad_node.lineno, Reasons.GETENV)
    if isinstance(node, (ast.Call)):
        return

    if is_node_static(node):
        yield LineError(node.lineno, Reasons.STATIC_OBJECT)

    if is_node_straight_assignment(node, parent, child_idx):
        yield LineError(node.lineno, Reasons.STRAIGHT_ASSIGNMENT)
    elif not is_node_static(node):
        for child_idx, child_node in enumerate(ast.iter_child_nodes(node)):
            yield from find_line_errors(
                child_node, ast_content, node, child_idx
            )


def get_line_numbers_of_wrong_assignments(
    node: ast.AST,
    ast_content: typing.Optional[str],
    parent: ast.AST,
) -> typing.Sequence[LineError]:
    line_errors: typing.List[LineError] = list(find_line_errors(node, ast_content, parent))

    uniq_errors: typing.Set[LineError] = set()
    result = []
    for line_error in sorted(line_errors, key=lambda le: le.lineno):
        if line_error in uniq_errors:
            continue
        uniq_errors.add(line_error)
        result.append(line_error)
    return result


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

    fail = False
    for settings_filepath in settings_files:
        ast_tree, ast_content = get_ast_tree_with_content(settings_filepath)
        if ast_tree is None:
            continue

        lines_with_noqa = exclude_lines_with_noqa(settings_filepath)
        line_errors = [
            line_error
            for line_error in get_line_numbers_of_wrong_assignments(
                ast_tree, ast_content, ast_tree
            )
            if line_error.lineno not in lines_with_noqa
        ]

        for line_error in sorted(line_errors, key=lambda le: le.lineno):
            print(f'{settings_filepath}:{line_error}')
            fail = True

    if fail:
        return 1


if __name__ == '__main__':
    exit(main())

from __future__ import annotations
import os
import ast
from typing import List, Iterator, Tuple, Union, Iterable, Optional, Set, Type, Callable, Any
import itertools

from hooks.utils.mypy_api_helpers import is_path_should_be_skipped
from hooks.utils.list_utils import flat


AnyFuncdef = Union[ast.FunctionDef, ast.AsyncFunctionDef]


def get_classdef_methods(node: ast.ClassDef) -> Iterable[ast.FunctionDef]:
    for body_node in node.body:
        if isinstance(body_node, ast.FunctionDef):
            yield body_node


def function_def_has_decorator(node: ast.FunctionDef, decorator_name: str) -> bool:
    if not node.decorator_list:
        return False

    decorator_names = []

    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name):
            decorator_names.append(decorator.id)
        if isinstance(decorator, ast.Call):
            decorator_names.append(decorator.func.id)  # type: ignore

    return decorator_name in decorator_names


def iterate_files_in(path: str, dirs_to_exclude: List[str], file_extension: str) -> Iterator[str]:
    for root, _, files in os.walk(path):
        for filename in files:
            if not filename.endswith(f'.{file_extension}'):
                continue
            filepath = os.path.abspath(os.path.join(root, filename))
            if is_path_should_be_skipped(filepath, dirs_to_exclude):
                continue
            yield filepath


def get_ast_tree_with_content(pyfilepath: str, set_parents: bool = False) -> Tuple[Optional[ast.Module], Optional[str]]:
    with open(pyfilepath, 'r') as file_handler:
        try:
            file_content = file_handler.read()
        except UnicodeDecodeError:
            return None, None
    ast_tree = ast.parse(file_content)
    if set_parents:
        for node in ast.walk(ast_tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node  # type: ignore
        ast_tree.parent = None  # type: ignore
    return ast_tree, file_content


def get_ast_tree(pyfilepath: str) -> Optional[ast.Module]:
    return get_ast_tree_with_content(pyfilepath)[0]


def get_classdef_assignments(node: ast.ClassDef) -> Iterable[ast.Assign]:
    for node_element in node.body:
        if isinstance(node_element, ast.Assign):
            yield node_element


def get_assign_name(node: ast.Assign) -> str:
    if node.targets[0]:
        return node.targets[0].id  # type: ignore


def get_var_names_from_assignment(
    assignment_node: Union[ast.Assign, ast.AnnAssign],
) -> List[Tuple[str, ast.AST]]:
    if isinstance(assignment_node, ast.AnnAssign):
        if isinstance(assignment_node.target, ast.Name):
            return [(assignment_node.target.id, assignment_node.target)]
    elif isinstance(assignment_node, ast.Assign):
        names = [t for t in assignment_node.targets if isinstance(t, ast.Name)]
        return [(n.id, n) for n in names]
    return []


def get_var_names_from_funcdef(funcdef_node: ast.FunctionDef) -> List[Tuple[str, ast.arg]]:
    vars_info = []
    for arg in funcdef_node.args.args:
        vars_info.append((arg.arg, arg))
    return vars_info


def get_var_names_from_for(for_node: ast.For) -> List[Tuple[str, ast.AST]]:
    if isinstance(for_node.target, ast.Name):
        return [(for_node.target.id, for_node.target)]
    elif isinstance(for_node.target, ast.Tuple):
        return [(n.id, n) for n in for_node.target.elts if isinstance(n, ast.Name)]
    return []


def extract_all_variable_names(ast_tree: ast.AST) -> List[Tuple[str, ast.AST]]:
    var_info: List[Tuple[str, ast.AST]] = []
    assignments = [n for n in ast.walk(ast_tree) if isinstance(n, ast.Assign)]
    var_info += flat([get_var_names_from_assignment(a) for a in assignments])
    ann_assignments = [n for n in ast.walk(ast_tree) if isinstance(n, ast.AnnAssign)]
    var_info += flat([get_var_names_from_assignment(a) for a in ann_assignments])
    funcdefs = [n for n in ast.walk(ast_tree) if isinstance(n, ast.FunctionDef)]
    var_info += flat([get_var_names_from_funcdef(f) for f in funcdefs])
    fors = [n for n in ast.walk(ast_tree) if isinstance(n, ast.For)]
    var_info += flat([get_var_names_from_for(f) for f in fors])
    return var_info


def iterate_over_expressions(node: ast.AST) -> Iterable[ast.AST]:
    nodes_with_subnodes = (ast.FunctionDef, ast.If, ast.For, ast.Module, ast.ClassDef, ast.Try, ast.With, ast.While)
    if isinstance(node, (ast.If, ast.While)):
        yield node.test
    elif isinstance(node, ast.For):
        yield node.iter
    nodes_to_iter = node.body  # type: ignore
    if isinstance(node, ast.Try):
        nodes_to_iter = itertools.chain(node.body, node.finalbody, *[n.body for n in node.handlers])
    for child_node in nodes_to_iter:
        if isinstance(child_node, nodes_with_subnodes):
            for subnode in iterate_over_expressions(child_node):
                yield subnode
        else:
            yield child_node


def get_variable_node_by_name(node: ast.AST, target_variable: str) -> Optional[ast.Assign]:
    for child_node in iterate_over_expressions(node):
        if isinstance(child_node, ast.Assign):
            if target_variable in (name for name, _ in get_var_names_from_assignment(child_node)):
                return child_node


def is_django_orm_query(node: ast.AST) -> bool:
    django_orm_typical_methods = {
        'objects',
        'filter',
        'annotate',
        'select_related',
        'prefetch_related',
        'distinct',
    }
    total_points_to_be_threated_as_django_orm_query = 0
    points_required_to_be_threated_as_django_orm_query = 2
    for attribute_node in [n for n in ast.walk(node) if isinstance(n, ast.Attribute)]:
        if attribute_node.attr in django_orm_typical_methods:
            total_points_to_be_threated_as_django_orm_query += 1
    return total_points_to_be_threated_as_django_orm_query >= points_required_to_be_threated_as_django_orm_query


def is_import_from(import_node: Union[ast.Import, ast.ImportFrom], package_name: str) -> bool:  # noqa: CCR001
    prefix = f'{package_name}.'
    if isinstance(import_node, ast.Import):
        for import_alias in import_node.names:
            if import_alias.name == package_name or import_alias.name.startswith(prefix):
                return True
    elif isinstance(import_node, ast.ImportFrom):
        if import_node.module and (import_node.module == package_name or import_node.module.startswith(prefix)):
            return True
        full_imported_names = [f'{import_node.module}.{a.name}' for a in import_node.names]
        for imported_name in full_imported_names:
            if imported_name == package_name or imported_name.startswith(prefix):
                return True
    return False


def get_imports_from(package_name: str, ast_tree: ast.AST) -> List[Union[ast.Import, ast.ImportFrom]]:
    imports: List[Union[ast.Import, ast.ImportFrom]] = []
    for import_node in ast.walk(ast_tree):
        if not isinstance(import_node, (ast.Import, ast.ImportFrom)):
            continue
        if is_import_from(import_node, package_name):
            imports.append(import_node)
    return imports


def has_import_of_function_from_package(
    ast_tree: ast.AST, package_name: str, function_name: str,
) -> bool:
    url_import_from_nodes = get_imports_from(package_name, ast_tree=ast_tree)

    for import_node in url_import_from_nodes:
        for import_node_name in import_node.names:
            if import_node_name.name == function_name:
                return True

    return False


def _is_classdef_has_base_classes(
    classdef_node: ast.ClassDef,
    base_classess: Set[str],
    module_name: Optional[str],
) -> bool:
    if not classdef_node.bases:
        return False
    bases_names = None
    try:
        bases_names = {b.id for b in classdef_node.bases}  # type: ignore
    except AttributeError:
        pass
    if bases_names and bases_names.intersection(base_classess):
        return True

    if module_name:
        for base_node in classdef_node.bases:
            if (
                isinstance(base_node, ast.Attribute) and base_node.attr in base_classess
                and isinstance(base_node.value, ast.Name) and base_node.value.id == module_name
            ):
                return True
    return False


def _inherited_from_base_model(classdef_node: ast.ClassDef) -> bool:
    base_models_classes_names = {
        'Model',
        'AbstractBaseUser',
    }
    return _is_classdef_has_base_classes(classdef_node, base_models_classes_names, 'models')


def _has_meta_subclass(classdef_node: ast.ClassDef) -> bool:
    for subnode in classdef_node.body:
        if isinstance(subnode, ast.ClassDef) and subnode.name == 'Meta':
            return True
    return False


def _has_common_model_methods_overload(classdef_node: ast.ClassDef) -> bool:
    common_methods_names = {'save', 'delete'}
    for subnode in classdef_node.body:
        if isinstance(subnode, ast.FunctionDef) and subnode.name in common_methods_names:
            return True
    return False


def is_django_model_definition(classdef_node: ast.ClassDef) -> bool:
    min_score_to_match = 3
    scorers = [
        (_inherited_from_base_model, 3),
        (_has_meta_subclass, 2),
        (_has_common_model_methods_overload, 1),
    ]
    current_score = 0
    for scorer, score in scorers:
        if scorer(classdef_node):
            current_score += score
    return current_score >= min_score_to_match


def is_enum_definition(classdef_node: ast.ClassDef) -> bool:
    return _is_classdef_has_base_classes(classdef_node, {'Enum', 'IntEnum'}, 'enum')


def get_not_ok_base_nodes_from(
    ast_tree: ast.Module,
    allowed_ast_nodes: Set[Type],
    conditionals_ast_nodes: List[Tuple[Type, Callable[[Any], Any]]],
) -> List[ast.AST]:
    bad_nodes: List[ast.AST] = []
    for node in ast_tree.body:
        is_node_ok = False
        if isinstance(node, tuple(allowed_ast_nodes)):
            continue
        for condition_node_type, condition in conditionals_ast_nodes:
            if isinstance(node, condition_node_type) and condition(node):
                is_node_ok = True
                break
        if not is_node_ok:
            bad_nodes.append(node)
    return bad_nodes


def get_all_funcdefs(ast_tree: ast.AST) -> List[AnyFuncdef]:
    return [n for n in ast.walk(ast_tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def get_assignments_to(
    ast_tree: ast.AST, target_name: str,
) -> List[Union[ast.Assign, ast.AnnAssign, ast.AugAssign]]:
    return [
        ast_node for ast_node in ast.walk(ast_tree)
        if (
            isinstance(ast_node, ast.Assign)
            and any(
                target.id == target_name for target in ast_node.targets
                if isinstance(target, ast.Name)
            )
        )
        or (
            isinstance(ast_node, (ast.AnnAssign, ast.AugAssign))
            and isinstance(ast_node.target, ast.Name)
            and ast_node.target.id == target_name
        )
    ]


def logger_ast_nodes_conditional(
    logger_object_name: str = 'logger',
) -> List[Tuple[Type, Callable[[Any], Any]]]:
    return [
        (  # определения логгера (logger = logging.getLogger(__name__))
            ast.Assign,
            lambda n: (
                n.targets
                and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id == logger_object_name
            ),
        ),
        (  # конфиг логгера (logger.setLevel(logging.DEBUG))
            ast.Expr,
            lambda n: (
                isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Attribute)
                and isinstance(n.value.func.value, ast.Name)
                and n.value.func.value.id == logger_object_name
            ),
        ),
    ]


def get_full_imported_name(import_node: Union[ast.Import, ast.ImportFrom]) -> List[str]:
    if isinstance(import_node, ast.ImportFrom):
        return [f'{import_node.module}.{n.name}' for n in import_node.names]
    elif isinstance(import_node, ast.Import):
        return [n.name for n in import_node.names]


def get_check_decorators_includes(decorators_set: Set[str]) -> Callable[[ast.ClassDef], bool]:
    def _decorator_includes(classdef_node: ast.ClassDef) -> bool:
        if not classdef_node.decorator_list:
            return False
        decorators = None
        try:
            decorators = {d.id for d in classdef_node.decorator_list if isinstance(d, ast.Name)}
        except AttributeError:
            pass
        if decorators and decorators.intersection(decorators_set):
            return True

        return False
    return _decorator_includes

from __future__ import annotations

import ast
import re
import sys
from typing import Iterable, Iterator, List, NamedTuple, Optional

from hooks.utils.ast_helpers import get_ast_tree
from hooks.utils.common_types import AssignOrAnnAssign
from hooks.utils.pre_commit import get_input_files

BOOLEAN_VERBS = (
    'is',
    'was',
    'has',
    'needs',
    'should',
)


class BaseValidator:
    # Human-readable field name template, only for error reporting
    field_name_format: str

    def validate(self, field_name: str) -> bool:
        raise NotImplementedError


class DateTimeValidator(BaseValidator):
    field_name_format = 'xxx_at'

    def validate(self, field_name: str) -> bool:
        return field_name.endswith('_at')


class DateValidator(BaseValidator):
    field_name_format = 'xxx_date'

    def validate(self, field_name: str) -> bool:
        return field_name.endswith('_date')


class BooleanValidator(BaseValidator):
    def __init__(self) -> None:
        verbs_options = '|'.join(BOOLEAN_VERBS)
        self._regex = re.compile(fr'(?:[a-z0-9_]+_)?({verbs_options})_[a-z0-9_]+')
        self.field_name_format = f'[xxx_]({verbs_options})_xxx'

    def validate(self, field_name: str) -> bool:
        return self._regex.fullmatch(field_name) is not None


datetime_validator = DateTimeValidator()
date_validator = DateValidator()
boolean_validator = BooleanValidator()


VALIDATORS = [
    ('DateTime', datetime_validator),
    ('Date', date_validator),
    ('Boolean', boolean_validator),
]


def get_validator(field_type: str) -> Optional[BaseValidator]:
    if not field_type.endswith('Field'):
        return None
    for stem, validator in VALIDATORS:
        if stem in field_type:
            return validator
    return None


class Error(NamedTuple):
    filepath: str
    lineno: int
    field_name: str
    field_type: str
    validator: BaseValidator

    def __str__(self) -> str:
        return (
            f'{self.filepath}:{self.lineno} '
            f'{self.field_type} "{self.field_name}" should be named "{self.validator.field_name_format}"'
        )


def is_models_filepath(filepath: str) -> bool:
    return filepath.endswith('/models.py') or '/models/' in filepath


def iterate_module_classdef_assigns(module: ast.Module) -> Iterator[AssignOrAnnAssign]:
    for node in module.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for child_node in node.body:
            if isinstance(child_node, (ast.Assign, ast.AnnAssign)):
                yield child_node


def get_assign_target_name(assign: AssignOrAnnAssign) -> Optional[str]:
    if isinstance(assign, ast.AnnAssign):
        target = assign.target
    else:
        target = assign.targets[0]
    if not isinstance(target, ast.Name):
        return None
    return target.id


def get_call_func_name(call: ast.Call) -> Optional[str]:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def check_assign(assign: AssignOrAnnAssign, filepath: str) -> Optional[Error]:
    if not isinstance(assign.value, ast.Call):
        return None
    field_name = get_assign_target_name(assign)
    if not field_name:
        return None
    func_name = get_call_func_name(assign.value)
    if not func_name:
        return None
    validator = get_validator(func_name)
    if not validator or validator.validate(field_name):
        return None
    return Error(
        filepath=filepath,
        lineno=assign.lineno,
        field_name=field_name,
        field_type=func_name,
        validator=validator,
    )


def validate(filepaths: Iterable[str]) -> List[Error]:
    errors = []
    for models_filepath in filter(is_models_filepath, filepaths):
        module = get_ast_tree(models_filepath)
        if not module:
            continue
        for assign in iterate_module_classdef_assigns(module):
            error = check_assign(assign, models_filepath)
            if error:
                errors.append(error)
                print(error)  # noqa: T001
    return errors


def main() -> int:
    errors = validate(get_input_files())
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())

from __future__ import annotations

import dataclasses
import typing

from libcst import FunctionDef
from libcst import matchers as m
from libcst import parse_module
from libcst.metadata import MetadataWrapper, PositionProvider

from hooks.utils.pre_commit import get_input_files


@dataclasses.dataclass()
class Error:
    line: int
    function_name: str


APP_TASK_DECORATOR_ATTRIBUTE = m.Attribute(value=m.Name(value='app'), attr=m.Name(value='task'))
ASYNC_RESULT_OR_NONE_MATCHER = m.OneOf(m.Name(value='None'), m.Name(value='AsyncTaskResult'))
APP_TASK_DECORATOR_MATCHER = m.Decorator(
    decorator=m.Call(func=APP_TASK_DECORATOR_ATTRIBUTE) | APP_TASK_DECORATOR_ATTRIBUTE
)
FUNC_RETURN_NONE_OR_ASYNC_RESULT_MATCHER = m.FunctionDef(
    returns=(
        m.Annotation(
            annotation=ASYNC_RESULT_OR_NONE_MATCHER
            | m.BinaryOperation(
                left=ASYNC_RESULT_OR_NONE_MATCHER, right=ASYNC_RESULT_OR_NONE_MATCHER
            )
        )
    )
)


class ReturnAnnotationValidator(m.MatcherDecoratableVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self) -> None:
        super().__init__()
        self.errors: list[Error] = []

    @m.call_if_inside(m.FunctionDef())
    def visit_FunctionDef(self, node: FunctionDef) -> None:
        position = self.get_metadata(PositionProvider, node).start
        function_name = node.name.value
        for decorator in node.decorators:
            if self.matches(decorator, APP_TASK_DECORATOR_MATCHER):
                if not self.matches(node, FUNC_RETURN_NONE_OR_ASYNC_RESULT_MATCHER):
                    self.errors.append(Error(line=position.line, function_name=function_name))
                break


def validate_return_types(file_content: str) -> typing.List[Error]:
    validator = ReturnAnnotationValidator()
    module = parse_module(file_content)
    MetadataWrapper(module).visit(validator)
    return validator.errors


def main() -> typing.Optional[int]:
    files = get_input_files(extension='py')
    has_errors = False
    for filepath in files:
        with open(filepath) as f:
            errors = validate_return_types(f.read())
        if errors:
            has_errors = True
        for error in errors:
            print(  # noqa: T001
                f'{filepath}:{error.line}:{error.function_name} Invalid return type '
                'should be AsyncTaskResult or None',
            )

    if has_errors:
        return 1
    return 0


if __name__ == '__main__':
    main()

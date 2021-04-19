from __future__ import annotations

from collections import namedtuple
from typing import Iterator, List, cast

import libcst
from libcst import Assign, SimpleStatementLine
from libcst import matchers as m
from libcst.metadata import MetadataWrapper, PositionProvider

from hooks.utils.pre_commit import get_input_files

VALID_COMMENTS_FOR_NULL_TRUE = {'# null_by_design', '# null_for_compatibility'}

Error = namedtuple('Error', 'line, col, field')

null_comment = m.TrailingWhitespace(
    comment=m.Comment(m.MatchIfTrue(lambda n: n in VALID_COMMENTS_FOR_NULL_TRUE)),
    newline=m.Newline(),
)


field_without_comment = m.SimpleStatementLine(
    body=[
        m.Assign(
            value=(
                m.Call(
                    args=[
                        m.ZeroOrMore(),
                        m.Arg(keyword=m.Name('null'), value=m.Name('True')),
                        m.ZeroOrMore(),
                    ],
                    whitespace_before_args=m.DoesNotMatch(m.ParenthesizedWhitespace(null_comment)),
                )
                | m.Call(
                    func=m.Attribute(attr=m.Name('NullBooleanField')),
                    whitespace_before_args=m.DoesNotMatch(m.ParenthesizedWhitespace(null_comment)),
                )
                | m.Call(
                    func=m.Name('NullBooleanField'),
                    whitespace_before_args=m.DoesNotMatch(m.ParenthesizedWhitespace(null_comment)),
                )
            )
        )
    ],
    trailing_whitespace=m.DoesNotMatch(null_comment),
)


class FieldValidator(m.MatcherDecoratableVisitor):
    errors: List[Error] = []

    METADATA_DEPENDENCIES = (PositionProvider,)

    @m.call_if_inside(m.ClassDef())
    def visit_SimpleStatementLine(self, node: SimpleStatementLine) -> None:
        if self.matches(node, field_without_comment):
            position = self.get_metadata(PositionProvider, node).start
            field_name = cast(Assign, node.body[0]).targets[0].target.value
            self.errors.append(Error(position.line, position.column, field_name))


def get_input_models_files(
    args: List[str] = None, dirs_to_exclude: List[str] = None
) -> Iterator[str]:
    return (
        filepath
        for filepath in get_input_files(args, dirs_to_exclude, 'py')
        if filepath.endswith('/models.py') or '/models/' in filepath
    )


def validate_null_comments(file_content: str) -> List[Error]:
    validator = FieldValidator()
    module = libcst.parse_module(file_content)
    MetadataWrapper(module).visit(validator)
    return validator.errors


def main() -> int:
    has_errors = False
    for model_file_path in get_input_models_files():
        with open(model_file_path) as f:
            errors = validate_null_comments(f.read())
            if errors:
                has_errors = True
                for line, col, field in errors:
                    print(  # noqa: T001
                        f'{model_file_path}:{line}:{col} Field "{field}" needs '
                        'a valid comment for its\' "null=True"',
                    )

    if has_errors:
        return 1

    return 0


if __name__ == '__main__':
    exit(main())

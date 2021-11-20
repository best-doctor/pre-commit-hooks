from __future__ import annotations

import argparse
import contextlib
import re
import typing

import libcst as cst
from libcst import matchers as m
from libcst.metadata import PositionProvider

from hooks.utils.pre_commit import get_input_files

DEFAULT_VALID_DEPRECATION_COMMENT_REGEX = (
    r'#? deprecated (?P<ticket_id>[A-Z][A-Z,0-9]+-[0-9]+) (?P<deprecation_date>\d{2}\.\d{2}\.\d{4})'
)
DEFAULT_DEPRECATION_COMMENT_MARKER_REGEX = 'deprecated'


class Error(typing.NamedTuple):
    model_file_path: str
    line: int
    col: int
    field: str

    def __str__(self) -> str:
        return (
            f'{self.model_file_path}:{self.line}:{self.col} '
            f'Field "{self.field}" needs a valid deprecation comment'
        )


def is_model_field_type(name: str) -> bool:
    return name.endswith(('Field', 'ForeignKey'))


_any_comment = m.TrailingWhitespace(
    comment=m.Comment(m.MatchIfTrue(lambda n: n.startswith('#'))), newline=m.Newline()
)

_django_model_field_name_value = m.Call(
    func=m.Attribute(attr=m.Name(m.MatchIfTrue(is_model_field_type)))
) | m.Call(func=m.Name(m.MatchIfTrue(is_model_field_type)))

_django_model_field_name_with_leading_comment_value = m.Call(
    func=m.Attribute(attr=m.Name(m.MatchIfTrue(is_model_field_type))),
    whitespace_before_args=m.ParenthesizedWhitespace(_any_comment),
) | m.Call(
    func=m.Name(m.MatchIfTrue(is_model_field_type)),
    whitespace_before_args=m.ParenthesizedWhitespace(_any_comment),
)

_django_model_field_with_leading_comment = m.SimpleStatementLine(
    body=[
        m.Assign(value=_django_model_field_name_with_leading_comment_value)
        | m.AnnAssign(value=_django_model_field_name_with_leading_comment_value)
    ]
)

_django_model_field_with_trailing_comment = m.SimpleStatementLine(
    body=[
        m.Assign(value=_django_model_field_name_value)
        | m.AnnAssign(value=_django_model_field_name_value)
    ],
    trailing_whitespace=_any_comment,
)

django_model_field_with_comments = (
    _django_model_field_with_leading_comment | _django_model_field_with_trailing_comment
)


def get_leading_comment(node: cst.SimpleStatementLine) -> typing.Optional[str]:
    with contextlib.suppress(IndexError, AttributeError):
        return node.body[0].value.whitespace_before_args.first_line.comment.value.strip()

    return None


def get_trailing_comment(node: cst.SimpleStatementLine) -> typing.Optional[str]:
    with contextlib.suppress(AttributeError):
        return node.trailing_whitespace.comment.value.strip()

    return None


def get_model_field_name(node: cst.SimpleStatementLine) -> str:
    if isinstance(node.body[0], cst.AnnAssign):
        return node.body[0].target.value
    else:
        return node.body[0].targets[0].target.value


class DeprecatedModelFieldValidator(m.MatcherDecoratableVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(
        self,
        model_file_path: str,
        valid_deprecation_comment_pattern: re.Pattern,
        deprecation_comment_marker_pattern: re.Pattern,
    ):
        super().__init__()

        self.model_file_path = model_file_path
        self.valid_deprecation_comment_pattern = valid_deprecation_comment_pattern
        self.deprecation_comment_marker_pattern = deprecation_comment_marker_pattern
        self.errors: typing.List[Error] = []

    def is_deprecation_comment(self, comment: str) -> bool:
        return self.deprecation_comment_marker_pattern.search(comment) is not None

    def is_valid_deprecation_comment(self, comment: str) -> bool:
        return self.valid_deprecation_comment_pattern.search(comment) is not None

    @m.call_if_inside(m.ClassDef())
    def visit_SimpleStatementLine(self, node: cst.SimpleStatementLine) -> None:  # noqa: N802 C901
        if not self.matches(node, django_model_field_with_comments):
            return None

        leading_comment = get_leading_comment(node)
        trailing_comment = get_trailing_comment(node)

        if leading_comment and self.is_deprecation_comment(leading_comment):
            is_valid_deprecation_comment = self.is_valid_deprecation_comment(leading_comment)
        elif trailing_comment and self.is_deprecation_comment(trailing_comment):
            is_valid_deprecation_comment = self.is_valid_deprecation_comment(trailing_comment)
        else:
            return None

        if not is_valid_deprecation_comment:
            position = self.get_metadata(PositionProvider, node)
            self.errors.append(
                Error(
                    self.model_file_path,
                    position.start.line,
                    position.start.column,
                    get_model_field_name(node),
                )
            )

    def run_for_module(self, module: cst.Module) -> DeprecatedModelFieldValidator:
        cst.MetadataWrapper(module).visit(self)
        return self


def get_input_models_files(
    args: typing.List[str] = None, dirs_to_exclude: typing.List[str] = None
) -> typing.Iterator[str]:
    return (
        filepath
        for filepath in get_input_files(args, dirs_to_exclude, 'py')
        if filepath.endswith('/models.py') or '/models/' in filepath
    )


def validate_deprecated_model_field_comments(
    model_file_path: str,
    valid_deprecation_comment_pattern: re.Pattern,
    deprecation_comment_marker_pattern: re.Pattern,
) -> typing.List[Error]:
    with open(model_file_path) as f:
        file_content = f.read()

    validator = DeprecatedModelFieldValidator(
        model_file_path, valid_deprecation_comment_pattern, deprecation_comment_marker_pattern
    )
    module = cst.parse_module(file_content)
    return validator.run_for_module(module).errors


def main(args: typing.Optional[typing.Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--valid-deprecation-comment-regex',
        default=DEFAULT_VALID_DEPRECATION_COMMENT_REGEX,
        help='A regex to validate deprecation comment',
    )
    parser.add_argument(
        '--deprecation-comment-marker-regex',
        default=DEFAULT_DEPRECATION_COMMENT_MARKER_REGEX,
        help=(
            'A regex to match deprecation comment. '
            'Indicates thad field was deprecated '
            '(without checking whether the deprecation comment is valid or not).'
        ),
    )
    args, _ = parser.parse_known_args(args)
    valid_deprecation_comment_pattern = re.compile(args.valid_deprecation_comment_regex)
    deprecation_comment_marker_pattern = re.compile(args.deprecation_comment_marker_regex)

    has_errors = False
    for model_file_path in get_input_models_files():
        errors = validate_deprecated_model_field_comments(
            model_file_path, valid_deprecation_comment_pattern, deprecation_comment_marker_pattern
        )
        if errors:
            has_errors = True
            for error in errors:
                print(error)  # noqa: T001

    if has_errors:
        print(f'HINT: Valid deprecation comment pattern: {args.valid_deprecation_comment_regex}')  # noqa: T001
        return 1

    return 0


if __name__ == '__main__':
    exit(main())

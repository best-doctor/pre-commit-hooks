from __future__ import annotations

import re
from typing import Iterator, List, Optional

from redbaron import RedBaron
from redbaron.nodes import CommentNode, Node

from hooks.utils.pre_commit import get_input_files

VALID_COMMENTS_FOR_NULL_TRUE = (
    'null_by_design',
    'null_for_compatibility',
)

NULL_TRUE_KWARG_RE = re.compile(r'[( ,\n]null=True')


def get_input_models_files(args: List[str] = None, dirs_to_exclude: List[str] = None) -> Iterator[str]:
    return (
        filepath for filepath in get_input_files(args, dirs_to_exclude, 'py')
        if filepath.endswith('/models.py') or '/models/' in filepath
    )


def has_valid_comment(comment: Optional[Node]) -> bool:
    if comment is None:
        return False

    comment = comment.dumps()
    for valid_comment in VALID_COMMENTS_FOR_NULL_TRUE:
        if valid_comment in comment:
            return True

    return False


def get_node_line(node: Node) -> int:
    return node.absolute_bounding_box.top_left.line


def main() -> Optional[int]:
    has_errors = False
    for model_file_path in get_input_models_files():
        with open(model_file_path) as f:
            baron_tree = RedBaron(f.read())
        for assignment in baron_tree.find_all('assignment'):
            nodes_to_check = [
                assignment.find('comment'),
            ]
            if isinstance(assignment.next, CommentNode):
                nodes_to_check.append(assignment.next)

            assignment_str = assignment.dumps()
            is_nullable_field = (
                NULL_TRUE_KWARG_RE.search(assignment_str)
                or 'NullBooleanField' in assignment_str
            )
            if is_nullable_field and not any(filter(has_valid_comment, nodes_to_check)):
                has_errors = True
                field_name = assignment.target
                print(  # noqa: T001
                    '{0}:{1} Field "{2}" needs a valid comment for its "null=True"'.format(
                        model_file_path, get_node_line(assignment), field_name,
                    ),
                )

    if has_errors:
        return 1


if __name__ == '__main__':
    exit(main())

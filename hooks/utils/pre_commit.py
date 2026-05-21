from __future__ import annotations

import os
import sys
from collections import defaultdict
from typing import Any, DefaultDict, Iterable, Iterator, List, Tuple

from hooks.utils.ast_helpers import iterate_files_in
from hooks.utils.mypy_api_helpers import get_exclude_dirs_from_config, is_path_should_be_skipped


def get_input_files(
    args: list[str] | None = None,
    dirs_to_exclude: list[str] | None = None,
    extension: str | None = None,
) -> Iterator[str]:
    if args is None:
        args = sys.argv[1:] if len(sys.argv) > 1 else ['.']

    if extension is None:
        extension = 'py'

    if dirs_to_exclude is None:
        dirs_to_exclude = get_exclude_dirs_from_config('flake8', 'exclude')

    for item in args:
        path = os.path.realpath(os.path.abspath(item))

        if (
            os.path.isfile(path)
            and path.endswith(f'.{extension}')
            and not is_path_should_be_skipped(path, dirs_to_exclude)
        ):
            yield path

        if os.path.isdir(path):
            yield from iterate_files_in(path, dirs_to_exclude, extension)


def get_input_test_files(args: list[str] | None = None) -> Iterator[str]:
    return (
        filepath
        for filepath in get_input_files(args)
        if (
            '/tests/' in filepath
            and (
                os.path.basename(filepath).startswith('test_')
                or os.path.basename(filepath).endswith('_test')
            )
        )
    )


def get_modules_files(
    input_files: Iterable[str], base_dir: str | None = None, only_modules: list[Any] | None = None
) -> List[Tuple[str, str, List[str]]]:
    """Группирует список файлов по их корневым модулям."""

    if base_dir is None:
        base_dir = os.getcwd()

    processed_modules: DefaultDict[str, List[str]] = defaultdict(list)
    for filepath in input_files:
        module_name = os.path.relpath(os.path.dirname(filepath), base_dir).split(os.sep)[0]
        if module_name == '.':
            continue

        if not only_modules or module_name in only_modules:
            processed_modules[module_name].append(filepath)

    return [
        (module_name, os.path.join(base_dir, module_name.replace('.', os.sep)), module_files)
        for module_name, module_files in processed_modules.items()
    ]


def is_django_model_file(file_path: str) -> bool:
    return os.path.basename(file_path) == 'models.py' or (
        os.path.basename(os.path.dirname(file_path)) == 'models' and file_path.endswith('.py')
    )

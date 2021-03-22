from __future__ import annotations

import argparse
import collections
from typing import DefaultDict, List, Optional

from hooks.utils.pre_commit import get_input_files


def count_amount_of_lines_in_file(filepath: str) -> int:
    with open(filepath, 'r', encoding='utf=8') as file:
        amount_of_lines = 0
        for _line in file:
            amount_of_lines += 1

    return amount_of_lines


def find_too_long_py_files(allowed_amount: int, filenames: List[str]) -> DefaultDict[str, int]:
    too_long_files: DefaultDict[str, int] = collections.defaultdict(int)
    for py_file_name in get_input_files(filenames):
        amount_of_lines = count_amount_of_lines_in_file(filepath=py_file_name)
        if amount_of_lines <= allowed_amount:
            continue
        too_long_files[py_file_name] = amount_of_lines

    return too_long_files


def main() -> Optional[int]:
    parser = argparse.ArgumentParser(description='Process allowed amount of lines.')
    parser.add_argument('--lines', type=int, default=1000, help='Allowed amount of lines')
    args, files = parser.parse_known_args()

    too_long_files = find_too_long_py_files(args.lines, files)
    for py_file_name, amount_of_lines in too_long_files.items():
        print(f'{amount_of_lines} lines in {py_file_name}. Allowed amount - {args.lines}')  # noqa: T001

    if too_long_files:
        return 1


if __name__ == '__main__':
    exit(main())

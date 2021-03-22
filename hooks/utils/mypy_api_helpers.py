from __future__ import annotations

import configparser

from typing import List, Optional, Set


def get_exclude_dirs_from_config(
    config_file_name: str,
    section_name: str = 'mypy',
    param_name: str = 'exclude',
) -> List[str]:
    exclude_param = get_param_from_config(config_file_name, section_name, param_name)
    return [] if exclude_param is None else exclude_param.split(',')


def get_param_from_config(
    config_file_name: str,
    section_name: str,
    param_name: str,
) -> Optional[str]:
    config = configparser.ConfigParser()
    config.read(config_file_name)
    try:
        return config[section_name][param_name]
    except KeyError:
        return None


def get_list_param_from_config(
    config_file_name: str,
    section_name: str,
    param_name: str,
) -> List[str]:
    raw_value = get_param_from_config(config_file_name, section_name, param_name)
    return [] if raw_value is None else [v.strip() for v in raw_value.split('\n') if v.strip()]


def is_path_should_be_skipped(
    path: str, dirs_to_exclude: List[str], files_to_exclude: Set[str] = None,
) -> bool:
    if files_to_exclude and path in files_to_exclude:
        return True
    for dir_to_exclude in dirs_to_exclude:
        if (
            dir_to_exclude == path
            or '/{0}/'.format(dir_to_exclude) in path
            or path.startswith('{0}/'.format(dir_to_exclude))
        ):
            return True
    return False

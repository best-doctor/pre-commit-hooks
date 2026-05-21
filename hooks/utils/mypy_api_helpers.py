from __future__ import annotations

import configparser
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, List, Mapping, Optional, Set, Tuple

_PYPROJECT_SECTION_PATHS: dict[str, Tuple[str, ...]] = {
    'flake8': ('tool', 'flake8'),
    'project_structure': ('tool', 'project_structure'),
    'mypy': ('tool', 'mypy'),
}

_SETUP_CFG_FALLBACK = 'setup.cfg'
_PYPROJECT_TOML = 'pyproject.toml'


def _get_toml_loader() -> Any | None:
    if sys.version_info >= (3, 11):
        import tomllib

        return tomllib
    try:
        import tomli
    except ImportError:
        return None
    return tomli


@lru_cache(maxsize=1)
def _load_pyproject_toml() -> Mapping[str, Any]:
    project_file = Path(_PYPROJECT_TOML)
    if not project_file.is_file():
        return {}
    toml_loader = _get_toml_loader()
    if toml_loader is None:
        return {}
    with project_file.open('rb') as project_file_handle:
        loaded = toml_loader.load(project_file_handle)
    return loaded if isinstance(loaded, dict) else {}


def _get_nested_mapping(root: Mapping[str, Any], keys: Tuple[str, ...]) -> Mapping[str, Any] | None:
    current: Any = root
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current if isinstance(current, Mapping) else None


def _normalize_config_scalar(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    return None


def _normalize_config_list(value: Any) -> Optional[List[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    scalar = _normalize_config_scalar(value)
    if scalar is None:
        return None
    return [line.strip() for line in scalar.split('\n') if line.strip()]


def _get_raw_from_pyproject(section_name: str, param_name: str) -> Any | None:
    section_path = _PYPROJECT_SECTION_PATHS.get(section_name)
    if section_path is None:
        return None
    section_mapping = _get_nested_mapping(_load_pyproject_toml(), section_path)
    if section_mapping is None:
        return None
    return section_mapping.get(param_name) or section_mapping.get(param_name.replace('-', '_'))


def get_param_from_configs(section_name: str, param_name: str) -> Optional[str]:
    pyproject_value = _get_raw_from_pyproject(section_name, param_name)
    if isinstance(pyproject_value, list):
        return ','.join(str(item) for item in pyproject_value)
    normalized_pyproject_value = _normalize_config_scalar(pyproject_value)
    if normalized_pyproject_value is not None:
        return normalized_pyproject_value
    return get_param_from_config(_SETUP_CFG_FALLBACK, section_name, param_name)


def get_list_param_from_configs(section_name: str, param_name: str) -> List[str]:
    pyproject_value = _get_raw_from_pyproject(section_name, param_name)
    pyproject_list = _normalize_config_list(pyproject_value)
    if pyproject_list is not None:
        return pyproject_list
    return get_list_param_from_config(_SETUP_CFG_FALLBACK, section_name, param_name)


def get_exclude_dirs_from_config(
    section_name: str = 'flake8', param_name: str = 'exclude'
) -> List[str]:
    exclude_param = get_param_from_configs(section_name, param_name)
    return (
        []
        if exclude_param is None
        else [item.strip() for item in exclude_param.split(',') if item.strip()]
    )


def get_param_from_config(
    config_file_name: str, section_name: str, param_name: str
) -> Optional[str]:
    config = configparser.ConfigParser()
    config.read(config_file_name)
    try:
        return config[section_name][param_name]
    except KeyError:
        return None


def get_list_param_from_config(
    config_file_name: str, section_name: str, param_name: str
) -> List[str]:
    raw_value = get_param_from_config(config_file_name, section_name, param_name)
    return (
        []
        if raw_value is None
        else [value.strip() for value in raw_value.split('\n') if value.strip()]
    )


def is_path_should_be_skipped(
    path: str, dirs_to_exclude: List[str], files_to_exclude: Set[str] | None = None
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

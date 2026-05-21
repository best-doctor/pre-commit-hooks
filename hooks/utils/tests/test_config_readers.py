from __future__ import annotations

import pytest

from hooks.utils.mypy_api_helpers import (
    _load_pyproject_toml,
    get_exclude_dirs_from_config,
    get_list_param_from_config,
    get_list_param_from_configs,
    get_param_from_config,
    get_param_from_configs,
)


@pytest.fixture(autouse=True)
def clear_pyproject_cache() -> None:
    _load_pyproject_toml.cache_clear()
    yield
    _load_pyproject_toml.cache_clear()


@pytest.mark.parametrize(
    'setup_cfg_content, section_name, param_name, expected_value',
    [
        pytest.param(
            '[flake8]\nadjustable-default-max-complexity = 7\n',
            'flake8',
            'adjustable-default-max-complexity',
            '7',
            id='flake8_scalar',
        ),
        pytest.param(
            '[flake8]\nexclude = venv, migrations\n',
            'flake8',
            'exclude',
            'venv, migrations',
            id='flake8_exclude_comma_separated',
        ),
        pytest.param(
            '[project_structure]\nforbidden_imports = django.db\n',
            'project_structure',
            'forbidden_imports',
            'django.db',
            id='project_structure_scalar',
        ),
    ],
)
def test__get_param_from_config__parses_setup_cfg_sections(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    setup_cfg_content: str,
    section_name: str,
    param_name: str,
    expected_value: str,
) -> None:
    """Arrange: setup.cfg with a section parameter. Act: read via configparser. Assert: value matches."""
    monkeypatch.chdir(tmp_path)
    setup_cfg_path = tmp_path / 'setup.cfg'
    setup_cfg_path.write_text(setup_cfg_content, encoding='utf-8')

    assert get_param_from_config(str(setup_cfg_path), section_name, param_name) == expected_value


def test__get_list_param_from_config__parses_multiline_setup_cfg(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arrange: multiline list in setup.cfg. Act: read list param. Assert: all lines returned."""
    monkeypatch.chdir(tmp_path)
    setup_cfg_path = tmp_path / 'setup.cfg'
    setup_cfg_path.write_text(
        '[flake8]\n' 'per-path-max-complexity =\n' '    legacy.py: 12\n' '    other.py: 9\n',
        encoding='utf-8',
    )

    assert get_list_param_from_config(str(setup_cfg_path), 'flake8', 'per-path-max-complexity') == [
        'legacy.py: 12',
        'other.py: 9',
    ]


@pytest.mark.parametrize(
    'pyproject_content, section_name, param_name, expected_value',
    [
        pytest.param(
            '[tool.flake8]\nadjustable-default-max-complexity = 10\n',
            'flake8',
            'adjustable-default-max-complexity',
            '10',
            id='flake8_int_scalar',
        ),
        pytest.param(
            '[tool.flake8]\nexclude = ["venv", "migrations"]\n',
            'flake8',
            'exclude',
            'venv,migrations',
            id='flake8_exclude_list',
        ),
        pytest.param(
            '[tool.project_structure]\nforbidden_imports = ["pkg.a", "pkg.b"]\n',
            'project_structure',
            'forbidden_imports',
            'pkg.a,pkg.b',
            id='forbidden_imports_list_as_scalar_join',
        ),
    ],
)
def test__get_param_from_configs__parses_pyproject_toml(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    pyproject_content: str,
    section_name: str,
    param_name: str,
    expected_value: str,
) -> None:
    """Arrange: pyproject.toml with tool section. Act: read param. Assert: normalized scalar value."""
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath('pyproject.toml').write_text(pyproject_content, encoding='utf-8')

    assert get_param_from_configs(section_name, param_name) == expected_value


def test__get_list_param_from_configs__parses_pyproject_toml_array(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arrange: TOML array for per-path rules. Act: read list param. Assert: array items preserved."""
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath('pyproject.toml').write_text(
        '[tool.flake8]\n' 'per-path-max-complexity = ["legacy.py: 12", "other.py: 9"]\n',
        encoding='utf-8',
    )

    assert get_list_param_from_configs('flake8', 'per-path-max-complexity') == [
        'legacy.py: 12',
        'other.py: 9',
    ]


def test__get_list_param_from_configs__parses_multiline_pyproject_string(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arrange: multiline string in pyproject. Act: read list param. Assert: lines split correctly."""
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath('pyproject.toml').write_text(
        '[tool.project_structure]\n' 'forbidden_imports = """\n' 'pkg.a\n' 'pkg.b\n' '"""\n',
        encoding='utf-8',
    )

    assert get_list_param_from_configs('project_structure', 'forbidden_imports') == [
        'pkg.a',
        'pkg.b',
    ]


def test__load_pyproject_toml__parses_nested_tool_sections(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arrange: pyproject with project and tool tables. Act: load TOML. Assert: nested mapping available."""
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath('pyproject.toml').write_text(
        '[project]\nname = "demo"\n\n[tool.flake8]\nmax-line-length = 120\n', encoding='utf-8'
    )

    loaded = _load_pyproject_toml()

    assert loaded['project']['name'] == 'demo'
    assert loaded['tool']['flake8']['max-line-length'] == 120


def test__get_param_from_configs__pyproject_precedence_over_setup_cfg(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arrange: same key in both files with different values. Act: read param. Assert: pyproject wins."""
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath('pyproject.toml').write_text(
        '[tool.flake8]\nexclude = ["from_pyproject"]\n', encoding='utf-8'
    )
    tmp_path.joinpath('setup.cfg').write_text(
        '[flake8]\nexclude = from_setup_cfg\n', encoding='utf-8'
    )

    assert get_param_from_configs('flake8', 'exclude') == 'from_pyproject'


def test__get_list_param_from_configs__falls_back_to_setup_cfg_multiline(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arrange: list only in setup.cfg. Act: read via unified API. Assert: setup.cfg multiline parsed."""
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath('setup.cfg').write_text(
        '[project_structure]\n' 'forbidden_imports =\n' '    pkg.a\n' '    pkg.b\n',
        encoding='utf-8',
    )

    assert get_list_param_from_configs('project_structure', 'forbidden_imports') == [
        'pkg.a',
        'pkg.b',
    ]


@pytest.mark.parametrize(
    'config_source, config_content, expected_dirs',
    [
        pytest.param(
            'setup.cfg',
            '[flake8]\nexclude = venv, migrations\n',
            ['venv', 'migrations'],
            id='exclude_from_setup_cfg',
        ),
        pytest.param(
            'pyproject.toml',
            '[tool.flake8]\nexclude = ["venv", "migrations"]\n',
            ['venv', 'migrations'],
            id='exclude_from_pyproject',
        ),
    ],
)
def test__get_exclude_dirs_from_config__parses_exclude_from_both_formats(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    config_source: str,
    config_content: str,
    expected_dirs: list[str],
) -> None:
    """Arrange: exclude in setup.cfg or pyproject. Act: read exclude dirs. Assert: comma/list normalized."""
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath(config_source).write_text(config_content, encoding='utf-8')

    assert get_exclude_dirs_from_config('flake8', 'exclude') == expected_dirs


def test__get_param_from_configs__returns_none_when_missing(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arrange: empty directory without config files. Act: read unknown param. Assert: None."""
    monkeypatch.chdir(tmp_path)

    assert get_param_from_configs('flake8', 'adjustable-default-max-complexity') is None


def test__get_list_param_from_configs__returns_empty_list_when_missing(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Arrange: setup.cfg without list param. Act: read list param. Assert: empty list."""
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath('setup.cfg').write_text('[flake8]\nmax-line-length = 120\n', encoding='utf-8')

    assert get_list_param_from_configs('flake8', 'per-path-max-complexity') == []

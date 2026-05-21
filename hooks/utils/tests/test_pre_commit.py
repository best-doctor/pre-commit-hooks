from __future__ import annotations

from hooks.utils.pre_commit import (
    get_input_files,
    get_input_test_files,
    get_modules_files,
    is_django_model_file,
)


def test__get_input_files__yields_single_py_file(tmp_path):
    py_file = tmp_path / 'module.py'
    py_file.write_text('x = 1\n', encoding='utf-8')

    result = list(get_input_files(args=[str(py_file)], dirs_to_exclude=[]))

    assert result == [str(py_file.resolve())]


def test__get_input_files__yields_py_files_from_directory(tmp_path):
    py_file = tmp_path / 'module.py'
    py_file.write_text('x = 1\n', encoding='utf-8')
    (tmp_path / 'readme.txt').write_text('text\n', encoding='utf-8')

    result = list(get_input_files(args=[str(tmp_path)], dirs_to_exclude=[]))

    assert result == [str(py_file.resolve())]


def test__get_input_test_files__filters_test_py_files(tmp_path):
    tests_directory = tmp_path / 'app' / 'tests'
    tests_directory.mkdir(parents=True)
    test_file = tests_directory / 'test_foo.py'
    test_file.write_text('pass\n', encoding='utf-8')
    (tests_directory / 'conftest.py').write_text('pass\n', encoding='utf-8')
    (tests_directory / 'helpers.py').write_text('pass\n', encoding='utf-8')

    result = list(get_input_test_files(args=[str(tmp_path / 'app')]))

    assert result == [str(test_file.resolve())]


def test_get_modules_files():
    test_entries = [
        '/orders/some/nested/file.py',
        '/orders/some/other/nested/file.py',
        '/patients/another/file.py',
        '/some/module/not/in/modules/list.py',
        '/root_level_file.py',
    ]

    result = list(get_modules_files(test_entries, base_dir='/'))

    assert result == [
        ('orders', '/orders', ['/orders/some/nested/file.py', '/orders/some/other/nested/file.py']),
        ('patients', '/patients', ['/patients/another/file.py']),
        ('some', '/some', ['/some/module/not/in/modules/list.py']),
    ]


def test_is_django_model_file():
    assert is_django_model_file('models.py')
    assert is_django_model_file('/models.py')
    assert is_django_model_file('/foo/bar/models.py')
    assert is_django_model_file('/foo/bar/models/baz.py')

    assert not is_django_model_file('baz.py')
    assert not is_django_model_file('model.py')
    assert not is_django_model_file('/foo/models/bar.html')

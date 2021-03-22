from __future__ import annotations

from hooks.utils.pre_commit import is_django_model_file, get_modules_files


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
        ('orders', '/orders', [
            '/orders/some/nested/file.py',
            '/orders/some/other/nested/file.py',
        ]),
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

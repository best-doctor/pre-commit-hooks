from __future__ import annotations

from hooks.validate_package_structure import (
    all_enums_in_enums_py_module,
    has_no_empty_py_files,
    has_no_submodules_with_blacklisted_suffixes,
    has_only_models_in_models_submodule,
    no_url_calls,
    urls_py_has_urlpatterns,
    views_py_has_only_class_views,
)


def test__has_no_submodules_with_blacklisted_suffixes__empty_module_files():
    assert has_no_submodules_with_blacklisted_suffixes(
        'module', '/project/module', []) == []


def test__has_no_submodules_with_blacklisted_suffixes__detects_all_forbidden_files():
    module_path = '/project/module'
    module_files = [
        f'{module_path}/foo_utils.py',
        f'{module_path}/nested/bar_helpers.py',
        f'{module_path}/allowed.py',
        f'{module_path}/tests/test_foo_utils.py',
    ]

    errors = has_no_submodules_with_blacklisted_suffixes(
        'module', module_path, module_files)

    assert len(errors) == 2
    assert all(
        'should be moved to utils subdirectory' in error for error in errors)
    assert f'{module_path}/foo_utils.py' in errors[0]
    assert f'{module_path}/nested/bar_helpers.py' in errors[1]


def test__has_only_models_in_models_submodule__reports_module_level_function(tmp_path):
    module_path = tmp_path / 'orders'
    module_path.mkdir()
    models_file = module_path / 'models.py'
    models_file.write_text(
        'def not_a_model_helper():\n    pass\n',
        encoding='utf-8',
    )

    errors = has_only_models_in_models_submodule(
        'orders', str(module_path), [str(models_file)])

    assert len(errors) == 1
    assert 'Wrong instruction for models' in errors[0]
    assert str(models_file) in errors[0]


def test__has_only_models_in_models_submodule__allows_django_model_only(tmp_path):
    module_path = tmp_path / 'orders'
    module_path.mkdir()
    models_file = module_path / 'models.py'
    models_file.write_text(
        'from django.db import models\n\n\n'
        'class Order(models.Model):\n'
        '    class Meta:\n'
        '        pass\n',
        encoding='utf-8',
    )

    errors = has_only_models_in_models_submodule(
        'orders', str(module_path), [str(models_file)])

    assert errors == []


def test__views_py_has_only_class_views__reports_function_view(tmp_path):
    module_path = tmp_path / 'orders'
    module_path.mkdir()
    views_file = module_path / 'views.py'
    views_file.write_text(
        'def function_view(request):\n    pass\n',
        encoding='utf-8',
    )

    errors = views_py_has_only_class_views(
        'orders', str(module_path), [str(views_file)])

    assert len(errors) == 1
    assert 'Only class views allowed in views.py' in errors[0]
    assert str(views_file) in errors[0]


def test__views_py_has_only_class_views__allows_class_based_view(tmp_path):
    module_path = tmp_path / 'orders'
    module_path.mkdir()
    views_file = module_path / 'views.py'
    views_file.write_text(
        'class OrderListView:\n'
        '    def get(self, request):\n'
        '        pass\n',
        encoding='utf-8',
    )

    errors = views_py_has_only_class_views(
        'orders', str(module_path), [str(views_file)])

    assert errors == []


def test__all_enums_in_enums_py_module__reports_enum_outside_enums_py(tmp_path):
    module_path = tmp_path / 'orders'
    module_path.mkdir()
    models_file = module_path / 'models.py'
    models_file.write_text(
        'import enum\n\n\nclass Status(enum.Enum):\n    ACTIVE = 1\n',
        encoding='utf-8',
    )

    errors = all_enums_in_enums_py_module(
        'orders', str(module_path), [str(models_file)])

    assert len(errors) == 1
    assert 'enums.py' in errors[0]
    assert str(models_file) in errors[0]


def test__all_enums_in_enums_py_module__allows_enum_in_enums_py(tmp_path):
    module_path = tmp_path / 'orders'
    module_path.mkdir()
    enums_file = module_path / 'enums.py'
    enums_file.write_text(
        'import enum\n\n\nclass Status(enum.Enum):\n    ACTIVE = 1\n',
        encoding='utf-8',
    )

    errors = all_enums_in_enums_py_module(
        'orders', str(module_path), [str(enums_file)])

    assert errors == []


def test__has_no_empty_py_files__reports_whitespace_only_file(tmp_path):
    module_path = tmp_path / 'orders'
    module_path.mkdir()
    empty_file = module_path / 'services.py'
    empty_file.write_text('   \n', encoding='utf-8')

    errors = has_no_empty_py_files(
        'orders', str(module_path), [str(empty_file)])

    assert errors == [f'{empty_file} empty files are not allowed']


def test__urls_py_has_urlpatterns__reports_missing_urlpatterns(tmp_path):
    module_path = tmp_path / 'orders'
    module_path.mkdir()
    urls_file = module_path / 'urls.py'
    urls_file.write_text('# no urlpatterns here\n', encoding='utf-8')

    errors = urls_py_has_urlpatterns(
        'orders', str(module_path), [str(urls_file)])

    assert errors == [f'{urls_file} does not contain "urlpatterns" assignment']


def test__no_url_calls__reports_deprecated_url_call(tmp_path):
    module_path = tmp_path / 'orders'
    module_path.mkdir()
    urls_file = module_path / 'urls.py'
    urls_file.write_text(
        'from django.conf.urls import url\n\nurlpatterns = [url("home")]\n',
        encoding='utf-8',
    )

    errors = no_url_calls('orders', str(module_path), [str(urls_file)])

    assert len(errors) == 1
    assert 'url() call is deprecated' in errors[0]
    assert str(urls_file) in errors[0]

from __future__ import annotations

from textwrap import dedent

from hooks.validate_django_null_true_comments import Error, validate_null_comments


def test_null_comments_valid_file() -> None:
    module = dedent('''
    class Operator(SafeDeletableModel):
        uuid = models.UUIDField(  # null_for_compatibility
            default=uuid4, unique=True, null=True
        )
        has_first_name = NullBooleanField('Есть имя')  # null_for_compatibility
        first_name = PersonNameField('Имя', null=True)  # null_by_design
        has_middle_name = models.NullBooleanField('Есть отчество')  # null_for_compatibility
        middle_name = models.CharField('Отчество')
    ''')

    assert validate_null_comments(module) == []


def test_null_comments_no_class() -> None:
    module = dedent('''
    uuid = models.UUIDField(  # null_for_compatibility
        default=uuid4, unique=True, null=True
    )
    has_first_name = NullBooleanField('Есть имя')  # null_for_compatibility
    first_name = PersonNameField('Имя', null=True)  # null_by_design
    has_middle_name = models.NullBooleanField('Есть отчество')  # null_for_compatibility
    middle_name = models.CharField('Отчество')
    ''')

    assert validate_null_comments(module) == []


def test_null_comments_has_errors() -> None:
    module = dedent('''
    class Operator(SafeDeletableModel):
        uuid = models.UUIDField(
            default=uuid4, unique=True, null=True
        )
        has_first_name = NullBooleanField('Есть имя')
        first_name = PersonNameField('Имя', null=True)
        has_middle_name = models.NullBooleanField('Есть отчество')
        middle_name = models.CharField('Отчество')
        always_null = Foo(null=True)# mull_for compuktability
    ''')

    assert validate_null_comments(module) == [
        Error(3, 4, 'uuid'),
        Error(6, 4, 'has_first_name'),
        Error(7, 4, 'first_name'),
        Error(8, 4, 'has_middle_name'),
        Error(10, 4, 'always_null'),
    ]

from __future__ import annotations

import pytest

from hooks.tests.helpers import get_class_def_node_body_from_string_definition
from hooks.validate_api_schema_annotations import (
    check_docstring,
    check_docstrings_for_api_action_handlers,
    check_docstrings_for_views_dispatch_methods,
    check_doctstrings_viewsets_dispatch_methods,
    check_help_text_attribute_in_serializer_fields,
    check_schema_tags_presence_in_views_and_viewsets,
    check_schema_wrapper_for_serializer_method_field,
    check_viewset_has_serializer_class_map,
    check_viewset_lookup_field_has_valid_value,
    is_serializer,
    is_view,
    is_viewset,
)


@pytest.fixture()
def serializers_file_path():
    return 'some_app/api/serializers/base.py'


@pytest.fixture()
def not_inspected_serializers_file_path():
    return 'some_app/api/filters.py'


@pytest.fixture()
def viewsets_file_path():
    return 'some_app/api/viewsets.py'


@pytest.fixture()
def views_file_path():
    return 'some_app/api/views.py'


@pytest.mark.parametrize(
    'definition, expected_result',
    (
        ('class Test(Serializer): pass', True),
        ('class Test(ModelSerializer): pass', True),
        ('class Test(GenericViewSet): pass', False),
        ('class Test(ModelViewSet): pass', False),
        ('class Test(ReadOnlyModelViewSet): pass', False),
        ('class Test(GenericAPIView): pass', False),
        ('class Test(RetrieveAPIView): pass', False),
        ('class Test(SerializerClassMapApiView): pass', False),
        ('class Test(ListAPIView): pass', False),
    ),
)
def test_is_serializer_success_case(definition, expected_result):
    classdef_node = get_class_def_node_body_from_string_definition(definition)

    result = is_serializer(classdef_node)

    assert result == expected_result


@pytest.mark.parametrize(
    'definition, expected_result',
    (
        ('class Test(Serializer): pass', False),
        ('class Test(ModelSerializer): pass', False),
        ('class Test(GenericViewSet): pass', True),
        ('class Test(ModelViewSet): pass', True),
        ('class Test(ReadOnlyModelViewSet): pass', True),
        ('class Test(GenericAPIView): pass', False),
        ('class Test(RetrieveAPIView): pass', False),
        ('class Test(SerializerClassMapApiView): pass', False),
        ('class Test(ListAPIView): pass', False),
    ),
)
def test_is_viewset_success_case(definition, expected_result):
    node = get_class_def_node_body_from_string_definition(definition)

    result = is_viewset(node)

    assert result == expected_result


@pytest.mark.parametrize(
    'definition, expected_result',
    (
        ('class Test(Serializer): pass', False),
        ('class Test(ModelSerializer): pass', False),
        ('class Test(GenericViewSet): pass', False),
        ('class Test(ModelViewSet): pass', False),
        ('class Test(ReadOnlyModelViewSet): pass', False),
        ('class Test(GenericAPIView): pass', True),
        ('class Test(RetrieveAPIView): pass', True),
        ('class Test(SerializerClassMapApiView): pass', True),
        ('class Test(ListAPIView): pass', True),
    ),
)
def test_is_view_success_case(definition, expected_result):
    node = get_class_def_node_body_from_string_definition(definition)

    result = is_view(node)

    assert result == expected_result


@pytest.mark.parametrize(
    'definition, expected_errors',
    (
        (
            """class Test:
                \"\"\"Has docstring.\"\"\"
            """, [],
        ),
        ('class Test: pass', [':1 Test missed docstring']),
    ),
)
def test_check_docstring_success_case(definition, expected_errors):
    node = get_class_def_node_body_from_string_definition(definition)

    errors = check_docstring(node)

    assert errors == expected_errors


@pytest.mark.parametrize(
    ('definition', 'file_path_fixture', 'expected_errors'), [
        (
            'class Test(ModelSerializer): pass',
            'serializers_file_path',
            [],
        ),
        (
            (
                """class Test(GenericViewSet):
                    schema_tags = ['test']
                """
            ),
            'viewsets_file_path',
            [],
        ),
        (
            (
                """class Test(GenericViewSet):
                    some_field = 'some_value'
                    schema_tags: list[str] = ['test']
                """
            ),
            'viewsets_file_path',
            [],
        ),
        (
            (
                """class Test(GenericViewSet):
                    schema_tags: list[str] = ['test']
                """
            ),
            'viewsets_file_path',
            [],
        ),
        (
            (
                """class Test(GenericViewSet):
                    some_field: str = 'some_value'
                    schema_tags = ['test']
                """
            ),
            'viewsets_file_path',
            [],
        ),
        (
            (
                """class Test(GenericViewSet):
                    some_field: str = 'some_value'
                    schema_tags: list[str] = ['test']
                """
            ),
            'viewsets_file_path',
            [],
        ),
        (
            (
                """class Test(GenericViewSet):
                    some_field: str = 'some_value'
                    schema_tags: list[str]
                """
            ),
            'viewsets_file_path',
            [],
        ),
        (
            (
                """class Test(GenericViewSet):
                    pass
                """
            ),
            'viewsets_file_path',
            ['Test missed schema tags attribute'],
        ),
    ],
)
def test_check_schema_tag_presence(request, definition, file_path_fixture, expected_errors):
    file_path = request.getfixturevalue(file_path_fixture)
    node = get_class_def_node_body_from_string_definition(definition)

    errors = check_schema_tags_presence_in_views_and_viewsets(node, file_path)

    assert errors == expected_errors


@pytest.mark.parametrize(
    ('definition', 'file_path_fixture', 'expected_errors'), [
        (
            (
                """class TestSerializer(ModelSerializer):
                    some_field = SchemaWrapper(
                        SerializerMethodField(help_text='Test help text', some_another_attr='Another help text'),
                        schema_type=BooleanField,
                    )
                """
            ),
            'serializers_file_path',
            [],
        ),
        (
            (
                """class TestSerializer(ModelSerializer):
                    some_field = SerializerMethodField(
                        help_text='Test help text', some_another_attr='Another help text',
                    )
                """
            ),
            'serializers_file_path',
            [],
        ),
        (
            'class Test(GenericViewSet): pass',
            'serializers_file_path',
            [],
        ),
        (
            (
                """class TestSerializer(ModelSerializer):
                    some_field = SerializerMethodField(
                        some_another_attr='Another help text',
                    )
                    another_field = SerializerMethodField(
                        some_another_attr='Another help text',
                    )
                """
            ),
            'serializers_file_path',
            [':2 missing `help_text` attribute', ':5 missing `help_text` attribute'],
        ),
        (
            (
                """class TestSerializer(ModelSerializer):
                    another_field = None
                    some_field = SchemaWrapper(
                        SerializerMethodField(some_another_attr='Another help text'),
                        schema_type=BooleanField,
                    )
                """
            ),
            'serializers_file_path',
            [':4 missing `help_text` attribute'],
        ),
        (
            (
                """class TestSerializer(Serializer):
                    another_field = None
                    some_field = SchemaWrapper(
                        SerializerMethodField(some_another_attr='Another help text'),
                        schema_type=BooleanField,
                    )
                """
            ),
            'serializers_file_path',
            [':4 missing `help_text` attribute'],
        ),
        (
            (
                """class TestSerializer(ModelSerializer):
                    another_field = None
                    some_field = SchemaWrapper(
                        SerializerMethodField(some_another_attr='Another help text'),
                        schema_type=BooleanField,
                    )
                """
            ),
            'not_inspected_serializers_file_path',
            [],
        ),
    ],
)
def test_help_text_attribute_in_serializer_fields(
    request, definition, file_path_fixture, expected_errors,
):
    file_path = request.getfixturevalue(file_path_fixture)
    node = get_class_def_node_body_from_string_definition(definition)

    errors = check_help_text_attribute_in_serializer_fields(node, file_path)

    assert errors == expected_errors


@pytest.mark.parametrize('definition, expected_errors', (
    (
        """class Test(GenericViewSet):
            pass
        """, [':1 Test missed `serializer_class_map` attribute'],
    ),
    (
        """class Test(GenericViewSet):
            some_field = 'some_value'
        """, [':1 Test missed `serializer_class_map` attribute'],
    ),
    (
        """class Test(GenericViewSet):
            some_field = 'some_value'
            serializer_class_map = ...
        """, [],
    ),
    (
        """class Test(GenericViewSet):
            some_field = 'some_value'
            serializer_class_map: SerializerClassMap = ...
        """, [],
    ),
    (
        """class Test(GenericViewSet):
            some_field: str = 'some_value'
            serializer_class_map: SerializerClassMap = ...
        """, [],
    ),
    (
        """class Test(GenericViewSet):
            some_field: str = 'some_value'
            serializer_class_map = ...
        """, [],
    ),
    (
        """class Test(GenericViewSet):
            some_field: str
            serializer_class_map: SerializerClassMap
        """, [],
    ),
    (
        """class Test(ListAPIView):
            pass
        """, [],
    ),
))
def test_check_viewset_has_serializer_class_map(definition, expected_errors):
    node = get_class_def_node_body_from_string_definition(definition)

    errors = check_viewset_has_serializer_class_map(node)

    assert errors == expected_errors


@pytest.mark.parametrize('definition, expected_errors', (
    (
        """class Test(GenericViewSet):
            another_field = 'another_value'
            lookup_field = 'uuid'
        """, [],
    ),
    (
        """class Test(GenericViewSet):
            another_field = 'another_value'
            lookup_field = 'id'
        """, [":1 Test viewset has forbidden `lookup_field`. Choose from: ['uuid']"],
    ),
))
def test_check_viewset_lookup_field_has_valid_value(definition, expected_errors):
    node = get_class_def_node_body_from_string_definition(definition)

    errors = check_viewset_lookup_field_has_valid_value(node)

    assert errors == expected_errors


@pytest.mark.parametrize(
    ('definition', 'file_path_fixture', 'expected_errors'), [
        (
            """class Test(ModelSerializer):
                visit = SerializerMethodField()
                patient = SerializerMethodField()
                urls = SerializerMethodField()

                def get_urls(self) -> typing.List:
                    pass

                def get_visit(self) -> Visit:
                    pass

                def get_patient(self) -> Patient:
                    pass
            """,
            'serializers_file_path',
            [
                ':2 Test serializer visit field missing SchemaWrapper',
                ':3 Test serializer patient field missing SchemaWrapper',
                ':4 Test serializer urls field missing SchemaWrapper',
            ],
        ),
        (
            """class Test(ModelViewSet):
                pass
            """,
            'serializers_file_path',
            [],
        ),
        (
            """class Test(ModelSerializer):
                visit = SerializerMethodField()
                patient = SerializerMethodField()

                def get_visit(self) -> str:
                    pass

                def get_patient(self) -> Optional[str]:
                    pass
            """,
            'serializers_file_path',
            [],
        ),
        (
            """class Test(ModelSerializer):
                visit = SchemaWrapper(SerializerMethodField(), schema_type=...)

                def get_visit(self) -> Visit:
                    pass
            """,
            'serializers_file_path',
            [],
        ),
        (
            """class Test(ModelSerializer):
                visit = SchemaWrapper(SerializerMethodField(), schema_type)

                def get_visit(self) -> str:
                    pass
            """,
            'serializers_file_path',
            [],
        ),
        (
            """class Test(ModelSerializer):
                class Meta:
                    fields = ['visit']
                visit = SchemaWrapper(SerializerMethodField(), schema_type)

                def get_visit(self) -> str:
                    pass
            """,
            'serializers_file_path',
            [],
        ),
        (
            """class Test(ModelSerializer):
                visit = SerializerMethodField()
                patient = SerializerMethodField()
                urls = SerializerMethodField()

                def get_urls(self) -> typing.List:
                    pass

                def get_visit(self) -> Visit:
                    pass

                def get_patient(self) -> Patient:
                    pass
            """,
            'not_inspected_serializers_file_path',
            [],
        ),
        (
            """class Test(Serializer):
                visit = SerializerMethodField()
                patient = SerializerMethodField()
                urls = SerializerMethodField()

                def get_urls(self) -> typing.List:
                    pass

                def get_visit(self) -> Visit:
                    pass

                def get_patient(self) -> Patient:
                    pass
            """,
            'serializers_file_path',
            [
                ':2 Test serializer visit field missing SchemaWrapper',
                ':3 Test serializer patient field missing SchemaWrapper',
                ':4 Test serializer urls field missing SchemaWrapper',
            ],
        ),
    ],
)
def test_check_schema_wrapper_for_serializer_method_field(
    request, definition, file_path_fixture, expected_errors,
):
    file_path = request.getfixturevalue(file_path_fixture)
    node = get_class_def_node_body_from_string_definition(definition)

    errors = check_schema_wrapper_for_serializer_method_field(node, file_path)

    assert errors == expected_errors


@pytest.mark.parametrize('definition, expected_errors', [
    (
        """class TestViewset(ModelViewSet):
            @action
            def test_action(self):
                pass
        """, [':3 test_action missed docstring'],
    ),
    (
        """class TestViewset(ModelViewSet):
            @action
            def test_action(self):
                \"\"\"Has docstring.\"\"\"
                pass
        """, [],
    ),
    (
        """class TestViewset(ModelViewSet):
            @drf_action
            def test_action(self):
                pass
        """, [':3 test_action missed docstring'],
    ),
    (
        """class TestViewset(ModelViewSet):
            @drf_action
            def test_action(self):
                \"\"\"Has docstring.\"\"\"
                pass
        """, [],
    ),
])
def test_check_docstrings_for_api_action_handlers(definition, expected_errors):
    node = get_class_def_node_body_from_string_definition(definition)

    errors = check_docstrings_for_api_action_handlers(node)

    assert errors == expected_errors


@pytest.mark.parametrize('definition, expected_errors', [
    (
        """class TestView(GenericAPIView):
            def get(self) -> None:
                pass

            def patch(self) -> None:
                pass
        """, [':2 get missed docstring', ':5 patch missed docstring'],
    ),
    (
        """class TestView(GenericAPIView):
            def post(self) -> None:
                \"\"\"Has docstring.\"\"\"
                pass

            def put(self) -> None:
                \"\"\"Has docstring.\"\"\"
                pass
        """, [],
    ),
    (
        """class TestViewset(ModelViewSet):
            def get(self):
                pass
        """, [],
    ),
])
def test_check_docstrings_for_views_dispatch_methods(definition, expected_errors):
    node = get_class_def_node_body_from_string_definition(definition)

    errors = check_docstrings_for_views_dispatch_methods(node)

    assert errors == expected_errors


@pytest.mark.parametrize('definition, expected_errors', [
    (
        """class TestViewset(ModelViewSet):
            def list(self) -> None:
                pass

            def retrieve(self) -> None:
                pass
        """, [':2 list missed docstring', ':5 retrieve missed docstring'],
    ),
    (
        """class TestViewset(ModelViewSet):
            def create(self) -> None:
                \"\"\"Has docstring.\"\"\"
                pass

            def partial_update(self) -> None:
                \"\"\"Has docstring.\"\"\"
                pass
        """, [],
    ),
    (
        """class TestView(GenericAPIView):
            def get(self):
                pass
        """, [],
    ),
])
def test_check_doctstrings_viewsets_dispatch_methods(definition, expected_errors):
    node = get_class_def_node_body_from_string_definition(definition)

    errors = check_doctstrings_viewsets_dispatch_methods(node)

    assert errors == expected_errors

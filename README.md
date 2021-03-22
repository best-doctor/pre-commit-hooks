# Pre Commit Hooks

Этот репозиторий содержит pre-commit хуки общего назначения которые используются в BestDoctor для Python-проектов.

## Как использовать

Чтобы подключить хуки, необходимо в корневой каталог репозитория положить файл `.pre-commit-config.yaml` следующего
содержания:

```yaml
repos:
  - repo: https://github.com/best-doctor/pre-commit-hooks
    rev: v1.0.0
    hooks:
      - id: no-asserts
```

и в секции `hooks` перечислить хуки уоторые требуется включить.

## Конфигурация

Все хуки используют параметр `setup.cfg -> [flake8] -> exclude` - для определения списка директорий исключаемых из
проверки. Если есть необходимость выключить какие-то файлы/директории дополнительно, можно использовать параметр хука
`exclude` в `.pre-commit-config.yaml` чтобы задать регулярное выражение - все попадающие под него пути будут невидимы
для данного хука.

## Доступные хуки

### `validate_ajustable_complexity`

Аналог [flake8-adjustable-complexity](https://github.com/best-doctor/flake8-adjustable-complexity), находит и ругается
на сложные функции (cyclomatic complexity > 8) с переменными со слишком общими именами.

Параметры:

- `setup.cfg -> [flake8] -> adjustable-default-max-complexity` - значение сложности функции при котором срабатывает валидатор
- `setup.cfg -> [flake8] -> per-path-max-complexity` - список 'имя_файла: сложность' для того чтобы перекрыть значение
  сложности на уровне конкретного файла

### `validate_amount_of_py_file_lines`

Проверяет количство строк в Python-файлах - по умолчанию срабатывает когда в файле больше 1000 строк.

Параметры:

- `--lines n` - максисальное количество строк (по умолчанию - 1000)

### `validate_api_schema_annotations`

Проверяет правильности аннотаций для генерации схемы:

- параметр schema_tags для вьюх и вьюсетов (check_schema_tags_presence_in_views_and_viewsets)
- есть докстринги у View/ViewSet и Serializer (check_docstring)
- help_text для атрибутов сериализаторов (check_help_text_attribute_in_serializer_fields)
- у ViewSet определен serializer_class_map (check_viewset_has_serializer_class_map)
- у ViewSet lookup_field != ‘id’ (check_viewset_lookup_field_has_valid_value)
- SerializerMethodField должны быть обернуты в SchemaWrapper (если функция возвращает не str)
- docstring-и для action-методов вьюх и вьюсетов (get/put/post/patch/delete, кастомные action)

### `validate_django_null_true_comments`

Проверяет что все nullable-поля в Django моделях помечены как `# null_by_design` или `#null_for_compatibility`

### `validate_django_model_field_names`

Проверяет соответствие именования полей Django-моделей гайдлайнам

### `validate_expressions_complexity`

Проверяет "сложность" блоков кода (функции, классы, циклы, блоки условных операторов) на превышение порогового значения
(9, не конфигурируется)

### `validate_graphql_model_fields_definition`

Проверяет что GraphQL-типы из `graphene-django` содержат метаданные с перечислением полей которые доступны в GraphQL
запросах - необходимо чтобы случайно не выставить наружу данные которые должны быть скрыты от пользователей.

### `validate_no_asserts`

Проверяет что Python-файлы не содержат инструкции `assert`

### `validate_no_forbidden_imports`

Проверяет что Python-файлы не содержат импортов запрещенных модулей

Параметры:

- `setup.cfg -> [project_structure] -> forbidden_imports` - список модулей которые запрещено импортировать

### `validate_old_style_annotations`

Проверяет что аннотации типов не содержат строковых литералов

### `validate_package_structure`

Валидатор структуры модуля.

Вот что он проверяет:

- в models.py только модели
- Все Enum в enums.py
- Нет файлов с суффиксом \_utils/\_helpers (им место в в utils)
- нет пустых файлов кроме инитов
- во views.py только классовые вьюхи
- в urls.py есть urlpatterns и в нём path, а не url

### `validate_settings_variables`

Проверяет что в `settings` нет переменных, которые нельзя переопределить через переменные окружения. Требует к каждой
строчке конфигов использования getenv или Value() или аналога, либо одного из комментариев
`# noqa: allowed straight assignment` или `# noqa: static object`.

### `validate_test_namings`

Проверяет что все тестовые функции начинаются с `test_` или `_`

### `check-gitleaks`

Проверяет что в код не попадут незашифрованные пароли, токены и ключи.
Данный хук требует установленную утилиту [gitleaks](https://github.com/zricethezav/gitleaks). Для этого достаточно скачать [бинарник](https://github.com/zricethezav/gitleaks/releases) и положить его в каталог, который прописан в `$PATH`. Например для linux:

```shell script
wget https://github.com/zricethezav/gitleaks/releases/download/v7.3.0/gitleaks-linux-amd64
sudo mv gitleaks-linux-amd64 /usr/local/bin/gitleaks
chmod +x /usr/local/bin/gitleaks
```

Для `MacOSX` можно установить также с помощью [homebrew](https://brew.sh):
```shell script
brew install gitleaks
```

## Разработка

Этот репозиторий использует [`pip-tools`](https://github.com/jazzband/pip-tools) для работы с пакетами поэтому перед
установкой зависимостей проекта нужно установить `pip-tools`:

```shell script
pip install pip-tools
```

Зависимости разбиты на packages (`requirements.txt`) и packages-dev (`requirements_dev.txt`) Перечни пакетов с указанием
версий находятся в файлах `requirements.in` и `requirements_dev.in` и залочены в файлах `requirements.txt` и
`requirements_dev.txt` соответственно, установка зависимостей делается командой:

```shell script
make install
```

Для установки нового пакета нужно добавить новую зависимость в файл `requirements.in` или `requirements_dev.in` и
выполнить:

```shell script
make lock
```

`make lock` генерирует `requirements.txt` и `requirements_dev.txt`, которые используются для установки зависимостей при
билде. Их нужно закоммитить вместе с `requirements.in`.

# Pre Commit Hooks

This repo contains BestDoctor's pre-commit hooks for python projects.

[pre-commit documentation](https://pre-commit.com/)

## How do I use it?

Create a `.pre-commit-config.yaml` in your repo and put this inside:

```yaml
repos:
  - repo: https://github.com/best-doctor/pre-commit-hooks
    rev: v1.0.0
    hooks:
      - id: no-asserts
```

List the hooks you'd like to enable under the `hooks:` section.

## How do I configure it?

All hooks obey flake8's exclude parameter in setup.cfg: `setup.cfg -> [flake8] -> exclude`.
Any path listed there will not be checked.

Per-hook excludes can be configured with regular expression(s) in
`exclude` parameter of a hook configuration in `.pre-commit-config.yaml`

## Available hooks

### `validate_ajustable_complexity`

Analogous to [flake8-adjustable-complexity](https://github.com/best-doctor/flake8-adjustable-complexity),
this validator complains about:
* functions with high (>8) cyclomatic complexity
* variables with too "generic" names (like `items`, `foo`, `vals`, `vars` etc.).

Configuration options:

- `setup.cfg -> [flake8] -> adjustable-default-max-complexity` - maximum allowed cyclomatic complexity
- `setup.cfg -> [flake8] -> per-path-max-complexity` - a list of 'file_name: complexity',
  each item containing max complexity override for a file.

### `validate_amount_of_py_file_lines`

Ensures a file does not contain more than `--lines n` lines (default: 1000).

### `validate_api_schema_annotations`

Validates API schema annotations:

- View/ViewSet defines `schema_tags` parameter (check_schema_tags_presence_in_views_and_viewsets)
- View/ViewSet/Serializer has a docstring (check_docstring)
- Serializer's attributes have `help_text` parameter (check_help_text_attribute_in_serializer_fields)
- ViewSet defines `serializer_class_map` (check_viewset_has_serializer_class_map)
- ViewSet's `lookup_field` != `id` (check_viewset_lookup_field_has_valid_value)
- `SerializerMethodField` is wrapped into `SchemaWrapper` (unless method's return type is `str`)
- View's/ViewSet's actions have docstrings (get/put/post/patch/delete, custom `action`s)

### `validate_django_null_true_comments`

All nullable fields in django models have to be commented with `# null_by_design` and/or `# null_for_compatibility`

### `validate_django_deprecated_model_field_comments`

All deprecated fields in django models have to be commented with `# deprecated <ticket_id> <deprecation_date>`

Configuration options:

- `--deprecation-comment-marker-regex` - A regex to match deprecation comment. Indicates thad field was deprecated (without checking whether the deprecation comment is valid or not). Defaults to `deprecated`
- `--valid-deprecation-comment-regex` - A regex to validate deprecation comment. Defaults to `#? deprecated (?P<ticket_id>[A-Z][A-Z,0-9]+-[0-9]+) (?P<deprecation_date>\d{2}\.\d{2}\.\d{4})`

<details>
  <summary>Example</summary>

  In `.pre-commit-config.yaml`
  ```yaml
  repos:
    - repo: https://github.com/best-doctor/pre-commit-hooks
      rev: v1.0.0
      hooks:
        - id: validate_deprecated_model_field_comments
          args: [--deprecation-comment-marker-regex=deprecated, --valid-deprecation-comment-regex="#? deprecated (?P<ticket_id>[A-Z][A-Z,0-9]+-[0-9]+)"]
  ```
</details>

### `validate_django_model_field_names`

Validates django models' field names against BestDoctor guidelines.

### `validate_expressions_complexity`

Ensures code block's (function, class, loop, if-expr) complexity <= 9 (unconfigurable)

### `validate_graphql_model_fields_definition`

Forces GraphQL types (`graphene-django`) to explicitly define accessible fields in `class Meta`.
Just to make sure you won't expose data you'd better not to.

### `validate_no_asserts`

Prohibits `assert` statements in python files (ignores tests, of course).

### `validate_no_forbidden_imports`

Forbids blacklisted imports

Configuration:

- `setup.cfg -> [project_structure] -> forbidden_imports` - a list of blacklisted modules' names

### `validate_old_style_annotations`

Makes sure type annotations are not string literals

### `validate_package_structure`

module structure validator. Checks if:

- `models.py` contains only model definitions
- all `Enum`s are defined in `enums.py`
- File's name doesn't end with `_utils`/`_helpers` postfix (place 'em in `utils/`)
- There are no empty files (`__init__.py` excluded)
- There are only class-based views in `views.py`
- `urls.py` contains `urlpatterns` and `urlpatterns` contain `path`s, not `url`s

### `validate_settings_variables`

Requires all settings from `DJANGO_SETTINGS` module to be configurable with environment variables.
Checks that each setting contains an `ast.Call` (assuming it's `getenv()`, `values.Value()`, etc.) or
is commented with `# noqa: allowed straight assignment` / `# noqa: static object`.

### `validate_test_namings`

Forces all tests names to start with either `test_` or `_`.

### `check-gitleaks`

Makes sure a password/token/apikey accidentally left in one of your tracked files won't make its way into outer world.
Requires [gitleaks](https://github.com/zricethezav/gitleaks) to run.
Installation is as easy as downloading [a binary](https://github.com/zricethezav/gitleaks/releases)
and dropping it somewhere in your `$PATH`.

Linux:
```shell script
wget https://github.com/zricethezav/gitleaks/releases/download/v7.3.0/gitleaks-linux-amd64
sudo mv gitleaks-linux-amd64 /usr/local/bin/gitleaks
chmod +x /usr/local/bin/gitleaks
```

[homebrew](https://brew.sh) does the job if you're on `MacOS`:
```shell script
brew install gitleaks
```

## Setting up development environment

This repo relies on [`pip-tools`](https://github.com/jazzband/pip-tools) as a package manager:

```shell script
pip install pip-tools
```

Project dependencies are **locked** in two files:
`requirements.txt` (mandatory) and `requirements_dev.txt` (development only).

These are used to install dependencies when building or setting up a project.

```shell script
make install
```
will handle this for you.

### Local development & testing

#### Managing project dependencies:
1. Edit `requirements.in` / `requirements_dev.in` as per your needs.

2. Lock dependencies.
   ```shell script
   # this generates 'requirements.txt' and 'requirements_dev.txt'
   make lock
   ```

3. Stage & commit all `requirements*` files.

#### Creating a hook:

Copy an existing hook, rename it and make it do something useful.
Next, register it in `.pre-commit-hooks.yaml`:
```yaml
- id: panzerfaust
  name: Fausts panzers
  entry: panzerfaustize  # that's the name you define in setup.cfg (see below)
  language: python
```

In `setup.cfg` too:
```сfg
[options.entry_points]
console_scripts =
    ; references hooks/panzerfaustize.py
    panzerfaustize = hooks.panzerfaustize:main
```

#### Running hooks from local repo:

Ensure your hook is **tracked**, or `try-repo` won't load it:
```shell script
git add hooks/panzerfaustize.py
```

```shell script
# execute this in a repo were you want your pre-commit hooks ran
pre-commit try-repo ../my-pre-commit-hooks/ panzerfaust\
  --files ./src/killroy.py ./src/was.py ./src/here.py
```

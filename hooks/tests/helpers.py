from __future__ import annotations

import ast


def get_class_def_node_body_from_string_definition(string_class_definition: str) -> ast.stmt:
    return ast.parse(string_class_definition).body[0]

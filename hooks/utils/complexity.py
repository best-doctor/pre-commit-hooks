from __future__ import annotations

import ast

import mccabe


def get_node_mccabe_complexity(ast_node: ast.AST) -> int:
    visitor = mccabe.PathGraphingAstVisitor()
    visitor.preorder(ast_node, visitor)
    return list(visitor.graphs.values())[0].complexity()

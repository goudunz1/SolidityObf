import logging
import random
from collections import deque
from solcast.nodes import NodeBase
from solidity import *
from opaqueConstants import random_name, random_number

logger = logging.getLogger(__name__)


OPAQUE_FALSE = (
    lambda x_name, x, y_name, y: ast_ne(  # (x-y)^2 != x^2 - 2xy + y^2
        ast_mul(  # (x-y)*(x-y)
            ast_sub(ast_id(x_name), ast_id(y_name)),  # x-y
            ast_sub(ast_id(x_name), ast_id(y_name)),  # x-y
        ),
        ast_add(  # x*x - 2*x*y + y*y
            ast_sub(  # x*x - 2*x*y
                ast_mul(ast_id(x_name), ast_id(x_name)),  # x*x
                ast_mul(ast_mul(ast_num(2), ast_id(x_name)), ast_id(y_name)),  # 2*x*y
            ),
            ast_mul(ast_id(y_name), ast_id(y_name)),  # y*y
        ),
    ),
    lambda x_name, x, y_name, y: ast_land(  # (x % 2 == 0) && (x % 2 == 1)
        ast_eq(ast_mod(ast_id(x_name), ast_num(2)), ast_num(0)),
        ast_eq(ast_mod(ast_id(x_name), ast_num(2)), ast_num(1)),
    ),
    lambda x_name, x, y_name, y: ast_land(  # (x >= y) && (x < y)
        ast_ge(ast_id(x_name), ast_id(y_name)),
        ast_lt(ast_id(x_name), ast_id(y_name)),
    ),
    # Feel free to add more!
)


def obfuscate(node: NodeBase) -> NodeBase:
    logger.debug(f"Inserting opaque predicates on {node}")

    # traverse the ast to insert opaque predicates

    bfs_queue = deque([node])  # BFS deque
    count = 0
    while len(bfs_queue) > 0:

        n = bfs_queue.popleft()

        if n.nodeType in ("FunctionDefinition", "ModifierDefinition"):
            if hasattr(n, "nodes"):
                original_nodes = n.nodes
                opaque_false = random.choice(OPAQUE_FALSE)

                x, y = random_number(), random_number()
                x_name, y_name = (
                    random_name(),
                    random_name(),
                )  # TODO: label name conflict
                x_dec_stmt, y_dec_stmt = ast_var_dec_stmt(x_name, x), ast_var_dec_stmt(
                    y_name, y
                )
                opaque_ast = ast_if_stmt(
                    cond=opaque_false(x_name=x_name, x=x, y_name=y_name, y=y),
                    true_body=[],
                    false_body=[],
                )

                n.nodes = []

                opaque = as_node(parent=n, ast=opaque_ast, at="nodes", list_idx=0)
                as_node(parent=n, ast=y_dec_stmt, at="nodes", list_idx=0)
                as_node(parent=n, ast=x_dec_stmt, at="nodes", list_idx=0)

                for x in original_nodes:
                    x._parent = opaque
                    opaque._children.add(x)
                opaque.falseBody = original_nodes
                # TODO add depth of original_nodes recursively

                continue

        if n.nodeType in ("ContractDefinition", "SourceUnit"):
            for child in n._children:
                bfs_queue.append(child)

    logger.debug("Opaque predicates insertion done")

    return node

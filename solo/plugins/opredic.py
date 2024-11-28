import logging
import random
from collections import deque
from copy import copy

from ..solidity.utils import *
from ..solidity.nodes import *
from .oconst import random_name, random_number, opaque_int

logger = logging.getLogger(__name__)


OPAQUE_FALSE = (
    lambda x_name, x, y_name, y: NE(  # (x-y)^2 != x^2 - 2xy + y^2
        MUL(  # (x-y)*(x-y)
            SUB(SYM(x_name), SYM(y_name)),  # x-y
            SUB(SYM(x_name), SYM(y_name)),  # x-y
        ),
        ADD(  # x*x - 2*x*y + y*y
            SUB(  # x*x - 2*x*y
                MUL(SYM(x_name), SYM(x_name)),  # x*x
                MUL(MUL(NUM(2), SYM(x_name)), SYM(y_name)),  # 2*x*y
            ),
            MUL(SYM(y_name), SYM(y_name)),  # y*y
        ),
    ),
    lambda x_name, x, y_name, y: LAND(  # (x % 2 == 0) && (x % 2 == 1)
        EQ(MOD(SYM(x_name), NUM(2)), NUM(0)),
        EQ(MOD(SYM(x_name), NUM(2)), NUM(1)),
    ),
    lambda x_name, x, y_name, y: LAND(  # (x >= y) && (x < y)
        GE(SYM(x_name), SYM(y_name)),
        LT(SYM(x_name), SYM(y_name)),
    ),
    # Feel free to add more!
)


def garbage_code(length: int = 1) -> Block:
    # For now, just generate
    # require(random_value == random_value);
    body = []
    for _ in range(length):
        value = random_number()
        garbage_expr = FUNCALL("require", [EQ(NUM(value), NUM(value))])
        body.append(EXPRSTMT(expr=garbage_expr))
    return BLK(body)


def run(node: SourceUnit) -> SourceUnit:
    logger.debug(f"Inserting opaque predicates on {node}")

    # traverse the ast to insert opaque predicates

    bfs_queue = deque([node])  # BFS deque
    while len(bfs_queue) > 0:

        n = bfs_queue.popleft()

        if isinstance(n, (FunctionDefinition, ModifierDefinition)):
            if hasattr(n, "body"):
                x, y = random_number(), random_number()
                x_name, y_name = (
                    random_name(),
                    random_name(),
                )  # TODO: label name conflict
                x_dec_stmt = VARSTMT(x_name, x)
                y_dec_stmt = VARSTMT(y_name, y)

                body: Block = n.body
                statements = body.iterable
                # !!! must insert this before using BLK(statements)
                # why??
                # 3ms -- 300ms
                body.iterable = []

                opaque_false = random.choice(OPAQUE_FALSE)
                opaque = IF(
                    cond=opaque_false(x_name=x_name, x=x, y_name=y_name, y=y),
                    true_body=garbage_code(length=4),
                    false_body=BLK(statements),
                )

                body.iterable = [x_dec_stmt, y_dec_stmt, opaque]

        elif isinstance(n, (ContractDefinition, SourceUnit)):
            for decl in n:
                bfs_queue.append(decl)

    logger.debug("Opaque predicates insertion done")

    return node

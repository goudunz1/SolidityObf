import logging
import random
from collections import deque

from ..solidity.utils import *
from ..solidity.nodes import *
from .opaqueConstants import random_name, random_number, opaque_int

logger = logging.getLogger(__name__)


OPAQUE_FALSE = (
    lambda x_name, x, y_name, y: LAND(  # (x % 2 == 0) && (x % 2 == 1)
        EQ(MOD(SYM(x_name), NUM(2)), NUM(0)),
        EQ(MOD(SYM(x_name), NUM(2)), NUM(1)),
    ),
    lambda x_name, x, y_name, y: LAND(  # (x >= y) && (x < y)
        GE(SYM(x_name), SYM(y_name)),
        LT(SYM(x_name), SYM(y_name)),
    ),
    # Feel free to add more!
    # Note that transactions will be reverted if there's an overflow, so avoid
    # using a lot of multiplies. Bit operations are recommended!
)


def garbage_code(length: int = 1) -> Block:
    # For now, just generate
    # require(random_value == random_value);
    body = []
    for _ in range(length):
        value = random_number()
        garbage_expr = FUNCALL("require", [EQ(NUM(value), NUM(value))])
        body.append(ExpressionStatement(expression=garbage_expr))
    return BLK(body)


def run(node: SourceUnit) -> SourceUnit:
    logger.debug(f"Inserting opaque predicates on {node}")

    # traverse the ast to insert opaque predicates
    for func in node.functions:
        if hasattr(func, "body"):
            body: Block = func.body

            x, y = random_number(), random_number()
            x_name, y_name = (
                random_name(),
                random_name(),
            )  # TODO: label name conflict
            x_dec_stmt = EVAR("int", x_name, x, stmt=True)
            y_dec_stmt = EVAR("int", y_name, y, stmt=True)

            statements = body.main
            opaque_false = random.choice(OPAQUE_FALSE)
            opaque = IF(
                cond=opaque_false(x_name=x_name, x=x, y_name=y_name, y=y),
                true_body=garbage_code(length=4),
                false_body=BLK(statements),
            )

            body.main = [x_dec_stmt, y_dec_stmt, opaque]

    logger.debug("Opaque predicates insertion done")

    return node

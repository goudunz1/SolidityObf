import logging
import random

from collections import deque
from math import gcd
from gmpy2 import gcdext

from ..solidity.nodes import *
from ..solidity.utils import *

logger = logging.getLogger(__name__)

mask = lambda x: (1 << x) - 1  # 0x1111_1111_...

OPAQUE0 = (
    # xor: x^y == x&~y|~x&y
    lambda x_name, x, y_name, y: SUB(
        XOR(SYM(x_name), SYM(y_name)),
        OR(
            AND(SYM(x_name), NOT(SYM(y_name))),
            AND(NOT(SYM(x_name)), SYM(y_name)),
        ),
    ),
    # De Morgan's law: ~x|y == ~(x&~y)
    lambda x_name, x, y_name, y: SUB(
        OR(NOT(SYM(x_name)), SYM(y_name)),
        NOT(AND(SYM(x_name), NOT(SYM(y_name)))),
    ),
    # Feel free to add more!
)


def random_number(bits: int = 128) -> int:
    """
    Return a random positive number that can be represented by integer of bit
    *bits*
    """
    return random.randint(1 << (bits - 2), (1 << (bits - 1)) - 1)


def random_name(length: int = 16) -> str:
    start = random.choice(AZazdollar_)
    return start + "".join(random.sample(AZaz09dollar_, length - 1))


def opaque_int(
    m: int, x_name: str, x: int, y_name: str, y: int, bits: int = 128
) -> dict:
    """
    Generate an AST representation of opaque integer of value m with linear
    combination of x and y based on Bezout's theorem

    We assume that x and y are positive coprime integers with 127 bits
    """

    if gcd(x, y) != 1:
        raise ValueError(
            f"opaque const generation: bad x, y value {hex(x)} and {hex(y)}"
        )

    # When m is zero, generate opaque 0 based on ast_id equations
    if m == 0:
        # template of opaque0
        opaque0: callable = random.choice(OPAQUE0)
        return opaque0(x_name=x_name, x=x, y_name=y_name, y=y)

    # When m is not zero, we're trying to find two const *aa* and *bb* that
    # aa*xx - bb*yy = m or bb*yy - aa*xx = m
    # If aa*xx - bb*yy equals to -1, we use bb*yy - aa*xx
    sign = True
    _, a, b = gcdext(x, y)
    a, b = int(a), int(b)

    if a < 0 and b > 0:
        a = -a  # a*x - b*y = -1
        sign = not sign
    elif a > 0 and b < 0:
        b = -b  # a*x - b*y = 1
    else:
        raise ValueError(
            f"opaque const generation: bad x, y value {hex(x)} and {hex(y)}"
        )

    k = random_number(bits)
    # (m*a + k*y)*x - (m*b + k*x)*y = m*(a*x - b*y)
    aa = (m * a + k * y) & mask(bits)
    bb = (m * b + k * x) & mask(bits)

    # sign is inverted twice or not inverted, We have aa*xx - bb*yy = m
    if sign is True:
        expr = SUB(
            MUL(NUM(aa), SYM(x_name)),
            MUL(NUM(bb), SYM(y_name)),
        )
    # sign is inverted once, We have aa*xx - bb*yy = -m
    else:
        expr = SUB(
            MUL(NUM(bb), SYM(y_name)),
            MUL(NUM(aa), SYM(x_name)),
        )

    return expr


def opaque_fixed() -> dict:
    # TODO opaque fixed
    pass


def run(node: SourceUnit) -> SourceUnit:
    """
    This function implements opaque constant obfuscation while keeping extra gas
    cost as low as possible
    Parameters:
        node (NodeBase): the root node to start obfuscation
    Returns:
        out (NodeBase): the obfuscated root node
    """

    logger.debug(f"Applying opaque constant obfuscation on {node}")

    # Generate const_x with a random name at beginning of the contract
    x, y = random_number(), random_number()
    while gcd(x, y) != 1:
        y = random_number()
    x_name, y_name = random_name(), random_name()  # TODO: label name conflict
    x_dec, y_dec = VAR(x_name, x, const=True), VAR(y_name, y, const=True)

    index = 0
    for n in node:
        if isinstance(n, PragmaDirective):
            index += 1
        else:
            break
    node.insert(index, x_dec)
    node.insert(index, y_dec)
    # TODO how to defend against compiler optimization of "constant variables"

    bfs_queue = deque([node])

    while len(bfs_queue) > 0:
        curr = bfs_queue.popleft()
        # Order of the children does not matter, so we use the dict children
        subnodes = curr.children.copy()
        for n in subnodes:

            # We're stopping at expressions that has a type identifier of
            # *t_rational*
            if (
                hasattr(n, "typeDescriptions")
                and "typeIdentifier" in n.typeDescriptions
            ):
                type_id: str = n.typeDescriptions["typeIdentifier"]
                if type_id.startswith("t_rational"):
                    # Normally, solc pre-compute values that can be determined
                    # during compilation time, i.e. the expression (1+1)*(2-3)
                    # will have type "t_rational_minus_2_by_1"
                    parts = type_id.split("_")
                    numerator = -int(parts[3]) if parts[2] == "minus" else int(parts[2])
                    denominator = int(parts[-1])

                    # integer
                    if denominator == 1:
                        value = numerator
                        # We can represent *value* using 128 bits
                        if (value >> 128) == 0:
                            expr = opaque_int(value, x_name, x, y_name, y)
                            # Note that there'll be junk values in the high
                            # 128 bits of the result
                            expr = AND(expr, NUM(mask(128)))
                        # 128 bits, but negative
                        elif (value >> 128) == -1:
                            expr = opaque_int(value, x_name, x, y_name, y)
                            # Because mask(128) << 128 can not be represented by
                            # int256, we generate the expression (-1) << 128
                            # instead
                            expr = OR(expr, LSL(NEG(NUM(1)), NUM(128)))
                        # We cannot represent *value* using 128 bits
                        else:
                            value_low = value & mask(128)
                            value_high = value >> 128
                            expr_low = opaque_int(value_low, x_name, x, y_name, y)
                            expr_low = AND(expr_low, NUM(mask(128)))
                            expr_high = opaque_int(value_high, x_name, x, y_name, y)
                            expr = OR(expr_low, LSL(expr_high, NUM(128)))

                        # Now expr holds a int that has the same bit
                        # representation as *value*

                        # TODO type conversion??
                        # TODO sub-denomination
                        expr = ETYPECONV("uint", expr)

                        replace_with(n, expr)

                    # TODO fixed
                    else:
                        pass

                    continue

            # Otherwise, add the node to bfs queue and continue the loop
            bfs_queue.append(n)

    return node

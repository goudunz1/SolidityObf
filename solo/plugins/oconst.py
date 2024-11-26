import logging
import random
from collections import deque
from math import gcd
from gmpy2 import gcdext
from solcast.nodes import NodeBase

from ..solidity.utils import *

logger = logging.getLogger(__name__)

mask = lambda x: (1 << x) - 1  # 0x1111_1111_...

OPAQUE0 = (
    # xor: x^y == x&~y|~x&y
    lambda x_name, x, y_name, y: ast_sub(
        ast_xor(ast_id(x_name), ast_id(y_name)),
        ast_or(
            ast_and(ast_id(x_name), ast_not(ast_id(y_name))),
            ast_and(ast_not(ast_id(x_name)), ast_id(y_name)),
        ),
    ),
    # De Morgan's law: ~x|y == ~(x&~y)
    lambda x_name, x, y_name, y: ast_sub(
        ast_or(ast_not(ast_id(x_name)), ast_id(y_name)),
        ast_not(ast_and(ast_id(x_name), ast_not(ast_id(y_name)))),
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
        expr = ast_sub(
            ast_mul(ast_num(aa), ast_id(x_name)),
            ast_mul(ast_num(bb), ast_id(y_name)),
        )
    # sign is inverted once, We have aa*xx - bb*yy = -m
    else:
        expr = ast_sub(
            ast_mul(ast_num(bb), ast_id(y_name)),
            ast_mul(ast_num(aa), ast_id(x_name)),
        )

    return expr


def opaque_fixed() -> dict:
    # TODO opaque fixed
    pass


def obfuscate(node: NodeBase) -> NodeBase:
    """
    This function implements opaque constant obfuscation while keeping extra gas
    cost as low as possible
    Parameters:
        node (NodeBase): the root node to start obfuscation
    Returns:
        out (NodeBase): the obfuscated root node
    """

    logger.debug(f"Applying opaque constant obfuscation on {node}")

    if node.nodeType != "SourceUnit":
        return node

    # Generate const_x with a random name at beginning of the contract
    x, y = random_number(), random_number()
    while gcd(x, y) != 1:
        y = random_number()
    x_name, y_name = random_name(), random_name()  # TODO: label name conflict
    x_dec, y_dec = ast_var_dec(x_name, x, const=True), ast_var_dec(
        y_name, y, const=True
    )
    idx = 0
    for n in node.nodes:
        if n.nodeType in ("PragmaDirective", "UsingDirective", "ImportDirective"):
            idx += 1
        else:
            break
    as_node(parent=node, ast=y_dec, at="nodes", list_idx=idx)
    as_node(parent=node, ast=x_dec, at="nodes", list_idx=idx)
    # TODO how to defend against compiler optimization of "constant variables"

    bfs_queue = deque([node])

    while len(bfs_queue) > 0:
        curr = bfs_queue.popleft()
        # Order of the children does not matter, so we use the set _children
        for n in curr._children:

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
                            expr = ast_and(expr, ast_num(mask(128)))
                        # 128 bits, but negative
                        elif (value >> 128) == -1:
                            expr = opaque_int(value, x_name, x, y_name, y)
                            # Because mask(128) << 128 can not be represented by
                            # int256, we generate the expression (-1) << 128
                            # instead
                            expr = ast_or(
                                expr, ast_lsh(ast_neg(ast_num(1)), ast_num(128))
                            )
                        # We cannot represent *value* using 128 bits
                        else:
                            value_low = value & mask(128)
                            value_high = value >> 128
                            expr_low = opaque_int(value_low, x_name, x, y_name, y)
                            expr_low = ast_and(expr_low, ast_num(mask(128)))
                            expr_high = opaque_int(value_high, x_name, x, y_name, y)
                            expr = ast_or(expr_low, ast_lsh(expr_high, ast_num(128)))

                        # Now expr holds a int that has the same bit
                        # representation as *value*

                        # TODO type conversion??
                        # TODO sub-denomination
                        expr = ast_elem_conv("uint", expr)

                        replace_node(node=n, ast=expr)

                    # TODO fixed
                    else:
                        pass

                    continue

            # Otherwise, add the node to bfs queue and continue the loop
            bfs_queue.append(n)

    return node

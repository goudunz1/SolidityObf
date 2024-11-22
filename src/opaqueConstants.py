import logging
import random
import os
from gmpy2 import gcdext
from solcast.nodes import NodeBase

from astUtils import *

logger = logging.getLogger(__name__)

uint256 = lambda x: x % (1 << 256)
uint128 = lambda x: x % (1 << 128)
uint64 = lambda x: x % (1 << 64)
uint32 = lambda x: x % (1 << 32)
uint16 = lambda x: x % (1 << 16)
uint8 = lambda x: x % (1 << 8)

OPAQUE0 = set(
    # xor: x^y == x&~y|~x&y
    lambda x_name, x, y_name, y: SOL_SUB(
        SOL_XOR(identifier(x_name), identifier(y_name)),
        SOL_OR(
            SOL_AND(identifier(x_name), SOL_NOT(identifier(y_name))),
            SOL_AND(SOL_NOT(identifier(x_name)), identifier(y_name)),
        ),
    ),
    # De Morgan's law: ~x|y == ~(x&~y)
    lambda x_name, x, y_name, y: SOL_SUB(
        SOL_OR(SOL_NOT(identifier(x_name)), identifier(y_name)),
        SOL_NOT(SOL_AND(identifier(x_name), SOL_NOT(identifier(y_name)))),
    ),
    # Feel free to add more!
)


def opaque_int(m: int, x_name: str, x: int, y_name: str, y: int) -> NodeBase:
    """
    Generate a opaque integer of value m with linear combination of x and y
    based on Bezout's theorem

    We assume that x and y are positive coprime integers with 255 bits and
    |x-y| > 1
    """

    if x < (1 << 255) or y < (1 << 255) or x == y or x == y + 1 or x == y - 1:
        raise ValueError(
            f"opaque const generation: bad x, y value {hex(x)} and {hex(y)}"
        )

    # When m is zero, generate opaque 0 based on identity equations
    if m == 0:
        # template of opaque0
        opaque0: callable = random.choice(OPAQUE0)
        return opaque0(x_name=x_name, x=x, y_name=y_name, y=y)

    # When m is not zero, we're trying to find two const *aa* and *bb* that
    # aa*xx - bb*yy = m or bb*yy - aa*xx = m
    # If aa*xx - bb*yy has a different sign with m, we use bb*yy - aa*xx
    sign = True

    if m < 0:
        m = -m  # We calculate aa and bb with positive integers
        sign = not sign

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

    k = random.randint(0, (1 << 256) - 1)
    # (m*a+k*y)*x - (m*b+k*x)*y = m*(a*x - b*y)
    aa = uint256(m * a + k * y)
    bb = uint256(m * b + k * x)

    # sign is inverted twice or not inverted, We have aa*xx - bb*yy = m
    if sign is True:
        return SOL_SUB(
            SOL_MUL(number(aa), identifier(x_name)),
            SOL_MUL(number(bb), identifier(y_name)),
        )
    # sign is inverted once, We have aa*xx - bb*yy = -m
    else:
        return SOL_SUB(
            SOL_MUL(number(bb), identifier(y_name)),
            SOL_MUL(number(aa), identifier(x_name)),
        )


def opaque_const(node: NodeBase, const_pool: dict = {}):
    # node has to be a function

    # Step 1: bfs,
    #   stopping at expressions that has a typeString of
    #   "int_const <value>" or
    #   "rational_const <value>" (TODO)

    # Step2: determine a group of random labels and assign a random value to it
    # then generate random arithmetic expression uses those labels that equals
    # to <value>
    # we have to add TupleExpressions at proper positions
    # TODO: label name conflict

    # Step3: we have to add a explicit type conversion to make it valid,
    # after that, we infect the original node with our new node.
    # special: if <value> is 0 or 1, use quick/fixed expressions like
    # (x&x)-(x|x)-(x^x)

    # Step4: generate aux const def at beginning of the function
    # i.e. int sPofS3x=0x1234abcd; int aSjkdU=0xccddeeff;
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

    const_pool = {}

    if node.nodeType != "SourceUnit":
        return node

    # do for each function
    for x in node.nodes:
        if x.nodeType == "VariableDeclaration":
            if x.constant is True and hasattr(x, "value"):
                type_string = x.value.typeDescriptions["typeString"]
                if type_string.startswith("int_const"):
                    name = x.name
                    value = type_string.split()[1]
                    const_pool[name] = value
                else:
                    # TODO: in this case, value can also be determined
                    pass
        elif x.nodeType == "ContractDefinition":
            local_const_pool = const_pool.copy()
            for y in x.nodes:
                if x.nodeType == "VariableDeclaration":
                    if x.constant is True and hasattr(x, "value"):
                        type_string = x.value.typeDescriptions["typeString"]
                        if type_string.startswith("int_const"):
                            name = x.name
                            value = type_string.split()[1]
                            local_const_pool[name] = value
                        else:
                            # TODO: in this case, value can also be determined
                            pass
                    else:
                        # TODO: what about immutable variables?
                        pass
                if (
                    x.nodeType == "FunctionDefinition"
                    or x.nodeType == "ModifierDefinition"
                ):
                    opaque_const(x, local_const_pool)
        elif x.nodeType == "FunctionDefinition":
            opaque_const(x, const_pool=const_pool)

    return node

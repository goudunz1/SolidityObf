"""
This module provides useful functions for manipulating the abstract syntax tree.

Author: Yu 'goudunz1' Sheng
"""

import json
from pathlib import Path
from functools import partial
from typing import Any

from .nodes import *


def from_standard_output_json(path):
    """
    Generates SourceUnit objects from a standard output json file.

    Arguments:
        path: path to the json file
    """

    output_json = json.load(Path(path).open())
    return from_standard_output(output_json)


def from_standard_output(output_json):
    """
    Generates SourceUnit objects from a standard output json as a dict.

    Arguments:
        output_json: dict of standard compiler output
    """

    source_nodes = [
        node_class_factory(v["ast"]) for v in output_json["sources"].values()
    ]
    return source_nodes


def from_ast(ast):
    """
    Generates a SourceUnit object from the given AST. Dependencies are not set.
    """

    return node_class_factory(ast)


def replace_with(node: NodeBase, new_node: NodeBase):
    """
    Replace node with a new node, update the parental relationship.

    Arguments:
        node(NodeBase): the original node
        new_node(NodeBase): the new node
    """

    parent = node.parent
    parent_key = parent.children[node]
    object = getattr(parent, parent_key)

    # The __setattr__ and __setitem__ calls are overridden and can automatically
    # set parental relationship, but we still have to check whether object is
    # a list
    if isinstance(object, list):
        object[object.index(node)] = new_node
    else:
        setattr(parent, parent_key, new_node)


def SYM(name: str) -> Identifier:
    """Wrapper for a name in source code, AKA. identifier."""
    return Identifier(name=name)


def NUM(value: int) -> Literal:
    """
    A number, big numbers are represented as hex values.

    Note that literal numbers are always positive.
    """
    return Literal(
        kind="number",
        hexValue=hex(value),
        value=hex(value) if value > 255 else str(value),
    )


def BLK(statements: list) -> Block:
    """Wrapper for a list of statements in source code, AKA. block."""
    return Block(statements=statements)


def PAREN(sub_expr: NodeBase) -> TupleExpression:
    """A pair parentheses."""
    return TupleExpression(components=[sub_expr], isInlineArray=False)


def TUPLE(components: list, is_arr: bool = False) -> TupleExpression:
    """A true tuple(list) with list of components."""
    return TupleExpression(components=components, isInlineArray=is_arr)


def ASSIGN(left: NodeBase, right: NodeBase) -> ExpressionStatement:
    """An assignment statement [left]=[right];"""
    assignment = Assignment(leftHandSide=left, operator="=", rightHandSide=right)
    return ExpressionStatement(expression=assignment)


def FOR(
    init_expr: NodeBase, cond: NodeBase, loop_expr: NodeBase, body: Block
) -> ForStatement:
    """A for statement."""
    return ForStatement(
        initializationExpression=init_expr,
        condition=cond,
        loopExpression=loop_expr,
        nodes=body,
    )


def IF(
    cond: NodeBase, true_body: Block, false_body: Block | None = None
) -> IfStatement:
    """An if statement with(out) false branch."""
    if false_body is not None:
        return IfStatement(
            condition=cond,
            trueBody=true_body,
            falseBody=false_body,
        )
    else:
        return IfStatement(condition=cond, trueBody=true_body)


def WHILE(cond: NodeBase, body: Block, do=False) -> DoWhileStatement | WhileStatement:
    """A (do-)while loop."""
    if do is True:
        return DoWhileStatement(condition=cond, body=body)
    else:
        return WhileStatement(condition=cond, body=body)


def FUNCALL(name: str, args: list, names: list = []) -> FunctionCall:
    """Call a function, or more precisely, generate a call instruction to a function."""
    return FunctionCall(expression=SYM(name), arguments=args, names=names)


def ETYPE(name: str) -> ElementaryTypeName:
    """Wrapper for an elementary in source code, AKA. type"""
    return ElementaryTypeName(name=name)


def ETYPECONV(name: str, expr: NodeBase) -> FunctionCall:
    """Explicit conversion of an elementary."""
    return FunctionCall(
        expression=ElementaryTypeNameExpression(typeName=ETYPE(name)),
        kind="typeConversion",
        arguments=[expr],
        names=[],
    )


def EVAR(
    etype: str,
    name: str,
    value: int | None,
    const: bool = False,
    mutability: str = "mutable",
    storage: str = "default",
    stmt: bool = False,
) -> VariableDeclaration:
    """Declaration of an elementary variable."""
    if stmt is False and value is not None:
        return VariableDeclaration(
            typeName=ETYPE(etype),
            constant=const,
            mutability=mutability,
            storageLocation=storage,
            name=name,
            value=NUM(value),
        )
    else:
        var_dec = VariableDeclaration(
            typeName=ETYPE(etype),
            constant=const,
            mutability=mutability,
            storageLocation=storage,
            name=name,
        )
        if stmt is True and value is not None:
            return VariableDeclarationStatement(
                declarations=[var_dec], initialValue=NUM(value)
            )
        elif stmt is True and value is None:
            return VariableDeclarationStatement(declarations=[var_dec])
        elif stmt is False:
            return var_dec


def ATYPE(
    base: ElementaryTypeName | ArrayTypeName | Any, length: int | None = None
) -> ArrayTypeName:
    """Wrapper for an array type in source code."""
    if length is None:
        return ArrayTypeName(baseType=base)
    else:
        return ArrayTypeName(baseType=base, length=length)


def AVAR(
    base: ElementaryTypeName | ArrayTypeName | Any,
    name: str,
    value: list | None,
    length: int | None = None,
    const: bool = False,
    mutability: str = "mutable",
    storage: str = "default",
    stmt: bool = False,
):
    """Declaration of an array variable."""
    if stmt is False and value is not None:
        return VariableDeclaration(
            typeName=ATYPE(base, length),
            constant=const,
            mutability=mutability,
            storageLocation=storage,
            name=name,
            value=TUPLE(value, is_arr=True),
        )
    else:
        var_dec = VariableDeclaration(
            typeName=ATYPE(base, length),
            constant=const,
            mutability=mutability,
            storageLocation=storage,
            name=name,
        )
        if stmt is True and value is not None:
            return VariableDeclarationStatement(
                declarations=[var_dec], initialValue=TUPLE(value, is_arr=True)
            )
        elif stmt is True and value is None:
            return VariableDeclarationStatement(declarations=[var_dec])
        elif stmt is False:
            return var_dec


PRECEDENCE = {
    "**": 3,
    "*": 4,
    "/": 4,
    "%": 4,
    "+": 5,
    "-": 5,
    "<<": 6,
    ">>": 6,
    "&": 7,
    "^": 8,
    "|": 9,
    "<": 10,
    ">": 10,
    "<=": 10,
    ">=": 10,
    "==": 11,
    "!=": 11,
    "&&": 12,
    "||": 13,
}


def BOP(operator: str, left: NodeBase, right: NodeBase) -> BinaryOperation:
    """
    A binary operation, solve priority by adding parentheses automatically.
    """
    if isinstance(left, BinaryOperation):
        curr_pred = PRECEDENCE[operator]
        left_pred = PRECEDENCE[left.operator]
        if left_pred > curr_pred:
            left = PAREN(left)

    if isinstance(right, BinaryOperation):
        curr_pred = PRECEDENCE[operator]
        right_pred = PRECEDENCE[right.operator]
        if right_pred >= curr_pred:
            right = PAREN(right)

    return BinaryOperation(
        operator=operator, leftExpression=left, rightExpression=right
    )


# P3
EXP = partial(BOP, "**")

# P4
MUL = partial(BOP, "*")
DIV = partial(BOP, "/")
MOD = partial(BOP, "%")

# P5
ADD = partial(BOP, "+")
SUB = partial(BOP, "-")

# P6
LSL = partial(BOP, "<<")
RSL = partial(BOP, ">>")

# P7
AND = partial(BOP, "&")

# P8
XOR = partial(BOP, "^")

# P9
OR = partial(BOP, "|")

# P10
LT = partial(BOP, "<")
GT = partial(BOP, ">")
LE = partial(BOP, "<=")
GE = partial(BOP, ">=")

# P11
EQ = partial(BOP, "==")
NE = partial(BOP, "!=")

# P12
LAND = partial(BOP, "&&")

# P13
LOR = partial(BOP, "||")


def UOP(operator: str, sub_expr: NodeBase) -> UnaryOperation:
    """An unary operation, solve priority by adding parentheses automatically."""
    if isinstance(sub_expr, BinaryOperation):
        sub_expr = PAREN(sub_expr)

    return UnaryOperation(operator=operator, subExpression=sub_expr)


# P2
NEG = partial(UOP, "-")
LNOT = partial(UOP, "!")
NOT = partial(UOP, "~")

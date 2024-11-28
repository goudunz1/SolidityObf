import json
from pathlib import Path
from functools import partial

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
        node_class_factory(v["ast"], None) for v in output_json["sources"].values()
    ]
    return source_nodes


def from_ast(ast):
    """
    Generates a SourceUnit object from the given AST. Dependencies are not set.
    """

    return node_class_factory(ast, None)


def replace_with(node: NodeBase, new_node: NodeBase):

    parent = node.parent
    where = parent.children[node]

    if isinstance(where, tuple):
        key, index = where
        array = getattr(parent, key)
        array[index] = new_node
    else:
        setattr(parent, where, new_node)

    if isinstance(node, NodeBase):
        node.parent = None
        parent.children.pop(node)

    if isinstance(new_node, NodeBase):
        if new_node.parent is not None:
            new_node = deepcopy(new_node)

        new_node.parent = parent
        parent.children[new_node] = where


single_node_factory = lambda **ast: node_class_factory(ast, None)


def SYM(name: str) -> Identifier:
    return single_node_factory(nodeType="Identifier", name=name)


def NUM(value: int) -> Literal:
    # Note that in lexical level number is always positive
    return single_node_factory(
        nodeType="Literal",
        kind="number",
        hexValue=hex(value),
        value=hex(value) if value > 255 else str(value),
    )


def PAREN(sub_expr: NodeBase) -> TupleExpression:
    return single_node_factory(nodeType="TupleExpression", components=[sub_expr])


def BOP(operator: str, left: NodeBase, right: NodeBase) -> BinaryOperation:
    # TODO: priorities
    # Add parentheses to left expression and right expression
    if not isinstance(left, (Literal, Identifier)):
        left = PAREN(left)
    if not isinstance(right, (Literal, Identifier)):
        right = PAREN(right)

    return single_node_factory(
        nodeType="BinaryOperation",
        operator=operator,
        leftExpression=left,
        rightExpression=right,
    )


def UOP(operator: str, sub_expr: NodeBase) -> UnaryOperation:
    # TODO: priorities
    # Add parentheses to sub-expression
    if not isinstance(sub_expr, (Literal, Identifier)):
        sub_expr = PAREN(sub_expr)

    return single_node_factory(
        nodeType="UnaryOperation", operator=operator, subExpression=sub_expr
    )


def ETYPE(name: str) -> ElementaryTypeName:
    return single_node_factory(nodeType="ElementaryTypeName", name=name)


def ETYPEXPR(name: str) -> ElementaryTypeNameExpression:
    return single_node_factory(
        nodeType="ElementaryTypeNameExpression", typeName=ETYPE(name)
    )


def ETYPECONV(type_name: str, expr: NodeBase) -> FunctionCall:
    return single_node_factory(
        nodeType="FunctionCall",
        expression=ETYPEXPR(type_name),
        arguments=[expr],
        names=[],
    )


def FUNCALL(name: str, args: list, names: list = []) -> FunctionCall:
    return single_node_factory(
        nodeType="FunctionCall",
        expression=SYM(name),
        arguments=args,
        names=names,
    )


def EXPRSTMT(expr: NodeBase) -> ExpressionStatement:
    return single_node_factory(
        nodeType="ExpressionStatement",
        expression=expr,
    )


def VAR(
    name: str, value: int | None, const: bool = False, etype: str = "int"
) -> VariableDeclaration:
    # TODO other types
    if value is not None:
        return single_node_factory(
            nodeType="VariableDeclaration",
            typeName=ETYPE(etype),
            constant=const,
            storageLocation="default",
            name=name,
            value=NUM(value),
        )
    else:
        return single_node_factory(
            nodeType="VariableDeclaration",
            typeName=ETYPE(etype),
            constant=const,
            storageLocation="default",
            name=name,
        )


def VARSTMT(name: str, value: int) -> VariableDeclarationStatement:
    return single_node_factory(
        nodeType="VariableDeclarationStatement",
        declarations=[VAR(name=name, value=None, const=False)],
        initialValue=NUM(value),
    )


def BLK(statements: list) -> Block:
    return single_node_factory(nodeType="Block", statements=statements)


def FOR(
    init_expr: NodeBase, cond: NodeBase, loop_expr: NodeBase, body: Block
) -> ForStatement:
    return single_node_factory(
        nodeType="ForStatement",
        initializationExpression=init_expr,
        condition=cond,
        loopExpression=loop_expr,
        nodes=body,
    )


def IF(
    cond: NodeBase, true_body: Block, false_body: Block | None = None
) -> IfStatement:
    if false_body is not None:
        return single_node_factory(
            nodeType="IfStatement",
            condition=cond,
            trueBody=true_body,
            falseBody=false_body,
        )
    else:
        return single_node_factory(
            nodeType="IfStatement", condition=cond, trueBody=true_body
        )


def WHILE(cond: NodeBase, body: Block, do=False):
    if do is True:
        return single_node_factory(
            nodeType="DoWhileStatement", condition=cond, nodes=body
        )
    else:
        return single_node_factory(
            nodeType="WhileStatement", condition=cond, nodes=body
        )


ADD = partial(BOP, "+")
SUB = partial(BOP, "-")
MUL = partial(BOP, "*")
AND = partial(BOP, "&")
OR = partial(BOP, "|")
XOR = partial(BOP, "^")
MOD = partial(BOP, "%")
LSL = partial(BOP, "<<")
RSL = partial(BOP, ">>")
RSA = partial(BOP, ">>>")
EQ = partial(BOP, "==")
NE = partial(BOP, "!=")
LE = partial(BOP, "<=")
GE = partial(BOP, ">=")
LT = partial(BOP, "<")
GT = partial(BOP, ">")
LAND = partial(BOP, "&&")
LOR = partial(BOP, "||")
NOT = partial(UOP, "~")
NEG = partial(UOP, "-")
LNOT = partial(UOP, "!")

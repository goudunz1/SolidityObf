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
        node_class_factory(v["ast"]) for v in output_json["sources"].values()
    ]
    return source_nodes


def from_ast(ast):
    """
    Generates a SourceUnit object from the given AST. Dependencies are not set.
    """

    return node_class_factory(ast)


def replace_with(node: NodeBase, new_node: NodeBase):
    parent = node.parent
    parent_key = parent.children[node]
    object = getattr(parent, parent_key)

    if isinstance(object, list):
        object[object.index(node)] = new_node
    else:
        setattr(parent, parent_key, new_node)


def SYM(name: str) -> Identifier:
    return Identifier(name=name)


def NUM(value: int) -> Literal:
    # Note that in lexical level number is always positive
    return Literal(
        kind="number",
        hexValue=hex(value),
        value=hex(value) if value > 255 else str(value),
    )


def PAREN(sub_expr: NodeBase) -> TupleExpression:
    return TupleExpression(components=[sub_expr])


def BOP(operator: str, left: NodeBase, right: NodeBase) -> BinaryOperation:
    # TODO: priorities
    # Add parentheses to left expression and right expression
    if not isinstance(left, (Literal, Identifier)):
        left = PAREN(left)
    if not isinstance(right, (Literal, Identifier)):
        right = PAREN(right)

    return BinaryOperation(
        operator=operator, leftExpression=left, rightExpression=right
    )


def UOP(operator: str, sub_expr: NodeBase) -> UnaryOperation:
    # TODO: priorities
    # Add parentheses to sub-expression
    if not isinstance(sub_expr, (Literal, Identifier)):
        sub_expr = PAREN(sub_expr)

    return UnaryOperation(operator=operator, subExpression=sub_expr)


def ETYPE(name: str) -> ElementaryTypeName:
    return ElementaryTypeName(name=name)


def ETYPEXPR(name: str) -> ElementaryTypeNameExpression:
    return ElementaryTypeNameExpression(typeName=ETYPE(name))


def ETYPECONV(type_name: str, expr: NodeBase) -> FunctionCall:
    return FunctionCall(expression=ETYPEXPR(type_name), arguments=[expr], names=[])


def ATYPE(etype_name: str, length: int | None = None) -> ArrayTypeName:
    if length is None:
        return ArrayTypeName(baseType=ETYPE(etype_name))
    else:
        return ArrayTypeName(baseType=ETYPE(etype_name), length=length)


def TUPLE(components: list, is_arr: bool = False) -> TupleExpression:
    return TupleExpression(components=components, isInlineArray=is_arr)


def FUNCALL(name: str, args: list, names: list = []) -> FunctionCall:
    return FunctionCall(expression=SYM(name), arguments=args, names=names)


def EXPRSTMT(expr: NodeBase) -> ExpressionStatement:
    return ExpressionStatement(expression=expr)


def VARDEC(
    name: str, value: int | None, const: bool = False, etype: str = "int"
) -> VariableDeclaration:
    # TODO other types
    if value is not None:
        return VariableDeclaration(
            typeName=ETYPE(etype),
            constant=const,
            mutability="mutable",
            storageLocation="default",
            name=name,
            value=NUM(value),
        )
    else:
        return VariableDeclaration(
            typeName=ETYPE(etype),
            constant=const,
            mutability="mutable",
            storageLocation="default",
            name=name,
        )


def ARRDEC(name: str, value: list | None, etype: str, length: int | None = None):
    if value is not None:
        return VariableDeclaration(
            typeName=ATYPE(etype, length),
            constant=False,
            mutability="mutable",
            storageLocation="default",
            name=name,
            value=TUPLE(value, is_arr=True),
        )
    else:
        return VariableDeclaration(
            typeName=ATYPE(etype, length),
            constant=False,
            mutability="mutable",
            storageLocation="default",
            name=name,
        )


def VARSTMT(name: str, value: int) -> VariableDeclarationStatement:
    return VariableDeclarationStatement(
        declarations=[VARDEC(name=name, value=None, const=False)],
        initialValue=NUM(value),
    )


def BLK(statements: list) -> Block:
    return Block(statements=statements)


def FOR(
    init_expr: NodeBase, cond: NodeBase, loop_expr: NodeBase, body: Block
) -> ForStatement:
    return ForStatement(
        initializationExpression=init_expr,
        condition=cond,
        loopExpression=loop_expr,
        nodes=body,
    )


def IF(
    cond: NodeBase, true_body: Block, false_body: Block | None = None
) -> IfStatement:
    if false_body is not None:
        return IfStatement(
            condition=cond,
            trueBody=true_body,
            falseBody=false_body,
        )
    else:
        return IfStatement(condition=cond, trueBody=true_body)


def WHILE(cond: NodeBase, body: Block, do=False) -> DoWhileStatement | WhileStatement:
    if do is True:
        return DoWhileStatement(condition=cond, body=body)
    else:
        return WhileStatement(condition=cond, body=body)


def ASSIGN(left: NodeBase, right: NodeBase) -> ExpressionStatement:
    assignment = Assignment(leftHandSide=left, operator="=", rightHandSide=right)
    return ExpressionStatement(expression=assignment)


def CONTINUE() -> Continue:
    return Continue()


def BREAK() -> Break:
    return Break()


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

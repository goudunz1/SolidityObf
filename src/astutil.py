import logging
import string

logger = logging.getLogger(__name__)

SOLIDITY_IDENTIFIER = string.ascii_letters + string.digits + "$_"


def gen_for_stmt(init_expr, cond, loop_expr):
    pass


def gen_if_stmt(cond, true_body, false_body):
    pass


def node2src(root, indent=0) -> str:

    indent_level = 0  # indent level iff. indent is on
    new_line = False  # new line flag, iff. indent is on

    tokens = []  # list of source tokens
    pre_ord_stack = []  # stack used for pre-order traverse

    aux_stack = []  # stack used to store local tokens

    def add_token(tok):
        nonlocal tokens
        if len(tokens) > 1:
            last = tokens[-1]
            if x[0] in SOLIDITY_IDENTIFIER and last[-1] in SOLIDITY_IDENTIFIER:
                tokens.append(" ")
        tokens.append(tok)

    def emit(obj):
        nonlocal aux_stack
        if type(obj) is not list and type(obj) is not tuple:
            aux_stack.append(obj)
        else:
            aux_stack.extend(obj)

    def emit_many(*obj):
        nonlocal aux_stack
        aux_stack.extend(obj)

    def emit_block(obj):
        nonlocal aux_stack
        aux_stack.append("{")
        aux_stack.append("\n")
        aux_stack.append(1)
        aux_stack.extend(obj)
        aux_stack.append(-1)
        aux_stack.append("}")
        aux_stack.append("\n")

    def end_stmt(line_break=True):
        nonlocal aux_stack
        aux_stack.append(";")
        if line_break is True:
            aux_stack.append("\n")

    def emit_tuple(obj):
        nonlocal aux_stack
        aux_stack.append("(")
        if len(obj) > 0:
            for i in range(len(obj) - 1):
                aux_stack.append(obj[i])
                aux_stack.append(",")
            aux_stack.append(obj[-1])
        aux_stack.append(")")

    def solidity(handler):

        def wrapper(node, *args, **kwargs):
            nonlocal aux_stack
            handler(node, *args, **kwargs)
            while len(aux_stack) > 0:
                item = aux_stack.pop()
                pre_ord_stack.append(item)

        wrapper.solidity = True
        return wrapper

    @solidity
    def SourceUnit(node):
        if hasattr(node, "license"):
            emit("//SPDX-License-Identifier:")
            emit(node.license)
            emit("\n")
        emit(node.nodes)

    @solidity
    def PragmaDirective(node):
        emit("pragma")
        emit(node.literals)
        end_stmt()

    @solidity
    def ContractDefinition(node):
        if node.abstract is True:
            emit("abstract")
        emit(node.contractKind)
        emit(node.name)
        emit_block(node.nodes)

    @solidity
    def VariableDeclarationStatement(node):
        if len(node.declarations) > 1:
            emit_tuple(node.declarations)
        else:
            emit(node.declarations[0])
        emit("=")
        emit(node.initialValue)
        caller = node.parent()
        if (
            caller.nodeType == "ForStatement"
            and node is caller.initializationExpression
        ):
            end_stmt(line_break=False)
        else:
            end_stmt()

    @solidity
    def VariableDeclaration(node):
        # variable type
        emit(node.typeName)
        # attributes
        if hasattr(node, "constant") and node.constant is True:
            emit("constant")
        elif hasattr(node, "indexed") and node.indexed is True:
            emit("indexed")
        elif node.visibility != "internal":
            emit(node.visibility)
        if node.storageLocation != "default":
            emit(node.storageLocation)
        # variable name
        if node.name != "":  # filter out anonymous variables
            emit(node.name)
            # initial value
            if hasattr(node, "value"):
                emit("=")
                emit(node.value)
        # close the statement for state variable declaration
        if node.parent().nodeType in ("ContractDefinition", "StructDefinition"):
            end_stmt()

    @solidity
    def FunctionDefinition(node):
        # function identifier
        if node.kind == "constructor":
            emit("constructor")
        else:
            emit_many("function", node.name)
        # parameter list
        emit(node.parameters)
        # visibility
        # Note that specify visibility for constructor is deprecated
        if node.kind != "constructor":
            emit(node.visibility)
        # state mutability
        if node.stateMutability != "nonpayable":
            emit(node.stateMutability)
        # is virtual
        if node.virtual is True:
            emit("virtual")
        # TODO: modifiers
        # return parameters
        if len(node.returnParameters.parameters) > 0:
            emit("returns")
            emit(node.returnParameters)
        # function body
        if hasattr(node, "nodes"):
            emit_block(node.nodes)
        else:
            end_stmt()

    @solidity
    def ParameterList(node):
        emit_tuple(node.parameters)

    @solidity
    def EventDefinition(node):
        emit("event")
        emit(node.name)
        emit(node.parameters)
        end_stmt()

    @solidity
    def StructDefinition(node):
        emit("struct")
        emit(node.name)
        emit_block(node.members)

    @solidity
    def ElementaryTypeNameExpression(node):
        emit(node.typeName)

    @solidity
    def ElementaryTypeName(node):
        if hasattr(node, "stateMutability") and node.stateMutability == "payable":
            if node.parent().nodeType == "ElementaryTypeNameExpression":
                # Handle address in expression differently, if its a payable
                # address, use 'payable' instead of 'address payable' as
                # specified in official documentation.
                emit("payable")
            else:
                emit_many(node.name, "payable")
        else:
            emit(node.name)

    @solidity
    def UserDefinedTypeName(node):
        emit(node.pathNode)

    @solidity
    def ArrayTypeName(node):
        emit(node.baseType)
        emit("[")
        emit("]")

    @solidity
    def IdentifierPath(node):
        emit(node.name)

    @solidity
    def Mapping(node):
        emit_many("mapping", "(", node.keyType, "=>", node.valueType, ")")

    @solidity
    def ExpressionStatement(node):
        emit(node.expression)
        caller = node.parent()
        if caller.nodeType == "ForStatement" and node is caller.loopExpression:
            return
        end_stmt()

    @solidity
    def EmitStatement(node):
        # function emit() has nothing to do with solidity's emit statement!
        emit("emit")
        emit(node.eventCall)
        end_stmt()

    @solidity
    def IfStatement(node):
        emit("if")
        emit_many("(", node.condition, ")")
        emit_block(node.trueBody)
        if hasattr(node, "falseBody"):
            emit("else")
            if isinstance(node.falseBody, list) or isinstance(node.falseBody, tuple):
                emit_block(node.falseBody)
            else:
                emit(node.falseBody)

    @solidity
    def ForStatement(node):
        emit("for")
        emit_many(
            "(",
            node.initializationExpression,
            node.condition,
            ";",
            node.loopExpression,
            ")",
        )
        emit_block(node.nodes)

    @solidity
    def WhileStatement(node):
        emit("while")
        emit_many("(", node.condition, ")")
        emit_block(node.nodes)

    @solidity
    def FunctionCall(n):
        emit(n.expression)
        emit_tuple(n.arguments)

    @solidity
    def MemberAccess(node):
        emit_many(node.expression, ".", node.memberName)

    @solidity
    def IndexAccess(node):
        emit_many(node.baseExpression, "[", node.indexExpression, "]")

    @solidity
    def UnaryOperation(node):
        emit_many(node.operator, node.subExpression)

    @solidity
    def BinaryOperation(node):
        emit_many(node.leftExpression, node.operator, node.rightExpression)

    @solidity
    def Assignment(n):
        emit_many(n.leftHandSide, n.operator, n.rightHandSide)

    @solidity
    def Literal(node):
        if node.kind == "string":
            emit(f'"{node.value}"')
        else:
            emit(node.value)
            if hasattr(node, "subdenomination"):
                emit(node.subdenomination)

    @solidity
    def Identifier(n):
        emit(n.name)

    logger.debug("Converting syntax tree to source")
    pre_ord_stack.append(root)
    while len(pre_ord_stack) > 0:
        x = pre_ord_stack.pop()
        if isinstance(x, str):
            if indent == 0:
                if x == "\n":
                    continue
                else:
                    add_token(x)
            else:  # for indented source
                if new_line is True:
                    if indent_level > 0:
                        add_token(" " * indent_level)
                    new_line = False
                add_token(x)
                if x == "\n":
                    new_line = True
        elif isinstance(x, int):
            indent_level += x * indent
            if indent_level < 0:
                indent_level = 0
        elif hasattr(x, "nodeType"):
            handler = locals().get(x.nodeType)
            if handler is not None and hasattr(handler, "solidity"):
                handler(x)
            else:
                logger.warning(f"AST node {x.nodeType} is not supported yet!")
        else:
            logger.warning(f"AST node of type {type(x)} is invalid")

    return "".join(tokens)

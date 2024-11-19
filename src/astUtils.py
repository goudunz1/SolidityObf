import logging
import string

logger = logging.getLogger(__name__)

SOLIDITY_IDENTIFIER = string.ascii_letters + string.digits + "$_"
SOLIDITY_PAIRS = {"{": "}", "(": ")", "[": "]"}


def gen_for_stmt(init_expr, cond, loop_expr):
    pass


def gen_if_stmt(cond, true_body, false_body):
    pass


def node2src(root, indent=0) -> str:

    tokens = []  # list of source tokens
    pre_ord_stack = []  # pre-order traverse stack

    aux_stack = []  # stack of local tokens

    def add_token(tok):
        nonlocal tokens
        if len(tokens) > 1:
            last = tokens[-1]
            # Insert separator (space) only when necessary
            if x[0] in SOLIDITY_IDENTIFIER and last[-1] in SOLIDITY_IDENTIFIER:
                tokens.append(" ")
        tokens.append(tok)

    def emit(obj):
        nonlocal aux_stack
        if type(obj) is not list and type(obj) is not tuple:
            aux_stack.append(obj)
        else:
            aux_stack.extend(obj)

    emit_many = lambda *obj: aux_stack.extend(obj)

    indent_level = 0  # indent level iff. indent is on
    new_line = False  # new line flag, iff. indent is on

    if indent == 0:

        def emit_block(obj, **kwargs):
            nonlocal aux_stack
            aux_stack.append("{")
            aux_stack.extend(obj)
            aux_stack.append("}")

        end_stmt = lambda **kwargs: aux_stack.append(";")

        def emit_tuple(obj, style=None, **kwargs):
            nonlocal aux_stack

            if style is not None:
                aux_stack.append(style)

            if len(obj) > 0:
                for i in range(len(obj) - 1):
                    aux_stack.append(obj[i])
                    aux_stack.append(",")
                aux_stack.append(obj[-1])

            if style is not None:
                aux_stack.append(SOLIDITY_PAIRS[style])

    else:  # for debugging

        def emit_block(obj, line_break=True):
            nonlocal aux_stack
            aux_stack.append("{")
            aux_stack.append("\n")
            aux_stack.append(1)
            aux_stack.extend(obj)
            aux_stack.append(-1)
            aux_stack.append("}")
            if line_break is True:
                aux_stack.append("\n")

        def end_stmt(line_break=True):
            nonlocal aux_stack
            aux_stack.append(";")
            if line_break is True:
                aux_stack.append("\n")

        def emit_tuple(obj, style=None, line_break=False):
            nonlocal aux_stack

            if style is not None:
                aux_stack.append(style)
                if line_break is True:
                    aux_stack.append("\n")
                    aux_stack.append(1)

            if len(obj) > 0:
                for i in range(len(obj) - 1):
                    aux_stack.append(obj[i])
                    aux_stack.append(",")
                    if line_break is True:
                        aux_stack.append("\n")
                aux_stack.append(obj[-1])
                if line_break is True:
                    aux_stack.append("\n")
                    aux_stack.append(-1)

            if style is not None:
                aux_stack.append(SOLIDITY_PAIRS[style])
                if line_break is True:
                    aux_stack.append("\n")

    def solidity(handler):

        def wrapper(node, *args, **kwargs):
            nonlocal aux_stack

            try:
                handler(node, *args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Bad node {node}! Maybe the node is missing some key attributes?",
                    exc_info=True,
                )
                return

            # Squeeze aux_stack into pre_ord_stack to maintain pre-order
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
            emit("\n")  # This is necessary and has nothing to do with indent
        emit(node.nodes)

    @solidity
    def ImportDirective(node):
        emit("import")
        emit(f'"{node.absolutePath}"')
        end_stmt()

    @solidity
    def PragmaDirective(node):
        emit("pragma")
        emit(node.literals)
        end_stmt()

    @solidity
    def ContractDefinition(node):
        if node.abstract is True:  # abstract?
            # For interface and library this's always False
            emit("abstract")
        emit(node.contractKind)  # interface, contract or library
        emit(node.name)  # contract name
        if len(node.baseContracts) > 0:  # inheritance
            emit("is")
            emit_tuple(node.baseContracts)
        emit_block(node.nodes)  # contract body

    @solidity
    def InheritanceSpecifier(node):
        emit(node.baseName)

    if indent == 0:

        @solidity
        def VariableDeclarationStatement(node):
            emit_tuple(node.declarations, "(")
            emit("=")
            emit(node.initialValue)
            end_stmt()

    else:

        @solidity
        def VariableDeclarationStatement(node):
            emit_tuple(node.declarations, "(")
            emit("=")
            emit(node.initialValue)
            caller = node.parent()
            end_stmt(
                line_break=not (
                    caller.nodeType == "ForStatement"
                    and node is caller.initializationExpression
                )
            )

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
        emit_tuple(node.parameters, "(")

    @solidity
    def EventDefinition(node):
        emit("event")
        emit(node.name)
        emit(node.parameters)
        end_stmt()

    @solidity
    def ErrorDefinition(node):
        emit("error")
        emit(node.name)
        emit(node.parameters)
        end_stmt()

    @solidity
    def EnumDefinition(node):
        emit("enum")
        emit(node.name)
        emit_tuple(node.members, style="{", line_break=True)

    @solidity
    def EnumValue(node):
        emit(node.name)

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
        # TODO: fixed length array
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
        emit_block(node.trueBody, not hasattr(node, "falseBody"))
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
    def Return(node):
        emit("return")
        emit(node.expression)
        end_stmt()

    @solidity
    def FunctionCall(n):
        emit(n.expression)
        emit_tuple(n.arguments, "(")

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

        # string literals, printable
        if node.kind == "string":
            emit(ascii(node.value))

        # string literals, non-printable
        elif node.kind == "unicodeString":
            emit_many("unicode", ascii(node.value))

        # hex string literals
        elif node.kind == "hexString":
            emit_many("hex", '"%s"' % node.hexValue)

        # number literals
        elif node.kind == "number":
            emit(node.value)
            # Note that there could be a sub-denomination, i.e. 100 wei
            if hasattr(node, "subdenomination"):
                emit(node.subdenomination)

        # bool literals and any undefined literals goes here
        else:
            emit(node.value)

    @solidity
    def Identifier(n):
        emit(n.name)

    logger.debug("Converting syntax tree to source")
    pre_ord_stack.append(root)
    while len(pre_ord_stack) > 0:
        x = pre_ord_stack.pop()
        if isinstance(x, str):
            if indent == 0:
                add_token(x)
            else:  # iff. indent is on
                if new_line is True:
                    if indent_level > 0:
                        add_token(" " * indent_level)
                    new_line = False
                add_token(x)
                if x == "\n":
                    new_line = True
        elif hasattr(x, "nodeType"):
            handler = locals().get(x.nodeType)
            if handler is not None and hasattr(handler, "solidity"):
                handler(x)
            else:
                logger.warning(f"AST node {x.nodeType} is not supported yet!")
        elif isinstance(x, int):  # iff. indent is on
            indent_level += x * indent
            if indent_level < 0:
                indent_level = 0
        else:
            logger.error(
                f"Bad node {x}! Maybe the node is missing some key attributes?"
            )

    return "".join(tokens)

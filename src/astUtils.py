import logging
import string
from typing import Union, List, Optional
logger = logging.getLogger(__name__)

GOOD_CHARS = string.ascii_letters + string.digits + "$_"


def gen_for_stmt(init_expr, cond, loop_expr):
    # TODO: reuseable for statement for obfuscate modules
    pass


def gen_if_stmt(cond, true_body, false_body):
    # TODO: reuseable if statement for obfuscate modules
    pass


def node2src(root: object, indent: int = 0) -> str:
    """
    Convert a *SourceUnit* AST node to solidity source
    Parameters:
        root (object): a *SourceUnit* AST node AKA. the root
        indent (int): If this field is set to a positive value, indent will be
            turned on, otherwise we generate compact source code
    Returns:
        the source code
    """

    tokens = []  # list of source tokens
    pre_ord_stack = []  # pre-order traverse stack

    aux_stack = []  # stack of local tokens

    def add_token(token: str):
        """
        Push a new token into string builder
        Parameters:
            token (str): the new token
        """

        nonlocal tokens

        if len(tokens) > 1:
            last = tokens[-1]
            # Insert separator (space) only when necessary
            if x[0] in GOOD_CHARS and last[-1] in GOOD_CHARS:
                tokens.append(" ")
        tokens.append(token)


    def emit(obj: Union[list, str, int, object]):
        """
        Push a new component onto local stack, used in grammar handlers
        Parameters:
            obj (object): the component to be processed
        """

        nonlocal aux_stack

        if isinstance(obj, (list, tuple)):
            aux_stack.extend(obj)
        else:
            aux_stack.append(obj)

    # auxiliary function emit_many()
    # like emit(), but for dynamic parameters
    emit_many = lambda *obj: aux_stack.extend(obj)

    # auxiliary function end_stmt()
    # end statement with a semicolon
    if indent > 0:
        end_stmt = lambda: aux_stack.append(";\n")
    else:
        end_stmt = lambda: aux_stack.append(";")

    shift = 0  # indent level iff. indent is on
    new_line = False  # new line flag, iff. indent is on

    def emit_block(obj: list, continuous: bool = False):
        """
        Push a list of components in block format
        Parameters:
            obj (list): the block body
            continuous (bool): whether to insert LF after the closing bracket,
                effective iff. indent is on
        """

        nonlocal aux_stack

        aux_stack.append("{")
        if indent > 0:  # indent mode, for debug purpose only
            aux_stack.append(1)
            aux_stack.append("\n")

        aux_stack.extend(obj)

        if indent > 0:
            aux_stack.append(-1)
            aux_stack.append("}")
            if continuous is False:
                aux_stack.append("\n")
        else:
            aux_stack.append("}")

    def emit_tuple(obj: list, paren: bool = True):
        """
        Push a list of components in tuple format
        Parameters:
            obj (list): the tuple body
            paren (bool): whether to show the parentheses, i.e.
                inheritance-specifier
        """

        nonlocal aux_stack

        if paren is True:
            aux_stack.append("(")

        if len(obj) > 0:
            for i in range(len(obj) - 1):
                aux_stack.append(obj[i])
                aux_stack.append(",")
            aux_stack.append(obj[-1])

        if paren is True:
            aux_stack.append(")")


    def emit_dict(values: List, keys: Optional[List] = None, line_break: bool = False):

        """
        Push a list of component in dict format
        Parameters:
            values (list): the dict body
            keys (list): If this field is not None, generate dict as key-value
                pairs, i.e. function-call with positional arguments

                Key list (if present) has to be equal to value list in length
            line_break (bool): If this field is True, insert LF after large
                brackets and each comma, i.e. enum-definition
        """

        nonlocal aux_stack

        if indent > 0 and line_break is True:  # indent mode, for debug purpose only
            aux_stack.append("{")
            aux_stack.append(1)
            aux_stack.append("\n")

            # Empty value list, skip generation of components
            if len(values) > 0:
                if keys is None:
                    for i in range(len(values)):
                        aux_stack.append(values[i])
                        aux_stack.append(",\n" if i < len(values) - 1 else "\n")
                else:
                    for i in range(len(values)):
                        aux_stack.append(keys[i])
                        aux_stack.append(":")
                        aux_stack.append(values[i])
                        aux_stack.append(",\n" if i < len(values) - 1 else "\n")

            aux_stack.append(-1)
            aux_stack.append("}")
            aux_stack.append("\n")
        else:
            aux_stack.append("{")

            # Empty value list, skip generation of components
            if len(values) > 0:
                if keys is None:
                    for i in range(len(values)):
                        aux_stack.append(values[i])
                        if i < len(values) - 1:
                            aux_stack.append(",")
                else:
                    for i in range(len(keys)):
                        aux_stack.append(keys[i])
                        aux_stack.append(":")
                        aux_stack.append(values[i])
                        if i < len(values) - 1:
                            aux_stack.append(",")

            aux_stack.append("}")

    def solidity(handler):
        """
        The decorator indicating a grammar handler

        Any function with this decorator handles an AST node
        """

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
    
    #####################################
    # Grammar handlers are defined here #
    #####################################

    @solidity
    def SourceUnit(node):
        if hasattr(node, "license"):
            emit("//SPDX-License-Identifier:")
            emit(node.license)
            emit("\n")  # This is necessary and has nothing to do with indent
        emit(node.nodes)

    @solidity
    def ImportDirective(node):
        # TODO: more import syntax
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
        # abstract flag
        if node.abstract is True:
            # For interface and library this's always False
            emit("abstract")
        # interface, contract or library
        emit(node.contractKind)
        # contract name
        emit(node.name)
        # inheritance
        if len(node.baseContracts) > 0:
            emit("is")
            emit_tuple(node.baseContracts, paren=False)
        # contract body
        emit_block(node.nodes)

    @solidity
    def InheritanceSpecifier(node):
        emit(node.baseName)

    @solidity
    def UserDefinedValueTypeDefinition(node):
        emit_many("type", node.name, "is", node.underlyingType)
        end_stmt()

    @solidity
    def VariableDeclaration(node):

        # state-variable-definition / constant-variable-definition
        if (
            node.parent().nodeType == "ContractDefinition"
            or node.parent().nodeType == "SourceUnit"
        ):
            # type of the member, it's also a node
            emit(node.typeName)
            # constant-variable-definition check
            if node.constant is True:
                emit("constant")
            # special attributes of state-variable-definition
            else:
                # public, private, internal, etc.
                # no need to visualize default value "internal"
                if hasattr(node, "visibility") and node.visibility != "internal":
                    emit(node.visibility)
                # immutable flag
                if node.mutability == "immutable":
                    emit("immutable")
                # state variable location, default or transient
                elif node.storageLocation != "default":
                    emit(node.storageLocation)
                # overrides any prototype?
                if hasattr(node, "overrides"):
                    emit(node.overrides)
            # name of the variable
            emit(node.name)
            # initial value
            # Note that transient state variable has no initial value
            if hasattr(node, "value"):
                emit("=")
                emit(node.value)
            end_stmt()

        # struct-member
        elif node.parent().nodeType == "StructDefinition":
            # type of the member, it's also a node
            emit(node.typeName)
            # name of the member
            emit(node.name)
            end_stmt()

        # parameter
        elif node.parent().nodeType == "ParameterList":
            # type of the parameter, it's also a node
            emit(node.typeName)
            # indexed flag, for event parameter only
            if hasattr(node, "indexed") and node.indexed is True:
                emit("indexed")
            # parameter location, memory, storage, calldata, etc.
            if node.storageLocation != "default":
                emit(node.storageLocation)
            # name of the parameter
            # Rule out anonymous variables
            if len(node.name) > 0:
                emit(node.name)
            # We don't emit semicolons here

        # other cases, i.e. variable declaration statement
        else:
            # type of the variable, it's also a node
            emit(node.typeName)
            # variable location, memory, storage, calldata, etc.
            if node.storageLocation != "default":
                emit(node.storageLocation)
            # name of the variable
            emit(node.name)

    @solidity
    def FunctionDefinition(node):

        # constructor-definition
        if node.kind == "constructor":
            emit("constructor")
            # parameter list
            emit(node.parameters)
            # list of modifiers
            if len(node.modifiers) > 0:
                emit(node.modifiers)
            # state mutability, can only be "payable" for constructors
            if node.stateMutability == "payable":
                emit("payable")
            # Function body is a must for constructors
            emit_block(node.nodes)

        # function-definition
        elif node.kind == "function" or node.kind == "freeFunction":
            emit_many("function", node.name)
            # parameter list
            emit(node.parameters)
            # Visibility is meaningless for free functions
            # public, external, internal, etc.
            if node.kind != "freeFunction":
                emit(node.visibility)
            # state mutability
            # Do not visualize "nonpayable"
            if node.stateMutability != "nonpayable":
                emit(node.stateMutability)
            # list of modifiers
            if len(node.modifiers) > 0:
                emit(node.modifiers)
            # can be overridden?
            if node.virtual is True:
                emit("virtual")
            # overrides any prototype?
            if hasattr(node, "overrides"):
                emit(node.overrides)
            # return parameters
            if len(node.returnParameters.parameters) > 0:
                emit("returns")
                emit(node.returnParameters)
            # function body, could be empty or not implemented
            if hasattr(node, "nodes"):
                emit_block(node.nodes)
            else:
                end_stmt()

        else:
            logger.warning(f"Fix me: {node.kind} function is not supported yet!")

    @solidity
    def ModifierInvocation(node):
        emit(node.modifierName)
        emit_tuple(node.arguments)

    @solidity
    def OverrideSpecifier(node):
        emit("override")
        emit_tuple(node.overrides)

    @solidity
    def ModifierDefinition(node):
        emit_many("modifier", node.name)
        # can be overridden?
        if node.virtual is True:
            emit("virtual")
        # overrides any prototype?
        if hasattr(node, "overrides"):
            emit(node.overrides)
        # modifier body, could be empty or not implemented
        if hasattr(node, "nodes"):
            emit_block(node.nodes)
        else:
            end_stmt()

    @solidity
    def ParameterList(node):
        emit_tuple(node.parameters)

    @solidity
    def EventDefinition(node):
        emit_many("event", node.name, node.parameters)
        # is it anonymous?
        if node.anonymous is True:
            emit("anonymous")
        end_stmt()

    @solidity
    def ErrorDefinition(node):
        emit_many("error", node.name, node.parameters)
        end_stmt()

    @solidity
    def EnumDefinition(node):
        emit("enum")
        emit(node.name)
        emit_dict(values=node.members, keys=None, line_break=True)

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
                # specified in official documentation
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
        if hasattr(node, "length"):
            emit_many(node.baseType, "[", node.length, "]")
        else:
            emit_many(node.baseType, "[]")

    @solidity
    def IdentifierPath(node):
        emit(node.name)

    @solidity
    def Mapping(node):
        emit_many("mapping", "(", node.keyType, "=>", node.valueType, ")")

    @solidity
    def PlaceholderStatement(node):
        emit("_")
        end_stmt()

    @solidity
    def VariableDeclarationStatement(node):
        if len(node.declarations) > 1:
            emit_tuple(node.declarations)
        else:
            emit(node.declarations[0])
        emit("=")
        emit(node.initialValue)
        caller = node.parent()
        # Special case in for statement:
        # Variable declaration statement is used as an expression
        if (
            caller.nodeType == "ForStatement"
            and node is caller.initializationExpression
        ):
            return
        end_stmt()

    @solidity
    def ExpressionStatement(node):
        emit(node.expression)
        # Special case in for statement:
        # Expression statement is used as an expression
        caller = node.parent()
        if caller.nodeType == "ForStatement" and node is caller.loopExpression:
            return
        end_stmt()

    @solidity
    def EmitStatement(node):
        # function emit() has nothing to do with solidity's emit statement!
        emit_many("emit", node.eventCall)
        end_stmt()

    @solidity
    def RevertStatement(node):
        emit_many("revert", node.errorCall)
        end_stmt()

    @solidity
    def IfStatement(node):
        emit_many("if", "(", node.condition, ")")

        # Check if else branch present
        has_else = hasattr(node, "falseBody")
        # trueBody can be a list of nodes or a normal node
        if isinstance(node.trueBody, (list, tuple)):
            # Do not insert line break if there's an else branch
            emit_block(node.trueBody, continuous=has_else)
        else:
            emit(node.trueBody)

        if has_else:
            emit("else")
            # falseBody can be a list of nodes or a normal node
            if isinstance(node.falseBody, (list, tuple)):
                emit_block(node.falseBody)
            else:
                emit(node.falseBody)

    @solidity
    def ForStatement(node):
        emit_many(
            "for",
            "(",
            node.initializationExpression,
            ";",
            node.condition,
            ";",
            node.loopExpression,
            ")",
        )
        emit_block(node.nodes)

    @solidity
    def WhileStatement(node):
        emit_many("while", "(", node.condition, ")")
        emit_block(node.nodes)

    @solidity
    def DoWhileStatement(node):
        emit("do")
        emit_block(node.nodes, continuous=True)
        emit_many("while", "(", node.condition, ")")
        end_stmt()

    @solidity
    def Return(node):
        emit_many("return", node.expression)
        end_stmt()

    @solidity
    def Break(node):
        emit("break")
        end_stmt()

    @solidity
    def TupleExpression(node):
        emit_tuple(node.components)

    @solidity
    def Continue(node):
        emit("continue")
        end_stmt()

    @solidity
    def FunctionCall(node):
        emit(node.expression)
        if len(node.names) > 0:
            emit_dict(values=node.arguments, keys=node.names, line_break=False)
        else:
            emit_tuple(node.arguments)

    @solidity
    def MemberAccess(node):
        emit_many(node.expression, ".", node.memberName)

    @solidity
    def IndexAccess(node):
        emit_many(node.baseExpression, "[", node.indexExpression, "]")

    @solidity
    def IndexRangeAccess(node):
        emit(node.baseExpression)
        emit("[")
        if hasattr(node, "startExpression"):
            emit(node.startExpression)
        emit(":")
        if hasattr(node, "endExpression"):
            emit(node.endExpression)
        emit("]")

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

    ################
    # the mainloop #
    ################

    logger.debug("Converting syntax tree to source")

    # To speed up pre-order visiting, we use stack-based iteration instead of
    # recursion.
    pre_ord_stack.append(root)

    while len(pre_ord_stack) > 0:
        x = pre_ord_stack.pop()

        # Pure string value, should send it directly to tokens
        if isinstance(x, str):
            # iff. indent is on
            if indent > 0:
                if new_line is True:
                    if shift > 0:
                        add_token(" " * shift)
                    new_line = False
                add_token(x)
                if x.endswith("\n"):
                    new_line = True
            else:
                add_token(x)

        # a node
        # We need to split it into tokens and subnodes and put 'em back to stack
        elif hasattr(x, "nodeType"):
            handler = locals().get(x.nodeType)
            if handler is not None and hasattr(handler, "solidity"):
                handler(x)
            else:
                logger.warning(f"Fix me: {x.nodeType} is not supported yet!")

        # indentation number
        # We need to set the current indentation level upon numbers
        # iff. indent is on
        elif isinstance(x, int):
            shift += x * indent
            if shift < 0:
                shift = 0

        # Undefined behaviors goes here
        else:
            logger.error(
                f"Bad node {x}! Maybe the node is missing some key attributes?"
            )

    return "".join(tokens)

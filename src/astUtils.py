import solcast
import logging

logger = logging.getLogger(__name__)


def node2src(node, indent=0) -> str:

    tokens = []  # list of source tokens
    indent_level = 0  # indent level iff. indent is on
    new_line = 0  # new line flag, indent if necessary
    aux_stack = []  # stack used for pre-order traverse

    def SourceUnit(n):
        l = []
        if hasattr(n, "license"):
            l.append("//SPDX-License-Identifier:")
            l.append(n.license)
            l.append("\n")
        l.extend(n.nodes)
        return l

    def PragmaDirective(n):
        return (
            "pragma",
            " ",
            n.literals[0],
            " ",
            *n.literals[1:],
            ";",
        )

    def ContractDefinition(n):
        l = []
        if n.abstract is True:
            l.append("abstract")
            l.append(" ")
        if n.contractKind == "interface":
            l.append("interface")
        else:
            l.append("contract")
        l.append(" ")
        l.append(n.name)
        l.append("{")
        l.extend(n.nodes)
        l.append("}")
        return l
    
    def VariableDeclarationStatement(n):
        l = []
        if len(n.declarations) > 1:
            l.append("(")
            for i in range(len(n.declarations) - 1):
                l.append(n.declarations[i])
                l.append(",")
            l.append(n.declarations[-1])
            l.append(")")
        else:
            l.append(n.declarations[0])
        l.append("=")
        l.append(n.initialValue)
        l.append(";")
        return l

    def VariableDeclaration(n):
        l = []
        # variable type
        l.append(n.typeName)
        # attributes
        if hasattr(n, "constant") and n.constant is True:
            l.append(" ")
            l.append("constant")
        elif hasattr(n, "indexed") and n.indexed is True:
            l.append(" ")
            l.append("indexed")
        elif n.visibility != "internal":
            l.append(" ")
            l.append(n.visibility)
        # variable name
        if n.name != "":  # filter out anonymous variables
            l.append(" ")
            l.append(n.name)
            # initial value
            if hasattr(n, "value"):
                l.append("=")
                l.append(n.value)
        # close the statement for state variable declaration
        if n.stateVariable is True:
            l.append(";")
        return l

    def FunctionDefinition(n):
        l = []
        # function identifier
        if n.kind == "constructor":
            l.append("constructor")
        else:
            l.append("function")
            l.append(" ")
            l.append(n.name)
        # parameter list
        l.append("(")
        if len(n.parameters.parameters) > 0:
            l.append(n.parameters)
        l.append(")")
        # visibility
        # Note that specify visibility for constructor is deprecated
        if n.kind != "constructor":
            l.append(" ")
            l.append(n.visibility)
        # state mutability
        if n.stateMutability != "nonpayable":
            l.append(" ")
            l.append(n.stateMutability)
        # is virtual
        if n.virtual is True:
            l.append(" ")
            l.append("virtual")
        # TODO: modifiers
        # return parameters
        if len(n.returnParameters.parameters) > 0:
            l.append(" ")
            l.append("returns")
            l.append("(")
            l.append(n.returnParameters)
            l.append(")")
        # function body
        if hasattr(n, "nodes"):
            l.append("{")
            l.extend(n.nodes)
            l.append("}")
        else:
            l.append(";")
        return l

    def ParameterList(n):
        l = []
        if len(n.parameters) > 0:
            for i in range(len(n.parameters) - 1):
                l.append(n.parameters[i])
                l.append(",")
            l.append(n.parameters[-1])
        return l

    def EventDefinition(n):
        l = []
        l.append("event")
        l.append(" ")
        l.append(n.name)
        l.append("(")
        if len(n.parameters.parameters) > 0:
            l.append(n.parameters)
        l.append(")")
        l.append(";")
        return l

    def ElementaryTypeNameExpression(n):
        return n.typeName

    def ElementaryTypeName(n):
        if n.name == "address":
            if hasattr(n, "stateMutability") and n.stateMutability == "payable":
                if n.parent().nodeType == "ElementaryTypeNameExpression":
                    # Handle address in expression differently, if its a payable
                    # address, use 'payable' instead of 'address payable' as
                    # specified in official documentation.
                    return "payable"
                else:
                    return "address", " ", "payable"
        return n.name

    def UserDefinedTypeName(n):
        return n.pathNode

    def IdentifierPath(n):
        return n.name

    def Mapping(n):
        return "mapping", "(", n.keyType, "=>", n.valueType, ")"

    def Literal(n):
        if n.kind == "string":
            return '"', n.value, '"'
        if hasattr(n, "subdenomination"):
            return n.value, " ", n.subdenomination
        return n.value

    def ExpressionStatement(n):
        return n.expression, ";"

    def Assignment(n):
        return n.leftHandSide, n.operator, n.rightHandSide

    def Identifier(n):
        return n.name

    def FunctionCall(n):
        l = []
        l.append(n.expression)
        l.append("(")
        if len(n.arguments) > 0:
            for i in range(len(n.arguments) - 1):
                l.append(n.arguments[i])
                l.append(",")
            l.append(n.arguments[-1])
        l.append(")")
        return l

    def EmitStatement(n):
        return "emit", " ", n.eventCall, ";"

    def IfStatement(n):
        l = []
        l.append("if")
        l.append("(")
        l.append(n.condition)
        l.append(")")
        l.append("{")
        l.extend(n.trueBody)
        l.append("}")
        if hasattr(n, "falseBody"):
            if isinstance(n.falseBody, list) or isinstance(n.falseBody, tuple):
                l.append("else")
                l.append("{")
                l.extend(n.falseBody)
                l.append("}")
            else:
                l.append("else")
                l.append(" ")
                l.append(n.falseBody)
        return l

    def MemberAccess(n):
        return n.expression, ".", n.memberName

    def IndexAccess(n):
        return n.baseExpression, "[", n.indexExpression, "]"

    def UnaryOperation(n):
        return n.operator, n.subExpression

    def BinaryOperation(n):
        return n.leftExpression, n.operator, n.rightExpression

    logger.debug("Converting syntax tree to source")

    aux_stack.append(node)

    while len(aux_stack) > 0:
        x = aux_stack.pop()
        if isinstance(x, str):
            if indent > 0:
                if x == "{":
                    indent_level += 1
                elif x == "}":
                    indent_level -= 1
                if new_line == True:
                    tokens.append(" " * indent_level * indent)
                    new_line = False
                tokens.append(x)
                if x in (";", "{", "}"):
                    tokens.append("\n")
                    new_line = True
            else:
                tokens.append(x)
        elif hasattr(x, "nodeType"):
            if x.nodeType in locals():
                f = locals()[x.nodeType]
                l = f(x)
                if isinstance(l, tuple) or isinstance(l, list):
                    # has to be reversed iterator since we're pre-ordering
                    aux_stack.extend(reversed(l))
                else:
                    aux_stack.append(l)
            else:
                logger.warning(f"AST node {x.nodeType} is not supported yet!")
        else:
            logger.warning(f"AST node of type {type(x)} is invalid")

    return "".join(tokens)

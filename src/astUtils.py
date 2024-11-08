import solcast
import logging

logger = logging.getLogger(__name__)


def node2src(node) -> str:
    str_builder = []

    sol_tokens = {
        "SourceUnit": lambda n: (n.nodes,),
        "PragmaDirective": lambda n: (
            "pragma ",
            "solidity ",
            "".join(n.literals[1:]),
            ";",
        ),
        "ContractDefinition": lambda n: (
            "abstract " if n.abstract is True else "",
            "contract ",
            n.name if hasattr(n, "name") else "",
            # TODO: inheritance
            "{",
            n.nodes,
            "}",
        ),
        "VariableDeclaration": lambda n: (
            n.typeName,
            " ",
            n.visibility,
            " ",
            n.name if hasattr(n, "name") else "",
            "=" if hasattr(n, "value") else "",
            n.value if hasattr(n, "value") else None,
            ";" if n.stateVariable is True else "",
        ),
        "ElementaryTypeName": lambda n: (n.name,),
        "Literal": lambda n: (n.value,),
        "FunctionDefinition": lambda n: (),
    }

    def visit(*nodes):
        for n in nodes:
            # check if node is valid
            node_type = n.nodeType
            if node_type not in sol_tokens:
                logger.warning(f"Node of type {n.nodeType} is not supported yet!")
                continue

            # add component
            for component in sol_tokens[node_type](n):
                if component is None:
                    continue
                elif component == "":
                    continue
                elif type(component) is str:
                    str_builder.append(component)
                elif hasattr(component, "__iter__"):
                    visit(*component)
                elif hasattr(component, "nodeType"):
                    visit(component)
                else:
                    logger.warning(f"Omitting component {component}")

    logger.debug("Revert syntax tree to source")
    visit(node)

    return "".join(str_builder)

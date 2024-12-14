import logging

from ..solidity.nodes import *
from ..solidity.utils import *
from .opaqueConstants import random_name


logger = logging.getLogger(__name__)


def extract_literals(contract: ContractDefinition) -> dict[str, list] | None:
    """Extract literals from the AST and store them in literal_storage."""

    literal_storage = {
        "uint256": {"func": random_name(), "array": []},
        "string": {"func": random_name(), "array": []},
        "address": {"func": random_name(), "array": []},
        "bool": {"func": random_name(), "array": []},
    }

    success = False

    for node in contract:
        if isinstance(node, VariableDeclaration):
            if not (hasattr(node, "value") and isinstance(node.value, Literal)):
                continue
            type_str = node.typeName.typeDescriptions["typeString"]
            try:
                storage = literal_storage[type_str]
                array: list = storage["array"]
                func_name: str = storage["func"]
                array.append(node.value)
                index = len(array) - 1
                node.value = FUNCALL(SYM(func_name), [NUM(index)])
                success = True
            except KeyError:
                logger.warning(f"Variable type {type_str} not supported!")

    if success is True:
        return literal_storage
    else:
        return None


def generate_constant_arrays(
    contract: ContractDefinition, literal_storage: dict[str, list]
):
    """Generate constant arrays for the extracted literals."""
    for key in literal_storage.keys():

        array: list = literal_storage[key]["array"]
        func_name: str = literal_storage[key]["func"]
        arr_dec = AVAR(ETYPE(key), "_" + func_name, array)
        contract.main.append(arr_dec)


def generate_functions(contract: ContractDefinition, literal_storage: dict[str, list]):
    for key in literal_storage.keys():
        array: list = literal_storage[key]["array"]
        func_name: str = literal_storage[key]["func"]
        idx_var_name = random_name(4)
        func_dec = FunctionDefinition(
            kind="function",
            name=func_name,
            parameters=ParameterList(
                parameters=[EVAR(etype="uint", name=idx_var_name, value=None)]
            ),
            visibility="internal",
            stateMutability="view",
            modifiers=[],
            virtual=False,
            returnParameters=ParameterList(
                parameters=[
                    EVAR(
                        etype=key,
                        name="",
                        value=None,
                        storage="storage" if key == "string" else "default",
                    )
                ]
            ),
            body=BLK(
                statements=[
                    Return(
                        expression=IndexAccess(
                            baseExpression=SYM("_" + func_name),
                            indexExpression=SYM(idx_var_name),
                        )
                    )
                ]
            ),
        )
        contract.main.append(func_dec)


def run(node: SourceUnit) -> SourceUnit:
    """Obfuscate the input AST node by replacing literals with function calls."""
    logger.debug("Starting data flow obfuscation")

    for contract in node.contracts:
        literal_storage = extract_literals(contract)
        if literal_storage is not None:
            generate_functions(contract, literal_storage)
            generate_constant_arrays(contract, literal_storage)

    logger.debug("Data flow obfuscation completed")
    return node

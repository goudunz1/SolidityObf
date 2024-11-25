import logging
from createNodes_data import *
from solcast.nodes import NodeBase


logger = logging.getLogger(__name__)

literal_storage = {
    "int": [],
    "str": [],
    "addr": [],
    "bool": []
}


def extract_literals(node):
    """Extract literals from the AST and store them in literal_storage."""
    if hasattr(node, 'value'):
        Type = node.typeName.typeDescriptions['typeString']
       # print(f"Node type:  {Type}")  # Debug print
      #  print(f"Node   {node}")  # Debug print
        if Type == "bool":
            literal_storage["bool"].append(node.value)
        elif Type == "string":
            literal_storage["str"].append(node.value)
        elif Type == "uint256":
            literal_storage["int"].append(node.value)
        elif Type == "address":
            literal_storage["addr"].append(node.value)

    if hasattr(node, 'nodes'):
        for child in node.nodes:
            extract_literals(child)
def generate_constant_arrays(node):
    """Generate constant arrays for the extracted literals."""
    #constants = []
   # for value in literal_storage.values():
    #    print("Values" + str(value))
    for key in literal_storage.keys():
        print("key", key)
        if key == "int":
            var_State = {"number":len(literal_storage["int"]), "type":"uint256", "name":"_integer_constant"}
            state = createVariableArray(var_State)
            for i in range(len(literal_storage["int"])):
                value = literal_storage["int"][i].value
                literal_int = {"kind": "number", "value": value}
                literalComponents = createDifferentLiteral(literal_int)
                state.value.components.append(literalComponents)
                print("state.value.components", state.value.components)
                node[1].nodes.append(state)

        if key == "str":
            var_State = {"number":len(literal_storage["str"]), "type":"string", "name":"_string_constant"}
            state = createVariableArray(var_State)
            for i in range(len(literal_storage["str"])):
                value = literal_storage["str"][i].value
                literal_int = {"kind": "string", "value": value}
                literalComponents = createDifferentLiteral(literal_int)
                state.value.components.append(literalComponents)
                node[1].nodes.append(state)

        if key == "addr":
            var_State = {"number":len(literal_storage["addr"]), "type":"address", "name":"_address_constant"}
            state = createVariableArray(var_State)
            for i in range(len(literal_storage["addr"])):
                value = literal_storage["addr"][i].value
                literal_int = {"kind": "number", "value": value}
                literalComponents = createDifferentLiteral(literal_int)
                state.value.components.append(literalComponents)
                node[1].nodes.append(state)

        if key == "bool":
            var_State = {"number":len(literal_storage["bool"]), "type":"bool", "name":"_bool_constant"}
            state = createVariableArray(var_State)
            for i in range(len(literal_storage["bool"])):
                value = literal_storage["bool"][i].value
                literal_int = {"kind": "bool", "value": value}
                literalComponents = createDifferentLiteral(literal_int)
                state.value.components.append(literalComponents)
                node[1].nodes.append(state)
            constants.append(NodeBase(array_ast, None))
    #return constants

#not right yet
def generate_functions():
    """Generate functions to retrieve the literals from the arrays."""
    functions = []
    for key in literal_storage.keys():
        if key == "int":
            func_ast = {
                "nodeType": "FunctionDefinition",
                "name": "getIntFunc",
                "visibility": "internal",
                "stateMutability": "view",
                "parameters": {
                    "nodeType": "ParameterList",
                    "parameters": [
                        {
                            "nodeType": "VariableDeclaration",
                            "typeName": {
                                "nodeType": "ElementaryTypeName",
                                "name": "uint256"
                            },
                            "name": "index",
                            "storageLocation": "default",
                            "isStateVar": False,
                            "isIndexed": False
                        }
                    ]
                },
                "returnParameters": {
                    "nodeType": "ParameterList",
                    "parameters": [
                        {
                            "nodeType": "VariableDeclaration",
                            "typeName": {
                                "nodeType": "ElementaryTypeName",
                                "name": "uint256"
                            },
                            "name": "",
                            "storageLocation": "default",
                            "isStateVar": False,
                            "isIndexed": False
                        }
                    ]
                },
                "body": {
                    "nodeType": "Block",
                    "statements": [
                        {
                            "nodeType": "Return",
                            "expression": {
                                "nodeType": "IndexAccess",
                                "baseExpression": {
                                    "nodeType": "Identifier",
                                    "name": "_integer_constant"
                                },
                                "indexExpression": {
                                    "nodeType": "Identifier",
                                    "name": "index"
                                }
                            }
                        }
                    ]
                },
                "src": "0:0:0"  # Dummy src attribute
            }
            functions.append(NodeBase(func_ast, None))
        elif key == "str":
            func_ast = {
                "nodeType": "FunctionDefinition",
                "name": "getStrFunc",
                "visibility": "internal",
                "stateMutability": "view",
                "parameters": {
                    "nodeType": "ParameterList",
                    "parameters": [
                        {
                            "nodeType": "VariableDeclaration",
                            "typeName": {
                                "nodeType": "ElementaryTypeName",
                                "name": "uint256"
                            },
                            "name": "index",
                            "storageLocation": "default",
                            "isStateVar": False,
                            "isIndexed": False
                        }
                    ]
                },
                "returnParameters": {
                    "nodeType": "ParameterList",
                    "parameters": [
                        {
                            "nodeType": "VariableDeclaration",
                            "typeName": {
                                "nodeType": "ElementaryTypeName",
                                "name": "string"
                            },
                            "name": "",
                            "storageLocation": "default",
                            "isStateVar": False,
                            "isIndexed": False
                        }
                    ]
                },
                "body": {
                    "nodeType": "Block",
                    "statements": [
                        {
                            "nodeType": "Return",
                            "expression": {
                                "nodeType": "IndexAccess",
                                "baseExpression": {
                                    "nodeType": "Identifier",
                                    "name": "_string_constant"
                                },
                                "indexExpression": {
                                    "nodeType": "Identifier",
                                    "name": "index"
                                }
                            }
                        }
                    ]
                },
                "src": "0:0:0"  # Dummy src attribute
            }
            functions.append(NodeBase(func_ast, None))
        elif key == "addr":
            func_ast = {
                "nodeType": "FunctionDefinition",
                "name": "getAddrFunc",
                "visibility": "internal",
                "stateMutability": "view",
                "parameters": {
                    "nodeType": "ParameterList",
                    "parameters": [
                        {
                            "nodeType": "VariableDeclaration",
                            "typeName": {
                                "nodeType": "ElementaryTypeName",
                                "name": "uint256"
                            },
                            "name": "index",
                            "storageLocation": "default",
                            "isStateVar": False,
                            "isIndexed": False
                        }
                    ]
                },
                "returnParameters": {
                    "nodeType": "ParameterList",
                    "parameters": [
                        {
                            "nodeType": "VariableDeclaration",
                            "typeName": {
                                "nodeType": "ElementaryTypeName",
                                "name": "address"
                            },
                            "name": "",
                            "storageLocation": "default",
                            "isStateVar": False,
                            "isIndexed": False
                        }
                    ]
                },
                "body": {
                    "nodeType": "Block",
                    "statements": [
                        {
                            "nodeType": "Return",
                            "expression": {
                                "nodeType": "IndexAccess",
                                "baseExpression": {
                                    "nodeType": "Identifier",
                                    "name": "_address_constant"
                                },
                                "indexExpression": {
                                    "nodeType": "Identifier",
                                    "name": "index"
                                }
                            }
                        }
                    ]
                },
                "src": "0:0:0"  # Dummy src attribute
            }
            functions.append(NodeBase(func_ast, None))
        elif key == "bool":
            func_ast = {
                "nodeType": "FunctionDefinition",
                "name": "getBoolFunc",
                "visibility": "internal",
                "stateMutability": "view",
                "parameters": {
                    "nodeType": "ParameterList",
                    "parameters": [
                        {
                            "nodeType": "VariableDeclaration",
                            "typeName": {
                                "nodeType": "ElementaryTypeName",
                                "name": "uint256"
                            },
                            "name": "index",
                            "storageLocation": "default",
                            "isStateVar": False,
                            "isIndexed": False
                        }
                    ]
                },
                "returnParameters": {
                    "nodeType": "ParameterList",
                    "parameters": [
                        {
                            "nodeType": "VariableDeclaration",
                            "typeName": {
                                "nodeType": "ElementaryTypeName",
                                "name": "bool"
                            },
                            "name": "",
                            "storageLocation": "default",
                            "isStateVar": False,
                            "isIndexed": False
                        }
                    ]
                },
                "body": {
                    "nodeType": "Block",
                    "statements": [
                        {
                            "nodeType": "Return",
                            "expression": {
                                "nodeType": "IndexAccess",
                                "baseExpression": {
                                    "nodeType": "Identifier",
                                    "name": "_bool_constant"
                                },
                                "indexExpression": {
                                    "nodeType": "Identifier",
                                    "name": "index"
                                }
                            }
                        }
                    ]
                },
                "src": "0:0:0"  # Dummy src attribute
            }
            functions.append(NodeBase(func_ast, None))
    return functions

#not right yet
def replace_literals(node):
    """Recursively replace literals with function calls."""
    if hasattr(node, 'value'):
        if isinstance(node.value, int):
            index = literal_storage["int"].index(node.value)
            node.value = createIdentifier(f"getIntFunc({index})")
        elif isinstance(node.value, str):
            index = literal_storage["str"].index(node.value)
            node.value = createIdentifier(f"getStrFunc({index})")
        elif isinstance(node.value, bool):
            index = literal_storage["bool"].index(node.value)
            node.value = createIdentifier(f"getBoolFunc({index})")
        elif isinstance(node.value, dict) and node.value.get('type') == 'address':
            index = literal_storage["addr"].index(node.value['value'])
            node.value = createIdentifier(f"getAddrFunc({index})")

    if hasattr(node, 'nodes'):
        for child in node.nodes:
            replace_literals(child)

def obfuscate(node):
    """Obfuscate the input AST node by replacing literals with function calls."""
    logger.debug("Starting data flow obfuscation")
    # Exotract literals
    extract_literals(node)
    generate_constant_arrays(node)
    '''
    # Generate dynamic functions
    functions = generate_functions()
    # Replace literals
    replace_literals(node)
    '''

    logger.debug("Data flow obfuscation completed")
    return node
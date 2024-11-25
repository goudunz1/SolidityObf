from solcast.nodes import NodeBase

def createDifferentLiteral(literal):
    ast = {
        "hexValue": "35",
        "id": 72,
        "isConstant": False,
        "isLValue": False,
        "isPure": True,
        "kind": literal["kind"],
        "lValueRequested": False,
        "nodeType": "Literal",
        "src": "289:1:0",
        "typeDescriptions": {
        "typeIdentifier": f"t_rational_{literal['value']}_by_1",
        "typeString": f"int_const{literal['value']}"
            #t_rational_42_by_1",
            #"typeString": "int_const 42"
        },
        "value": literal["value"]
    }
    return NodeBase(ast, None)
def createVariableArray(variable_dict):
    ast = {
                "constant": False,
                "id": 89,
                "mutability": "mutable",
                "name": variable_dict["name"],
                "nameLocation": "897:14:0",
                "nodeType": "VariableDeclaration",
                "scope": 90,
                "src": "0:0:0",
                "stateVariable": True,
                "storageLocation": "default",
                "typeDescriptions":
                {
                "typeIdentifier": f"t_array$_t_{variable_dict['type']}_$dyn_storage",
                "typeString": f"{variable_dict['type']}[]"
                },
                "typeName": {
                     "baseType": {
                        "id": 85,
                        "name": variable_dict["type"],
                        "nodeType": "ElementaryTypeName",
                        "src": "0:0:0",
                        "typeDescriptions": {
                            "typeIdentifier": f"t_{variable_dict['type']}",
                                    "typeString": variable_dict['type']
                        }
                    },
                    "id": 71,
                    "nodeType": "ArrayTypeName",
                    "src": "0:0:0",
                    "typeDescriptions": {
                        "typeIdentifier": f"t_array$_t_{variable_dict['type']}_$dyn_storage_ptr",
                        "typeString": f"{variable_dict['type']}[]",
                    }
                },
                "value": {
                    "components": [],
                    '''
                        {
                        
                        "hexValue": "3130",
                        "id": 17,
                        "isConstant": False,
                        "isLValue": False,
                        "isPure": True,
                        "kind": "number",
                        "lValueRequested": False,
                        "nodeType": "Literal",
                        "src": "0:0:0",
                        "typeDescriptions": {
                            "typeIdentifier": f"t_rational_{variable_dict['value']}_by_1",
                            "typeString": f"int_const {variable_dict['value']}"
                        },
                        "value": variable_dict["value"]
                        },
                    '''
                    "id": 80,
                    "isConstant": False,
                    "isInlineArray": True,
                    "isLValue": False,
                    "isPure": True,
                    "lValueRequested": False,
                    "nodeType": "TupleExpression",
                    "src": "782:18:0",
                    "typeDescriptions": {
                        "typeIdentifier": f"t_array$_t_string_memory_ptr_${variable_dict['number']}_memory_ptr",
                        "typeString": f"string memory[{variable_dict['number']}] memory"
                    },

                },
                "visibility": "private",
        }
    return NodeBase(ast, None)

def createVariable(variable_dict):
    ast = {
            "assignments": [
                            16
                        ],
            "declarations": [
            {
                "constant": False,
                "id": 16,
                "mutability": "mutable",
                "name": variable_dict["name"],
                "nameLocation": "196:7:0",
                "nodeType": "VariableDeclaration",
                "scope": 121,
                "src": "0:0:0",
                "stateVariable": False,
                "storageLocation": "default",
                "typeDescriptions": {
                "typeIdentifier": "t_uint256",
                "typeString": "uint256"
                },
                "typeName": {
                "id": 15,
                "name":
                    ["type"],
                "nodeType": "ElementaryTypeName",
                "src": "0:0:0",
                "typeDescriptions": {
                    "typeIdentifier": "t_uint256",
                    "typeString": "uint256"
                }
                },
                "visibility": "internal"
            }
            ],
            "id": 18,
            "initialValue": {
            "hexValue": "3130",
            "id": 17,
            "isConstant": False,
            "isLValue": False,
            "isPure": True,
            "kind": "number",
            "lValueRequested": False,
            "nodeType": "Literal",
            "src": "0:0:0",
            "typeDescriptions": {
                "typeIdentifier": f"t_rational_{variable_dict['value']}_by_1",
                "typeString": f"int_const {variable_dict['value']}"
            },
            "value": variable_dict["value"]
            },
            "nodeType": "VariableDeclarationStatement",
            "src": "0:0:0"
    }
    return NodeBase(ast, None)

# 创建If语句
def createIfStatement():
    # 可以先不填truebody及falsebody，设置statements，后面再填
    ast = {
            "condition": {
            # 其中是binaryOperation
            },
            "falseBody": {  "id": 47,
                            "nodeType": "Block",
                            "src": "317:169:0",
                            "statements":[]
                            },
            "trueBody": {   "id": 47,
                            "nodeType": "Block",
                            "src": "317:169:0",
                            "statements":[]
                            },
            "id": 48,
            "nodeType": "IfStatement",
            "src": "0:0:0"
    }
    return NodeBase(ast, None)


def createBinaryOperation(binaryStatement_dict):
    if isinstance(binaryStatement_dict["left"], str):
        left = createIdentifier(binaryStatement_dict["left"])
    elif isinstance(binaryStatement_dict["left"], int):
        left = createLiteral(str(binaryStatement_dict["left"])) 
    if isinstance(binaryStatement_dict["right"], str):
        right = createIdentifier(binaryStatement_dict["right"])
    elif isinstance(binaryStatement_dict["right"], int):
        right = createLiteral(str(binaryStatement_dict["right"])) 
    ast = {
        "commonType": {
                "typeIdentifier": "t_uint256",
                "typeString": "uint256"
            },
            "id": 28,
            "isConstant": False,
            "isLValue": False,
            "isPure": False,
            "lValueRequested": False,
            "leftExpression": {
            },
            "nodeType": "BinaryOperation",
            "operator": binaryStatement_dict["operator"],
            "rightExpression": {
            },
            "src": "279:11:0",
            "typeDescriptions": {
                "typeIdentifier": "t_bool",
                "typeString": "bool"
            }
    }
    binary_opt = NodeBase(ast, None)
    binary_opt.leftExpression = left
    binary_opt.rightExpression = right
    return binary_opt

def createLiteral(value):
    ast = {
        "hexValue": "35",
        "id": 27,
        "isConstant": False,
        "isLValue": False,
        "isPure": True,
        "kind": "number",
        "lValueRequested": False,
        "nodeType": "Literal",
        "src": "289:1:0",
        "typeDescriptions": {
        "typeIdentifier": "t_rational_5_by_1",
        "typeString": "int_const 5"
        },
        "value": value
    }
    return NodeBase(ast, None)

def createIdentifier(name):
    ast = {
        "id": 26,
        "name": name,
        "nodeType": "Identifier",
        "overloadedDeclarations": [],
        "referencedDeclaration": 16,
        "src": "279:7:0",
        "typeDescriptions": {
        "typeIdentifier": "t_uint256",
        "typeString": "uint256"
        }
    }
    return NodeBase(ast, None)

def createEpression(exp_dict):
    ast = { 
                      "expression": {
                        "id": 11,
                        "isConstant": False,
                        "isLValue": False,
                        "isPure": False,
                        "lValueRequested": False,
                        "leftHandSide": {
                          "id": 9,
                          "name": exp_dict["name"],
                          "nodeType": "Identifier",
                          "overloadedDeclarations": [],
                          "referencedDeclaration": 4,
                          "src": "388:9:0",
                          "typeDescriptions": {
                            "typeIdentifier": "t_uint256",
                            "typeString": "uint256"
                          }
                        },
                        "nodeType": "Assignment",
                        "operator": "=",
                        "rightHandSide": {
                          "hexValue": "313030",
                          "id": 10,
                          "isConstant": False,
                          "isLValue": False,
                          "isPure": True,
                          "kind": "number",
                          "lValueRequested": False,
                          "nodeType": "Literal",
                          "src": "400:3:0",
                          "typeDescriptions": {
                            "typeIdentifier": f"t_rational_{exp_dict['value']}_by_1",
                            "typeString": f"int_const {exp_dict['value']}"
                          },
                          "value": exp_dict["value"]
                        },
                        "src": "388:15:0",
                        "typeDescriptions": {
                          "typeIdentifier": "t_uint256",
                          "typeString": "uint256"
                        }
                      },
                      "id": 12,
                      "nodeType": "ExpressionStatement",
                      "src": "388:15:0"                   
    }
    return NodeBase(ast, None)
    
'''
binary_opt = {"left":"test", "operator":"+", "right": 5}
print(createBinaryOperation(binary_opt).leftExpression)

b = createBinaryOperation()
print(b)
test = createIfStatement
test.condition = b
print(test.condition.leftExpression)'''
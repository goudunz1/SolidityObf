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
            index = len(literal_storage["bool"])
            function = {"number": index, "name": "getBoolFunc", "typeIdentifier": "t_uint256", "typeString": "uint256"}
            node.value = valueFuctionCall(function)
        elif Type == "string":
            literal_storage["str"].append(node.value)
            index = len(literal_storage["bool"])
            function = {"number": index, "name": "getStrFunc", "typeIdentifier": "t_string_storage_ptr",  "typeString": "string storage pointer"}
            node.value = valueFuctionCall(function)
        elif Type == "uint256":
            literal_storage["int"].append(node.value)
            index = len(literal_storage["bool"])
            function = {"number": index, "name": "getIntFunc", "typeIdentifier": "t_address", "typeString": "address"}
            node.value = valueFuctionCall(function)
        elif Type == "address":
            literal_storage["addr"].append(node.value)
            index = len(literal_storage["bool"])
            function = {"number": index, "name": "getAddrFunc", "typeIdentifier": "t_bool", "typeString": "bool"}
            node.value = valueFuctionCall(function)
    if hasattr(node, 'nodes'):
        for child in node.nodes:
            extract_literals(child)
def generate_constant_arrays(node):
    contract = find_Contract(node)
    """Generate constant arrays for the extracted literals."""
    #constants = []
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
            contract.nodes.append(state)

        if key == "str":
            var_State = {"number":len(literal_storage["str"]), "type":"string", "name":"_string_constant"}
            state = createVariableArray(var_State)
            for i in range(len(literal_storage["str"])):
                value = literal_storage["str"][i].value
                literal_int = {"kind": "string", "value": value}
                literalComponents = createDifferentLiteral(literal_int)
                state.value.components.append(literalComponents)
            contract.nodes.append(state)

        if key == "addr":
            var_State = {"number":len(literal_storage["addr"]), "type":"address", "name":"_address_constant"}
            state = createVariableArray(var_State)
            for i in range(len(literal_storage["addr"])):
                value = literal_storage["addr"][i].value
                literal_int = {"kind": "number", "value": value}
                literalComponents = createDifferentLiteral(literal_int)
                state.value.components.append(literalComponents)
            contract.nodes.append(state)

        if key == "bool":
            var_State = {"number":len(literal_storage["bool"]), "type":"bool", "name":"_bool_constant"}
            state = createVariableArray(var_State)
            for i in range(len(literal_storage["bool"])):
                value = literal_storage["bool"][i].value
                literal_int = {"kind": "bool", "value": value}
                literalComponents = createDifferentLiteral(literal_int)
                state.value.components.append(literalComponents)
            contract.nodes.append(state)

    #return constants
def generate_functions(node):
    contract = find_Contract(node)
    '''
    boolFunction = {"functionName": "getBoolFunc", "name": "_bool_constant", "type": "bool", "typeIdentifier": "bool", "typeString":"bool", "typeReturn": "bool"}
    stringFunction = {"functionName": "getStrFunc", "name": "_string_constant", "type": "string", "typeIdentifier": "string_storage", "typeString":"string storage ref", "typeReturn": "string_storage_ptr"}
    addressFunction = {"functionName": "getAddrFunc", "name": "_address_constant", "type": "address", "typeIdentifier": "address", "typeString":"address", "typeReturn": "address"}
    intFunction = {"functionName": "getIntFunc", "name": "_integer_constant", "type": "uint256", "typeIdentifier": "uint256", "typeString":"uint256", "typeReturn": "uint256"}
    '''
    boolFunction = {"functionName": "getBoolFunc", "type": "bool", "storage": "default"}
    stringFunction = {"functionName": "getStrFunc", "name": "_string_constant", "type": "string", "storage": "storage"}
    addressFunction = {"functionName": "getAddrFunc", "name": "_address_constant", "type": "address", "storage": "default"}
    intFunction = {"functionName": "getIntFunc", "name": "_integer_constant", "type": "uint256", "storage": "default"}
    bool = {"typeIdentifier": "bool", "typeString":"bool", "name": "_bool_constant"}
    address = {"typeIdentifier": "address", "typeString":"address", "name": "_address_constant"}
    int = {"typeIdentifier": "uint256", "typeString":"uint256", "name": "_integer_constant"}
    string = {"typeIdentifier": "string_storage", "typeString":"string storage ref", "name": "_string_constant"}
    function = FuctionCall(boolFunction)
    functionStatement = FunctionStatement(bool)
    print("function.body", function.body)
    function.body.append(functionStatement)
    functionStatement._parent = function
    print("function.statement", functionStatement)
    #function.body.statements.append()
    contract.nodes.append(function)
    #function.body._parent = function
    #print("function.body", function.body)
    #print("function.returnParameters", function.returnParameters)
    function = FuctionCall(stringFunction)
    functionStatement = FunctionStatement(string)
    function.body.append(functionStatement)
    contract.nodes.append(function)
    function = FuctionCall(addressFunction)
    functionStatement = FunctionStatement(address)
    function.body.append(functionStatement)
    contract.nodes.append(function)
    function = FuctionCall(intFunction)
    functionStatement = FunctionStatement(int)
    function.body.append(functionStatement)
    #print ("Function nodeType", function.nodeTyoe)
    contract.nodes.append(function)


def obfuscate(node):
    """Obfuscate the input AST node by replacing literals with function calls."""
    logger.debug("Starting data flow obfuscation")
    # Exotract literals
    extract_literals(node)
    generate_constant_arrays(node)
    # Generate dynamic functions
    generate_functions(node)
    for nodes in contract.nodes:
        nodes._parent = contract
        #contract._children.add(nodes)
        print("nodes._parent", nodes._parent)
    print(contract.nodes)


    logger.debug("Data flow obfuscation completed")
    return node
from createNodes import *

index = 0


class TreeNode:
    def __init__(self, value):
        self.value = value
        self.parent = None
        self.index = -1
        self.nodeType = None
        self.siblings = []
        self.children = []

    def add_sibling(self, sibling):
        self.siblings.append(sibling)

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def __repr__(self):
        return f"TreeNode({self.value})"

# 形成控制流图
def create_CFgraph(root: TreeNode):
    global index
    expList = []
    childList = []
    if root.nodeType == "root":
        for n in root.value.nodes:
            if n.nodeType == "IfStatement":
                child = TreeNode(n)
                child.index = index
                child.nodeType = "IF"
                childList.append(child)
                index += 1
                if "trueBody" in n.fields:
                    c1 = TreeNode(n.trueBody)
                    c1.index = index
                    c1.nodeType = "tbody"
                    child.add_child(c1)
                    index += 1
                    create_CFgraph(c1)
                if "falseBody" in n.fields:
                    c2 = TreeNode(n.falseBody)
                    c2.index = index
                    c2.nodeType = "fbody"
                    child.add_child(c2)
                    index += 1
                    create_CFgraph(c2)
            else:
                expList.append(n)
    elif root.nodeType in ("tbody", "fbody"):
        for n in root.value:
            if n.nodeType == "IfStatement":
                child = TreeNode(n)
                child.nodeType = "IF"
                childList.append(child)
                if "trueBody" in n.fields:
                    c1 = TreeNode(n.trueBody)
                    c1.index = index
                    c1.nodeType = "tbody"
                    child.add_child(c1)
                    index += 1
                    create_CFgraph(c1)
                if "falseBody" in n.fields:
                    c2 = TreeNode(n.falseBody)
                    c2.index = index
                    c2.nodeType = "fbody"
                    child.add_child(c2)
                    index += 1
                    create_CFgraph(c2)
            else:
                expList.append(n)
    child = TreeNode(expList)
    child.nodeType = "expList"
    childList.append(child)
    for i,children in enumerate(childList):
        root.add_child(children)
        for j in range(len(childList)):
            if i != j:
                children.add_sibling(childList[j])
        #children.add_sibling(childList[j] for j in range(len(childList)) if i != j)
        #print(children.siblings)
    if len(root.children) > 1:
        child.index = index
        index += 1
    return

# 从控制流图中提取基本块
def extractBlockFromTree(node, block_list, level=0):
    if node.index >= 0:
        block_list.append(node)
    # 打印当前节点
    print('  ' * level ,node ,node.index)
    # 递归打印子节点
    for child in node.children:
        block_list = extractBlockFromTree(child, block_list, level + 1)
    return block_list

def obfuscate(node):
    # 查询while节点(可能有多个) 
    # TODO 收集所有WhileStatement 
    while_Node = find_WhileStatement(node[1])
    parent = while_Node.parent() # 父节点
    
    #print(while_Node[0].condition.leftExpression)# [<ExpressionStatement object>]
    '''# 获取while循环条件
    while_condition = get_BinaryOperation_code(while_Node) 
    print(while_condition)'''

    # 创建state状态变量，插入到控制流之前
    var_State = {"type":"unit256", "name":"state", "value":"0"}
    state = createVariable(var_State)
    index = parent.nodes.index(while_Node)
    parent.nodes.insert(index, state)

    # 创建控制流图
    root = TreeNode(while_Node)
    root.nodeType = "root"
    create_CFgraph(root)
    
    # 提取基本块
    block_list = []
    extractBlockFromTree(root, block_list)
    print(block_list)    

    # print(root.children[0].children[0].children)

    # 根据基本块及控制流图进行ControlFlow_Flatten
    node_list = []
    for child in block_list:
        if1 = createIfStatement()
        binary_condition = {"left":"state", "operator":"==", "right": child.index}
        condition = createBinaryOperation(binary_condition)
        if1.condition = condition
        if1.fields.remove("falseBody")

        if child.nodeType == "IF":
            trueBody = createIfStatement()
            inner_condition = child.value.condition
            jump_index2 = -2
            for i in child.children:
                if i.nodeType == "tbody":
                    jump_index1 = i.index
                elif i.nodeType == "fbody":
                    jump_index2 = i.index
            inner_trueBody = createEpression({"name":"state", "value":str(jump_index1)})
            if jump_index2 < 0:
                trueBody.fields.remove("falseBody")
            else:
                inner_falseBody = createEpression({"name":"state", "value":str(jump_index2)})
                trueBody.falseBody.append(inner_falseBody)
            trueBody.condition = inner_condition
            trueBody.trueBody.append(inner_trueBody)
            if1.trueBody = trueBody

        elif child.nodeType in ("tbody", "fbody"):
            flag = False
            for i in child.value:
                if i.nodeType == "IfStatement":
                    flag = True
                    break
            if flag == True:
                for children in child.children:
                    if children.nodeType == "IF":
                        trueBody = createIfStatement()
                        inner_condition = children.value.condition
                        jump_index2 = -2
                        for i in children.children:
                            if i.nodeType == "tbody":
                                jump_index1 = i.index
                            elif i.nodeType == "fbody":
                                jump_index2 = i.index
                        inner_trueBody = createEpression({"name":"state", "value":str(jump_index1)})
                        if jump_index2 < 0:
                            trueBody.fields.remove("falseBody")
                        else:
                            inner_falseBody = createEpression({"name":"state", "value":str(jump_index2)})
                            trueBody.falseBody.append(inner_falseBody)
                        trueBody.condition = inner_condition
                        trueBody.trueBody.append(inner_trueBody)
                        if1.trueBody = trueBody
                        break
            else:
                inner_ExpressionList = []
                _index = get_sibling_index(child)
                if _index == None:
                    _index = 0
                inner_Expression = createEpression({"name":"state", "value":str(_index)})
                for i in child.value:
                    inner_ExpressionList.append(i)
                inner_ExpressionList.append(inner_Expression)
                if1.trueBody = inner_ExpressionList   

        elif child.nodeType == "expList":
            inner_ExpressionList = []
            _index = get_sibling_index(child)
            if _index == None:
                _index = 0
            inner_Expression = createEpression({"name":"state", "value":str(_index)})
            for i in child.value:
                inner_ExpressionList.append(i)
            inner_ExpressionList.append(inner_Expression)
            if1.trueBody = inner_ExpressionList
        node_list.append(if1)
    #print(node_list[0].trueBody.falseBody[0].expression.rightHandSide)
    print(node_list)

    # 向while节点中添加
    while_Node.nodes = node_list
    return node

# 给定一个节点，查询该节点祖先的兄弟节点，如果有某个兄弟节点是Expression类型的话，则返回该兄弟节点的index
def get_sibling_index(node: TreeNode):
    while node:
        for i in node.siblings:
            if i.nodeType == "expList":
                return i.index
        node = node.parent

# 获取while循环的条件
def get_BinaryOperation_code(while_Node):
    def get_condition(condition):
        if condition.nodeType == "BinaryOperation":
            # 如果条件是 BinaryOperation 类型，递归获取左右子条件
            return get_condition(condition.leftExpression) + " " + condition.operator + " " + get_condition(condition.rightExpression)
        elif condition.nodeType == "Assignment":
            # 如果条件是 Assignment类型
            return get_condition(condition.leftHandSide) + " " + condition.operator + " " + get_condition(condition.rightHandSide)
        else:
            # 如果条件不是 BinaryOperation 类型，它就是一个具体的变量或常数
            if condition.nodeType == "Literal": # 常数
                return condition.value
            else:
                return condition.name
    # 获取条件表达式
    condition_expression = get_condition(while_Node.condition)
    return condition_expression

def find_WhileStatement(node):
    try:
        if node.nodes:
            for element in node.nodes:
                if element.nodeType == "WhileStatement":
                    print(element)
                    return element
                while_node = find_WhileStatement(element)
    except:
        return
    
    return while_node

'''
def get_while_code(while_node):
    # 递归函数来获取ifStatement的代码
    def get_if_statement_code(if_statement):
        condition_code = get_condition_code(if_statement.condition)
        true_body_code = get_while_code(if_statement.truebody)
        false_body_code = get_while_code(if_statement.falsebody) if if_statement.falsebody else ""
        return f"if ({condition_code}) {{\n{true_body_code}\n}}" + (f"\nelse {{\n{false_body_code}\n}}" if false_body_code else "")

    # 递归函数来获取条件的代码
    def get_condition_code(condition):
        if isinstance(condition, BinaryClass):
            return f"({get_condition_code(condition.left)} {condition.operator} {get_condition_code(condition.right)})"
        # 这里可以添加更多的条件类型处理
        else:
            return str(condition)

    # 递归函数来获取表达式（或语句）的代码
    def get_statement_code(statement):
        if isinstance(statement, ifStatement):
            return get_if_statement_code(statement)
        elif isinstance(statement, ExpressionStatement):
            expression_code = get_expression_code(statement.expression)
            return f"{expression_code};\n"
        elif isinstance(statement, return):
            expression_code = get_expression_code(statement.expression)
            return f"return {expression_code};\n"
        # 其他节点类型可以在这里添加处理逻辑
        else:
            raise ValueError(f"Unsupported statement type: {type(statement)}")

    # 递归函数来获取表达式的代码
    def get_expression_code(expression):
        if isinstance(expression, BinaryClass):
            return f"({get_expression_code(expression.left)} {expression.operator} {get_expression_code(expression.right)})"
        # 这里可以添加更多的表达式类型处理
        else:
            return str(expression)

    # 构建while循环的代码
    body_code = ""
    for node in while_node.nodes:
        body_code += get_statement_code(node)

    return f"while (true) {{\n{body_code}\n}}"
'''

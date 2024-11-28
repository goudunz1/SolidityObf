from createNodes import *

Index = 0


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
    global Index
    expList = []
    childList = []
    if root.nodeType == "root":
        try:
            for n in root.value.nodes:
                if n.nodeType == "IfStatement":
                    child = TreeNode(n)
                    child.index = Index
                    child.nodeType = "IF"
                    childList.append(child)
                    Index += 1
                    if "trueBody" in n.fields:
                        c1 = TreeNode(n.trueBody)
                        c1.index = Index
                        c1.nodeType = "tbody"
                        child.add_child(c1)
                        Index += 1
                        create_CFgraph(c1)
                    if "falseBody" in n.fields:
                        c2 = TreeNode(n.falseBody)
                        c2.index = Index
                        c2.nodeType = "fbody"
                        child.add_child(c2)
                        Index += 1
                        create_CFgraph(c2)
                else:
                    expList.append(n)
        except:
            n = root.value
            if n.nodeType == "IfStatement":
                root.index = Index
                root.nodeType = "IF"
                Index += 1
                if "trueBody" in n.fields:
                    c1 = TreeNode(n.trueBody)
                    c1.index = Index
                    c1.nodeType = "tbody"
                    root.add_child(c1)
                    Index += 1
                    create_CFgraph(c1)
                if "falseBody" in n.fields:
                    c2 = TreeNode(n.falseBody)
                    c2.index = Index
                    c2.nodeType = "fbody"
                    root.add_child(c2)
                    Index += 1
                    create_CFgraph(c2)

    elif root.nodeType in ("tbody", "fbody"):
        for n in root.value:
            if n.nodeType == "IfStatement":
                child = TreeNode(n)
                child.nodeType = "IF"
                childList.append(child)
                if "trueBody" in n.fields:
                    c1 = TreeNode(n.trueBody)
                    c1.index = Index
                    c1.nodeType = "tbody"
                    child.add_child(c1)
                    Index += 1
                    create_CFgraph(c1)
                if "falseBody" in n.fields:
                    c2 = TreeNode(n.falseBody)
                    c2.index = Index
                    c2.nodeType = "fbody"
                    child.add_child(c2)
                    Index += 1
                    create_CFgraph(c2)
            else:
                expList.append(n)
    if len(expList) != 0:
        child = TreeNode(expList)
        child.nodeType = "expList"
        childList.append(child)
    for i, children in enumerate(childList):
        root.add_child(children)
        for j in range(len(childList)):
            if i != j:
                children.add_sibling(childList[j])
    try:
        if len(root.children) > 1:
            child.index = Index
            Index += 1
    except:
        pass
    return


# 从控制流图中提取基本块
def extractBlockFromTree(node, block_list, level=0):
    if node.index >= 0:
        block_list.append(node)
    # 打印当前节点
    # print('  ' * level ,node ,node.index)
    # 递归打印子节点
    for child in node.children:
        block_list = extractBlockFromTree(child, block_list, level + 1)
    return block_list

def obfuscate(node):
    global Index
    # 查询while节点(可能有多个)
    f_node = []
    for index, element in enumerate(node.nodes):
        if element.nodeType == "ContractDefinition":
            f_node.append(index)
    for n in f_node:
        while_Nodes = find_While_and_If_Statement(
            node[n]
        )
        
        # print(while_Nodes)
        statenumber = 0
        for while_Node in while_Nodes:
            parent = while_Node.parent()  # 父节点

            # 创建state状态变量，插入到控制流之前
            var_State = {"type": "uint256", "name": f"state{statenumber}", "value": "0"}
            state = createVariable(var_State, parent)
            index = parent.nodes.index(while_Node)
            parent.nodes.insert(index, state)

            # 创建控制流图
            root = TreeNode(while_Node)
            root.nodeType = "root"
            create_CFgraph(root)

            # 提取基本块
            block_list = []
            extractBlockFromTree(root, block_list)
            # print("+++++:",block_list)

            # 根据基本块及控制流图进行ControlFlow_Flatten
            node_list = []
            for child in block_list:
                if1 = createIfStatement_woF()
                binary_condition = {"left":f"state{statenumber}", "operator":"==", "right": child.index}
                condition = createBinaryOperation(binary_condition)
                if1.condition = condition
                #if1.fields.remove("falseBody")

                if child.nodeType == "IF":
                    trueBody = createIfStatement(if1)
                    inner_condition = child.value.condition
                    jump_index2 = -2
                    for i in child.children:
                        if i.nodeType == "tbody":
                            jump_index1 = i.index
                        elif i.nodeType == "fbody":
                            jump_index2 = i.index
                    inner_trueBody = createEpression(
                        {"name": f"state{statenumber}", "value": str(jump_index1)}, trueBody
                    )
                    if jump_index2 < 0:
                        #trueBody.fields.remove("falseBody")
                        trueBody = createIfStatement_woF(if1)
                    else:
                        inner_falseBody = createEpression(
                            {"name": f"state{statenumber}", "value": str(jump_index2)},
                            trueBody,
                        )
                        trueBody.falseBody.append(inner_falseBody)
                    trueBody.condition = inner_condition
                    trueBody.trueBody.append(inner_trueBody)
                    if1.trueBody = [trueBody]

                elif child.nodeType in ("tbody", "fbody"):
                    flag = False
                    for i in child.value:
                        if i.nodeType == "IfStatement":
                            flag = True
                            break
                    if flag == True:
                        for children in child.children:
                            if children.nodeType == "IF":
                                trueBody = createIfStatement(if1)
                                inner_condition = children.value.condition
                                jump_index2 = -2
                                for i in children.children:
                                    if i.nodeType == "tbody":
                                        jump_index1 = i.index
                                    elif i.nodeType == "fbody":
                                        jump_index2 = i.index
                                inner_trueBody = createEpression(
                                    {
                                        "name": f"state{statenumber}",
                                        "value": str(jump_index1),
                                    },
                                    trueBody,
                                )
                                if jump_index2 < 0:
                                    #trueBody.fields.remove("falseBody")
                                    trueBody = createIfStatement_woF(if1)
                                else:
                                    inner_falseBody = createEpression(
                                        {
                                            "name": f"state{statenumber}",
                                            "value": str(jump_index2),
                                        },
                                        trueBody,
                                    )
                                    trueBody.falseBody.append(inner_falseBody)
                                trueBody.condition = inner_condition
                                trueBody.trueBody.append(inner_trueBody)
                                if1.trueBody = [trueBody]
                                break
                    else:
                        inner_ExpressionList = []
                        _index = get_sibling_index(child)
                        if _index == None:
                            _index = 0
                        inner_Expression = createEpression(
                            {"name": f"state{statenumber}", "value": str(_index)}, if1
                        )

                        for i in child.value:

                            inner_ExpressionList.append(i)
                        inner_ExpressionList.append(inner_Expression)
                        if1.trueBody = inner_ExpressionList

                elif child.nodeType == "expList":
                    inner_ExpressionList = []
                    _index = get_sibling_index(child)
                    if _index == None:
                        _index = 0
                    inner_Expression = createEpression(
                        {"name": f"state{statenumber}", "value": str(_index)}, if1
                    )
                    # inner_Expression.parent = if1
                    for i in child.value:
                        # i.parent = if1
                        inner_ExpressionList.append(i)
                    inner_ExpressionList.append(inner_Expression)
                    if1.trueBody = inner_ExpressionList
                node_list.append(if1)

            # 向while节点中添加
            if while_Node.nodeType == "WhileStatement":
                while_Node.nodes = node_list
            else:
                index = parent.nodes.index(while_Node)
                parent.nodes.pop(index)
                parent.nodes[index:index] = node_list

            
            # 重置stateNumber
            statenumber += 1
            # 重置index
            Index = 0
    return node    

# 给定一个节点，查询该节点祖先的兄弟节点，如果有某个兄弟节点是Expression类型的话，则返回该兄弟节点的index
def get_sibling_index(node: TreeNode):
    while node:
        for i in node.siblings:
            if i.nodeType == "expList":
                return i.index
        node = node.parent


# 获取while循环的条件(not used)
def get_BinaryOperation_code(while_Node):
    def get_condition(condition):
        if condition.nodeType == "BinaryOperation":
            # 如果条件是 BinaryOperation 类型，递归获取左右子条件
            return (
                get_condition(condition.leftExpression)
                + " "
                + condition.operator
                + " "
                + get_condition(condition.rightExpression)
            )
        elif condition.nodeType == "Assignment":
            # 如果条件是 Assignment类型
            return (
                get_condition(condition.leftHandSide)
                + " "
                + condition.operator
                + " "
                + get_condition(condition.rightHandSide)
            )
        else:
            # 如果条件不是 BinaryOperation 类型，它就是一个具体的变量或常数
            if condition.nodeType == "Literal":  # 常数
                return condition.value
            else:
                return condition.name

    # 获取条件表达式
    condition_expression = get_condition(while_Node.condition)
    return condition_expression


# 查询所有while语句
def find_While_and_If_Statement(node, while_nodes=None):
    if while_nodes is None:
        while_nodes = []
    try:
        if node.nodes:
            for element in node.nodes:
                if element.nodeType in ("WhileStatement", "IfStatement"):
                    if (
                        element.nodeType == "IfStatement"
                        and element.parent().nodeType == "WhileStatement"
                    ):
                        continue
                    while_nodes.append(element)
                # 递归调用自身，以便在子节点中查找更多的 WhileStatement
                find_While_and_If_Statement(element, while_nodes)
    except:
        return while_nodes

    return while_nodes

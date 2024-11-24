import logging
import random
from copy import copy
from collections import deque
from solcast.nodes import NodeBase

logger = logging.getLogger(__name__)

Index = 0


class CodeSegment:

    def __init__(self, state: int, next_state: int, body: list = []):
        self.state = state
        self.body = body
        self.next_state = next_state


class StateSegment(CodeSegment):

    def __init__(
        self,
        state: int,
        next_state: int,
        body: list = [],
        break_to: int | None = None,
        continue_at: int | None = None,
    ):
        super().__init__(state=state, next_state=next_state, body=body)
        if break_to is not None:
            self.break_to = break_to
        if continue_at is not None:
            self.continue_at = continue_at


class BasicBlock(CodeSegment):

    def __init__(
        self,
        state: int,
        next_state: int,
        body: list = [],
        cond: NodeBase | None = None,
        jump_state: int | None = None,
    ):
        super().__init__(state=state, next_state=next_state, body=body)
        if cond is not None:
            self.cond = cond
            self.jump_state = jump_state

    @staticmethod
    def of_ss(ss: StateSegment):
        return BasicBlock(state=ss.state, next_state=ss.next_state, body=ss.body)


class CFG:

    BRANCH_STMT = ("IfStatement", "ForStatement", "WhileStatement", "DoWhileStatement")
    STATE_LB = 1 << 127
    STATE_UB = (1 << 128) - 1

    def gen_state(self):
        state = self.rand.randint(CFG.STATE_LB, CFG.STATE_UB)
        while state in self.states:
            state = self.rand.randint(CFG.STATE_LB, CFG.STATE_UB)
        self.states.add(state)
        return state

    def __init__(self):
        self.seed = random.randint(CFG.STATE_LB, CFG.STATE_UB)
        self.rand = random.Random(x=self.seed)
        self.states = set()
        self.blocks = {}
        self.init_state = self.gen_state()
        self.end_state = self.gen_state()

    @staticmethod
    def gen_cfg(body: list):
        cfg = CFG()
        bfs_queue = deque(
            [StateSegment(body=body, state=cfg.init_state, next_state=cfg.end_state)]
        )

        while len(bfs_queue) > 0:
            ss: StateSegment = bfs_queue.popleft()
            continue_at = getattr(ss, "continue_at", default=None)
            break_to = getattr(ss, "break_to", default=None)

            for i in range(len(ss.body)):
                x = ss.body[i]

                if x.nodeType == "Continue":
                    if continue_at is None:
                        raise ValueError(
                            "A continue statement in non-loop environment, maybe the AST is broken??"
                        )
                    new_bb = BasicBlock(
                        body=ss.body[:i],
                        state=ss.state,
                        next_state=continue_at,
                    )
                    cfg.blocks[new_bb.state] = new_bb
                    break
                elif x.nodeType == "Break":
                    if break_to is None:
                        raise ValueError(
                            "A break statement in non-loop environment, maybe the AST is broken??"
                        )
                    new_bb = BasicBlock(
                        body=ss.body[:i],
                        state=ss.state,
                        next_state=break_to,
                    )
                    cfg.blocks[new_bb.state] = new_bb
                    break

                if x.nodeType in CFG.BRANCH_STMT:
                    # bfs on the final branch
                    if i == len(ss.body) - 1:
                        final_state = ss.next_state
                    else:
                        final_state = cfg.gen_state()
                        bfs_queue.append(
                            StateSegment(
                                body=ss.body[i + 1 :],
                                state=final_state,
                                next_state=ss.next_state,
                                continue_at=continue_at,
                                break_to=break_to,
                            )
                        )

                if x.nodeType == "IfStatement":
                    # bfs on the true branch
                    if len(x.trueBody) == 0:
                        true_state = final_state
                    else:
                        true_state = cfg.gen_state()
                        bfs_queue.append(
                            StateSegment(
                                body=x.trueBody,
                                state=true_state,
                                next_state=final_state,
                                continue_at=continue_at,
                                break_to=break_to,
                            )
                        )
                    if hasattr(x, "falseBody"):
                        # bfs on the false branch (if present)
                        if len(x.falseBody == 0):
                            false_state = final_state
                        else:
                            false_state = cfg.gen_state()
                            bfs_queue.append(
                                StateSegment(
                                    body=x.falseBody,
                                    state=false_state,
                                    next_state=final_state,
                                    continue_at=continue_at,
                                    break_to=break_to,
                                )
                            )
                        next_state = false_state
                    else:
                        next_state = final_state

                    new_bb = BasicBlock(
                        body=ss.body[:i],
                        state=ss.state,
                        next_state=next_state,
                        cond=x.condition,
                        jump_state=true_state,
                    )
                    cfg.blocks[new_bb.state] = new_bb
                    break
                elif x.nodeType == "ForStatement":
                    cond_state = cfg.gen_state()
                    true_state = cfg.gen_state()
                    bfs_queue.append(
                        StateSegment(
                            body=[*x.nodes, x.loopExpression],
                            state=true_state,
                            next_state=cond_state,
                            continue_at=continue_at,
                            break_to=break_to,
                        )
                    )

                    cond_bb = BasicBlock(
                        body=[],
                        state=cond_state,
                        next_state=final_state,
                        cond=x.condition,
                        jump_state=true_state,
                    )
                    cfg.blocks[cond_bb.state] = cond_bb

                    new_bb = BasicBlock(
                        body=[*ss.body[:i], x.initializationExpression],
                        state=ss.state,
                        next_state=cond_state,
                    )
                    cfg.blocks[new_bb.state] = new_bb
                elif x.nodeType.endswith("WhileStatement"):
                    cond_state = cfg.gen_state()
                    if len(x.nodes) == 0:
                        true_state = cond_state
                    else:
                        true_state = cfg.gen_state()
                        bfs_queue.append(
                            StateSegment(
                                body=x.nodes,
                                state=true_state,
                                next_state=cond_state,
                                continue_at=continue_at,
                                break_to=break_to,
                            )
                        )
                    cond_bb = BasicBlock(
                        body=[],
                        state=cond_state,
                        next_state=final_state,
                        cond=x.condition,
                        jump_state=true_state,
                    )
                    cfg.blocks[cond_bb.state] = cond_bb

                    if x.nodeType == "WhileStatement":
                        next_state = cond_state  # while
                    else:
                        next_state = true_state  # do-while

                    new_bb = BasicBlock(
                        body=ss.body[:i],
                        state=ss.state,
                        next_state=next_state,
                    )
                    cfg.blocks[new_bb.state] = new_bb
                    break
            else:
                bb = BasicBlock.of_ss(ss)
                cfg.blocks[bb.state] = bb

        return cfg


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
    while_Nodes = find_While_and_If_Statement(
        node[1],
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
            if1 = createIfStatement()
            binary_condition = {
                "left": f"state{statenumber}",
                "operator": "==",
                "right": child.index,
            }
            condition = createBinaryOperation(binary_condition)
            if1.condition = condition
            if1.fields.remove("falseBody")

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
                    trueBody.fields.remove("falseBody")
                else:
                    inner_falseBody = createEpression(
                        {"name": f"state{statenumber}", "value": str(jump_index2)},
                        trueBody,
                    )
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
                                trueBody.fields.remove("falseBody")
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
                            if1.trueBody = trueBody
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

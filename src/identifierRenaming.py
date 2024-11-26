import hashlib
import time
from solcast.nodes import NodeBase

GLOBAL_VARIABLES = {"block", "msg", "sender", "tx",
                    "abi", "require", "length", "push",
                    "this", "timestamp", "value", "transfer"} # 全局变量（不替换避免和用户自定义变量重名产生bug）
replacements = {} # 变量名字典（集中替换重复出现的变量）


# 使用SHA-1算法以变量名+时间为种子生成替换名
def sha1_hash(value: str) -> str:
    combined_value = f"{value}_{time.time()}"
    return hashlib.sha1(combined_value.encode()).hexdigest()


# 不合法的替换名前面加_使之合法
def make_valid_name(name: str) -> str:
    hashed = sha1_hash(name)

    # 以数字开头的不合法替换名
    if hashed[0].isdigit():
        # 前加_
        valid_name = '_' + hashed
    else:
        valid_name = hashed

    return valid_name


# 替换变量名
def renaming(node: NodeBase) -> NodeBase:
    # 使用栈来模拟递归
    stack = [node]
    processed_nodes = set()  # 用于跟踪已处理的节点

    # 遍历所有节点
    while stack:
        current_node = stack.pop()

        # 检查当前节点是否已经处理过
        if id(current_node) in processed_nodes:
            continue  # 如果已经处理过，跳过该节点

        # 将当前节点标记为已处理
        processed_nodes.add(id(current_node))

        # 检查当前节点的 nodeType
        if hasattr(current_node, 'nodeType'):
            if current_node.nodeType in ['ContractDefinition',
                                         'StructDefinition',
                                          'FunctionDefinition',
                                          'EventDefinition',
                                          'VariableDeclaration',
                                          'ModifierDeclaration',
                                          'IdentifierPath',
                                          'MemberAccess',
                                          'FunctionCall',
                                          'Identifier']:
                if hasattr(current_node, 'name'):
                    if current_node.name:
                        original_name = current_node.name

                        # 剔除其中的全局变量
                        if original_name not in GLOBAL_VARIABLES:
                            # 如果不在变量名字典中（第一次出现的变量名）
                            if original_name not in replacements:
                                # 生成替换名并加入变量名字典
                                replacements[original_name] = make_valid_name(original_name)

                            # 替换名称
                            current_node.name = replacements[original_name]

                elif hasattr(current_node, 'memberName'):
                    original_name = current_node.memberName

                    # 剔除其中的全局变量
                    if original_name not in GLOBAL_VARIABLES:
                        # 如果不在变量名字典中（第一次出现的变量名）
                        if original_name not in replacements:
                            # 生成替换名并加入变量名字典
                            replacements[original_name] = make_valid_name(original_name)

                        # 替换名称
                        current_node.memberName = replacements[original_name]

                elif hasattr(current_node, 'names'):
                        # 创建一个新的列表来存储原始名称
                        original_names = []
                        for name in current_node.names:
                            original_names.append(name)  # 将每个名称添加到列表中

                            # 对每个名称进行替换
                            # 剔除其中的全局变量
                            if name not in GLOBAL_VARIABLES:
                                # 如果不在变量名字典中（第一次出现的变量名）
                                if name not in replacements:
                                    # 生成替换名并加入变量名字典
                                    replacements[name] = make_valid_name(name)

                                # 替换名称
                                current_node.names[current_node.names.index(name)] = replacements[name]

        # 遍历当前节点的属性
        for attr in current_node.__dict__:
            child_node = getattr(current_node, attr)

            # 如果是节点对象，添加到栈中
            if isinstance(child_node, NodeBase):
                stack.append(child_node)

            # 如果是节点列表，添加列表中的每个节点到栈中
            elif isinstance(child_node, list):
                for item in child_node:
                    if isinstance(item, NodeBase):
                        stack.append(item)

    return node


# 变量名替换混淆
def obfuscate(node: NodeBase) -> NodeBase:
    # 替换变量名
    node = renaming(node)

    return node
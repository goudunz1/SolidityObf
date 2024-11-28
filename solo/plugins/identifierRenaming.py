import hashlib
import time

from ..solidity.nodes import *

GLOBAL_VARIABLES = {
    "block",
    "msg",
    "sender",
    "tx",
    "abi",
    "require",
    "length",
    "push",
    "this",
    "timestamp",
    "value",
    "transfer",
}  # ȫ�ֱ��������滻������û��Զ��������������bug��
replacements = {}  # �������ֵ䣨�����滻�ظ����ֵı�����


# ʹ��SHA-1�㷨�Ա�����+ʱ��Ϊ���������滻��
def sha1_hash(value: str) -> str:
    combined_value = f"{value}_{time.time()}"
    return hashlib.sha1(combined_value.encode()).hexdigest()


# ���Ϸ����滻��ǰ���_ʹ֮�Ϸ�
def make_valid_name(name: str) -> str:
    hashed = sha1_hash(name)

    # �����ֿ�ͷ�Ĳ��Ϸ��滻��
    if hashed[0].isdigit():
        # ǰ��_
        valid_name = "_" + hashed
    else:
        valid_name = hashed

    return valid_name


# �滻������
def renaming(node: NodeBase) -> NodeBase:
    # ʹ��ջ��ģ��ݹ�
    stack = [node]
    processed_nodes = set()  # ���ڸ����Ѵ����Ľڵ�

    # �������нڵ�
    while stack:
        current_node = stack.pop()

        # ��鵱ǰ�ڵ��Ƿ��Ѿ�������
        if id(current_node) in processed_nodes:
            continue  # ����Ѿ��������������ýڵ�

        # ����ǰ�ڵ���Ϊ�Ѵ���
        processed_nodes.add(id(current_node))

        # ��鵱ǰ�ڵ�� nodeTyp    # �滻������e
        if isinstance(current_node, NodeBase):
            if isinstance(current_node, (
                ContractDefinition,
                StructDefinition,
                FunctionDefinition,
                EventDefinition,
                VariableDeclaration,
                ModifierDefinition,
                IdentifierPath,
                MemberAccess,
                FunctionCall,
                Identifier,
            )):
                if hasattr(current_node, "name"):
                    if current_node.name:
                        original_name = current_node.name

                        # �޳����е�ȫ�ֱ���
                        if original_name not in GLOBAL_VARIABLES:
                            # ������ڱ������ֵ��У���һ�γ��ֵı�������
                            if original_name not in replacements:
                                # �����滻��������������ֵ�
                                replacements[original_name] = make_valid_name(
                                    original_name
                                )

                            # �滻����
                            current_node.name = replacements[original_name]

                elif hasattr(current_node, "memberName"):
                    original_name = current_node.memberName

                    # �޳����е�ȫ�ֱ���
                    if original_name not in GLOBAL_VARIABLES:
                        # ������ڱ������ֵ��У���һ�γ��ֵı�������
                        if original_name not in replacements:
                            # �����滻��������������ֵ�
                            replacements[original_name] = make_valid_name(original_name)

                        # �滻����
                        current_node.memberName = replacements[original_name]

                elif hasattr(current_node, "names"):
                    # ����һ���µ��б����洢ԭʼ����
                    original_names = []
                    for name in current_node.names:
                        original_names.append(name)  # ��ÿ���������ӵ��б���

                        # ��ÿ�����ƽ����滻
                        # �޳����е�ȫ�ֱ���
                        if name not in GLOBAL_VARIABLES:
                            # ������ڱ������ֵ��У���һ�γ��ֵı�������
                            if name not in replacements:
                                # �����滻��������������ֵ�
                                replacements[name] = make_valid_name(name)

                            # �滻����
                            current_node.names[current_node.names.index(name)] = (
                                replacements[name]
                            )

        # ������ǰ�ڵ������
        for attr in current_node.fields:
            child_node = getattr(current_node, attr)

            # ����ǽڵ�������ӵ�ջ��
            if isinstance(child_node, NodeBase):
                stack.append(child_node)

            # ����ǽڵ��б��������б��е�ÿ���ڵ㵽ջ��
            elif isinstance(child_node, list):
                for item in child_node:
                    if isinstance(item, NodeBase):
                        stack.append(item)

    return node


# �������滻����
def run(node: SourceUnit) -> SourceUnit:
    # �滻������
    node = renaming(node)

    return node

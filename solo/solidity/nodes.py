"""
This file is a augmented version of py-solcast/nodes.py

Author: Yu 'goudunz1' Sheng

The original license:

MIT License

Copyright (c) 2019 Ben Hauser

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
import itertools
import string

from copy import copy, deepcopy
from collections import deque
from typing import override, Generator, Iterable

logger = logging.getLogger(__name__)

AZaz09dollar_ = string.ascii_letters + string.digits + "$_"
AZazdollar_ = string.ascii_letters + "$_"


class NodeBase:

    def _bind(self, node: "NodeBase", key: str) -> "NodeBase":
        if node._parent is not self:
            if node._parent is not None:
                saved_parent, node._parent = node._parent, None
                temp = deepcopy(node)
                node._parent = saved_parent
                node = temp
            node._parent = self
            self._children[node] = key
        return node

    def _unbind(self, node: "NodeBase"):
        if node._parent is self:
            del self._children[node]
            node._parent = None

    class NodeList(list):

        @override
        def __init__(
            self, iterable: Iterable, parent: "NodeBase" = None, parent_key: str = ""
        ):
            self._parent = parent
            self._parent_key = parent_key
            super().__init__(
                (
                    self._parent._bind(v, self._parent_key)
                    if isinstance(v, NodeBase)
                    else v
                )
                for v in iterable
            )

        @override
        def __setitem__(self, key: int | slice, value: object):
            v = self.__getitem__(key)
            if isinstance(key, slice):  # when key is slice
                for x in v:
                    if isinstance(x, NodeBase):
                        self._parent._unbind(x)
            elif isinstance(v, NodeBase):
                self._parent._unbind(v)

            if isinstance(key, slice):  # when key is slice
                value = (
                    (
                        self._parent._bind(v, self._parent_key)
                        if isinstance(v, NodeBase)
                        else v
                    )
                    for v in value
                )
            elif isinstance(value, NodeBase):
                value = self._parent._bind(value, self._parent_key)
            return super().__setitem__(key, value)

        @override
        def __delitem__(self, key: int | slice):
            v = self.__getitem__(key)
            if isinstance(key, slice):  # when key is slice
                for x in v:
                    if isinstance(x, NodeBase):
                        self._parent._unbind(x)
            elif isinstance(v, NodeBase):
                self._parent._unbind(v)

            return super().__delitem__(key)

        @override
        def insert(self, index: int, object: object):
            if isinstance(object, NodeBase):
                object = self._parent._bind(object, self._parent_key)

            return super().insert(index, object)

        @override
        def append(self, object: object):
            if isinstance(object, NodeBase):
                object = self._parent._bind(object, self._parent_key)

            return super().append(object)

        @override
        def clear(self):
            for v in self:
                if isinstance(v, NodeBase):
                    self._parent._unbind(v)

            return super().clear()

        @override
        def extend(self, iterable: Iterable):
            return super().extend(
                (
                    self._parent._bind(v, self._parent_key)
                    if isinstance(v, NodeBase)
                    else v
                )
                for v in iterable
            )

        @override
        def pop(self, index: int = -1):
            v = self.__getitem__(index)
            if isinstance(v, NodeBase):
                self._parent._unbind(v)

            return super().pop(index)

        @override
        def remove(self, value: object):
            if isinstance(value, NodeBase):
                self._parent._unbind(value)

            return super().remove(value)

        @property
        def parent(self):
            return self._parent

        @property
        def parent_key(self):
            return self._parent_key

    """
    Represents a node within the solidity AST.

    Attributes:
        offset: Absolute source offsets as a (start, stop) tuple
        contract_id: Contract ID as given by the standard compiler JSON

        _fields: List of syntax attributes for this node
        _parent: Reference to the parent node in the AST
        _children: Dictionary with key pair {object : attribute_name}
    """

    def _setattr(self, name: str, value: object):
        if name not in self._fields:
            self.__dict__[name] = value
            return

        if name in self.__dict__:
            object = self.__dict__[name]
            if isinstance(object, NodeBase):
                self._unbind(object)
            elif isinstance(object, NodeBase.NodeList):
                for x in object:
                    if isinstance(x, NodeBase):
                        self._unbind(x)

        if isinstance(value, NodeBase):
            value = self._bind(value, name)
        elif isinstance(value, list):
            value = NodeBase.NodeList(value, parent=self, parent_key=name)

        self.__dict__[name] = value

    def __init__(self, **ast: dict):
        if "src" in ast:
            src: str = ast.pop("src")
            src = [int(i) for i in src.split(":")]
            self.offset = (src[0], src[0] + src[1])
            self.contract_id = src[2]
        else:
            self.offset = (0, 0)
            self.contract_id = -1

        self._fields: set = set()
        self._parent: "NodeBase" = None
        self._children: dict = {}

        self.__setattr__ = self._setattr

        for key, value in ast.items():
            if isinstance(value, (dict, list)):
                value = node_class_factory(ast=value)

            self._fields.add(key)
            self.__setattr__(key, value)

    def __repr__(self) -> str:
        repr_str = f"<{type(self).__name__}"
        if isinstance(self, IterableNodeBase):
            repr_str += " iterable"
        if "name" in self.__dict__ and "value" in self.__dict__:
            repr_str += f" {self.name} = {self.value}"
        else:
            for attr in ("name", "value", "absolutePath"):
                if attr in self.__dict__:
                    repr_str += f" {self.__dict__[attr]}"
            else:
                repr_str += " object"
        return f"{repr_str}>"

    def tokenize(self, sb: "SourceBuilder"):
        pass

    @property
    def children(self) -> dict:
        return self._children

    @property
    def parent(self) -> "NodeBase | None":
        return self._parent

    @property
    def fields(self) -> set:
        return self._fields


class IterableNodeBase(NodeBase):

    BODY_ATTR = "nodes"

    @property
    def main(self) -> NodeBase.NodeList:
        return self.__dict__[self.__class__.BODY_ATTR]

    @main.setter
    def main(self, value: object):
        return self.__setattr__(self.__class__.BODY_ATTR, value)

    def __getitem__(self, key: int) -> object:
        body: NodeBase.NodeList = self.__dict__[self.__class__.BODY_ATTR]
        return body.__getitem__(key)

    def __setitem__(self, key: int | slice, value: object):
        body: NodeBase.NodeList = self.__dict__[self.__class__.BODY_ATTR]
        return body.__setitem__(key, value)

    def __delitem__(self, key: int | slice):
        body: NodeBase.NodeList = self.__dict__[self.__class__.BODY_ATTR]
        return body.__delitem__(key)

    def __iter__(self) -> Iterable:
        return iter(self.__dict__[self.__class__.BODY_ATTR])

    def __len__(self) -> int:
        return len(self.__dict__[self.__class__.BODY_ATTR])

    def __contains__(self, object: object) -> bool:
        return object in self.__dict__[self.__class__.BODY_ATTR]


class SourceUnit(IterableNodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        if hasattr(self, "license"):
            sb.add("//SPDX-License-Identifier:").add(self.license).add("\n")
        sb.add_all(self.nodes)

    @property
    def functions(self) -> Generator:
        bfs_queue: deque = deque([self])  # BFS deque
        while len(bfs_queue) > 0:
            n = bfs_queue.popleft()
            if isinstance(n, (FunctionDefinition, ModifierDefinition)):
                yield n
            elif isinstance(n, (ContractDefinition, SourceUnit)):
                for decl in n:
                    bfs_queue.append(decl)

    @property
    def contracts(self) -> Generator:
        for decl in self:
            if isinstance(decl, ContractDefinition):
                yield decl


class PragmaDirective(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("pragma").add_all(self.literals).add_semi()


class ContractDefinition(IterableNodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        # abstract flag
        if self.abstract is True:
            # For interface and library this's always False
            sb.add("abstract")
        # interface, contract or library
        sb.add(self.contractKind).add(self.name)
        # inheritance
        if len(self.baseContracts) > 0:
            sb.add("is").add_tuple(self.baseContracts, format="")
        # contract body
        sb.add_blk(self.nodes)

    def functions(self) -> Generator:
        for n in self:
            if isinstance(n, (FunctionDefinition, ModifierDefinition)):
                yield n


class Block(IterableNodeBase):

    BODY_ATTR = "statements"

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add_blk(self.statements)


class InheritanceSpecifier(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.baseName)


class UserDefinedValueTypeDefinition(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("type").add(self.name).add("is").add(self.underlyingType).add_semi()


class FunctionDefinition(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        # constructor-definition
        if self.kind == "constructor":
            sb.add("constructor").add(self.parameters)
            # list of modifiers
            if len(self.modifiers) > 0:
                sb.add_all(self.modifiers)
            # state mutability, can only be "payable" for constructors
            if self.stateMutability == "payable":
                sb.add("payable")
            # Function body is a must for constructors
            sb.add(self.body)

        # function-definition
        elif self.kind == "function" or self.kind == "freeFunction":
            sb.add("function").add(self.name).add(self.parameters)
            # Visibility is meaningless for free functions
            # public, external, internal, etc.
            if self.kind != "freeFunction":
                sb.add(self.visibility)
            # state mutability
            # Do not visualize "nonpayable"
            if self.stateMutability != "nonpayable":
                sb.add(self.stateMutability)
            # list of modifiers
            if len(self.modifiers) > 0:
                sb.add_all(self.modifiers)
            # can be overridden?
            if self.virtual is True:
                sb.add("virtual")
            # overrides any prototype?
            if hasattr(self, "overrides"):
                sb.add(self.overrides)
            # return parameters
            if len(self.returnParameters) > 0:
                sb.add("returns").add(self.returnParameters)
            # function body, could be empty or not implemented
            if hasattr(self, "body"):
                sb.add(self.body)
            else:
                sb.add_semi()

        else:
            raise ValueError(f"Unknown function kind {self.kind}, please fix this!")


class ModifierInvocation(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.modifierName).add_tuple(self.arguments)


class OverrideSpecifier(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("override").add_tuple(self.overrides)


class ModifierDefinition(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("modifier").add(self.name).add(self.parameters)
        # can be overridden?
        if self.virtual is True:
            sb.add("virtual")
        # overrides any prototype?
        if hasattr(self, "overrides"):
            sb.add(self.overrides)
        # modifier body, could be empty or not implemented
        if hasattr(self, "body"):
            sb.add(self.body)
        else:
            sb.add_semi()


class ParameterList(IterableNodeBase):

    BODY_ATTR = "parameters"

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add_tuple(self.parameters)


class EventDefinition(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("event").add(self.name).add(self.parameters)
        # is it anonymous?
        if self.anonymous is True:
            sb.add("anonymous")
        sb.add_semi()


class ErrorDefinition(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("error").add(self.name).add(self.parameters).add_semi()


class EnumDefinition(IterableNodeBase):

    BODY_ATTR = "members"

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("enum").add(self.name).add_dict(values=self.members, keys=None)


class EnumValue(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.name)


class StructDefinition(IterableNodeBase):

    BODY_ATTR = "members"

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("struct").add(self.name).add_blk(self.members)


class VariableDeclaration(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        # state-variable-definition / constant-variable-definition
        if isinstance(self._parent, ContractDefinition) or isinstance(
            self._parent, SourceUnit
        ):
            # type of the member, it's also a node
            sb.add(self.typeName)
            # constant-variable-definition check
            if self.constant is True:
                sb.add("constant")
            # special attributes of state-variable-definition
            else:
                # public, private, internal, etc.
                # no need to visualize default value "internal"
                if hasattr(self, "visibility") and self.visibility != "internal":
                    sb.add(self.visibility)
                # immutable flag
                if self.mutability == "immutable":
                    sb.add("immutable")
                # state variable location, default or transient
                elif self.storageLocation != "default":
                    sb.add(self.storageLocation)
                # overrides any prototype?
                if hasattr(self, "overrides"):
                    sb.add(self.overrides)
            # name of the variable
            sb.add(self.name)
            # initial value
            # Note that transient state variable has no initial value
            if hasattr(self, "value"):
                sb.add("=").add(self.value)
            sb.add_semi()

        # struct-member
        elif isinstance(self._parent, StructDefinition):
            # type of the member, it's also a node
            # name of the member
            sb.add(self.typeName).add(self.name).add_semi()

        # parameter
        elif isinstance(self._parent, ParameterList):
            # type of the parameter, it's also a node
            sb.add(self.typeName)
            # indexed flag, for event parameter only
            if hasattr(self, "indexed") and self.indexed is True:
                sb.add("indexed")
            # parameter location, memory, storage, calldata, etc.
            if self.storageLocation != "default":
                sb.add(self.storageLocation)
            # name of the parameter
            # Rule out anonymous variables
            if len(self.name) > 0:
                sb.add(self.name)
            # We don't emit semicolons here

        # other cases, i.e. variable declaration statement
        else:
            # type of the variable, it's also a node
            sb.add(self.typeName)
            # variable location, memory, storage, calldata, etc.
            if self.storageLocation != "default":
                sb.add(self.storageLocation)
            # name of the variable
            sb.add(self.name)


class ElementaryTypeNameExpression(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.typeName)


class ElementaryTypeName(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        if hasattr(self, "stateMutability") and self.stateMutability == "payable":
            if isinstance(self._parent, ElementaryTypeNameExpression):
                # Handle address in expression differently, if its a payable
                # address, use 'payable' instead of 'address payable' as
                # specified in official documentation
                sb.add("payable")
            else:
                sb.add(self.name).add("payable")
        else:
            sb.add(self.name)


class UserDefinedTypeName(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.pathNode)


class ArrayTypeName(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        if hasattr(self, "length"):
            sb.add(self.baseType).add("[").add(self.length).add("]")
        else:
            sb.add(self.baseType).add("[]")


class IdentifierPath(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.name)


class Mapping(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("mapping")
        sb.add("(").add(self.keyType).add("=>").add(self.valueType).add(")")


class PlaceholderStatement(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("_").add_semi()


class VariableDeclarationStatement(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        if len(self.declarations) > 1:
            sb.add_tuple(self.declarations)
        else:
            sb.add(self.declarations[0])
        sb.add("=").add(self.initialValue)
        # Special case in for statement:
        # Variable declaration statement is used as an expression
        if not (
            isinstance(self._parent, ForStatement)
            and self is self._parent.initializationExpression
        ):
            sb.add_semi()


class ExpressionStatement(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.expression)
        # Special case in for statement:
        # Expression statement is used as an expression
        if not (
            isinstance(self._parent, ForStatement)
            and self is self._parent.loopExpression
        ):
            sb.add_semi()


class EmitStatement(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        # function sb.emit() has nothing to do with solidity's emit statement!
        sb.add("emit").add(self.eventCall).add_semi()


class RevertStatement(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("revert").add(self.errorCall).add_semi()


class IfStatement(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        # trueBody can be a block or a statement
        sb.add("if").add("(").add(self.condition).add(")").add(self.trueBody)
        # Check if else branch present
        if hasattr(self, "falseBody"):
            # falseBody can be a list of nodes or a normal node
            sb.add("else").add(self.falseBody)


class ForStatement(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("for").add("(").add(self.initializationExpression).add(";")
        sb.add(self.condition).add(";").add(self.loopExpression).add(")")
        sb.add(self.body)


class WhileStatement(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("while").add("(").add(self.condition).add(")").add(self.body)


class DoWhileStatement(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("do").add(self.body)
        sb.add("while").add("(").add(self.condition).add(")").add_semi()


class Return(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("return").add(self.expression).add_semi()


class Break(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("break").add_semi()


class TupleExpression(IterableNodeBase):

    BODY_ATTR = "components"

    @override
    def tokenize(self, sb: "SourceBuilder"):
        if self.isInlineArray is True:
            sb.add_tuple(self.components, format="[]")
        else:
            sb.add_tuple(self.components)


class Continue(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add("continue").add_semi()


class FunctionCall(IterableNodeBase):

    BODY_ATTR = "arguments"

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.expression)
        if len(self.names) > 0:
            sb.add("(").add_dict(values=self.arguments, keys=self.names).add(")")
        else:
            sb.add_tuple(self.arguments)


class MemberAccess(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.expression).add(".").add(self.memberName)


class IndexAccess(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.baseExpression).add("[").add(self.indexExpression).add("]")


class IndexRangeAccess(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.baseExpression).add("[")
        if hasattr(self, "startExpression"):
            sb.add(self.startExpression)
        sb.add(":")
        if hasattr(self, "endExpression"):
            sb.add(self.endExpression)
        sb.add("]")


class UnaryOperation(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.operator).add(self.subExpression)


class BinaryOperation(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.leftExpression).add(self.operator).add(self.rightExpression)


class Assignment(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.leftHandSide).add(self.operator).add(self.rightHandSide)


class Literal(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        # string literals, printable
        if self.kind == "string":
            sb.add(ascii(self.value))
        # string literals, non-printable
        elif self.kind == "unicodeString":
            sb.add("unicode").add(ascii(self.value))
        # hex string literals
        elif self.kind == "hexString":
            sb.add("hex").add('"%s"' % self.hexValue)
        # number literals
        elif self.kind == "number":
            sb.add(self.value)
            # Note that there could be a sub-denomination, i.e. 100 wei
            if hasattr(self, "subdenomination"):
                sb.add(self.subdenomination)
        # bool literals and any undefined literals goes here
        else:
            sb.add(self.value)


class Identifier(NodeBase):

    @override
    def tokenize(self, sb: "SourceBuilder"):
        sb.add(self.name)


def node_class_factory(ast):
    if isinstance(ast, dict):
        if "nodeType" not in ast:
            # ast is a normal dict instead of an AST
            return ast

        node_type = ast.pop("nodeType")

        if node_type not in globals():
            # raise NotImplementedError(f"Node of type {node_type} isn't supported yet!")
            logger.warning(f"Node of type {node_type} isn't supported yet!")
            return NodeBase(**ast)

        return globals()[node_type](**ast)

    elif isinstance(ast, list):
        return [node_class_factory(ast=a) for a in ast]

    return ast


class SourceBuilder:

    def __init__(self, verbose=False, indent=0):
        self.tokens: list = []
        self.cache: deque = deque()
        self.verbose = verbose
        self.indent = indent

        if verbose is True:
            self.x_semicolon = ";\n"
            self.x_comma = ",\n"
            self.x_left_big_brace = "{\n"
            self.x_right_big_brace = "}\n"
        else:
            self.x_semicolon = ";"
            self.x_comma = ","
            self.x_left_big_brace = "{"
            self.x_right_big_brace = "}"

    def _make(self, token: str):
        if len(self.tokens) >= 1:
            last = self.tokens[-1]
            if token[0] in AZaz09dollar_ and last[-1] in AZaz09dollar_:
                self.tokens.append(" ")
        self.tokens.append(token)

    def add(self, item: str | NodeBase) -> "SourceBuilder":
        self.cache.appendleft(item)
        return self

    def add_all(self, items: list) -> "SourceBuilder":
        self.cache.extendleft(items)
        return self

    def add_semi(self) -> "SourceBuilder":
        self.cache.appendleft(self.x_semicolon)
        return self

    def add_blk(self, body: list) -> "SourceBuilder":
        self.cache.extendleft((self.x_left_big_brace, *body, self.x_right_big_brace))
        return self

    def add_tuple(self, elements: list, format: str = "()") -> "SourceBuilder":
        if len(elements) > 0:
            temp = [","] * ((len(elements) << 1) - 1)
            temp[0::2] = elements
        else:
            temp = []
        if len(format) == 2:
            self.cache.extendleft((format[0], *temp, format[1]))
        else:
            self.cache.extendleft(temp)
        return self

    def add_dict(self, values: list, keys: list | None = None) -> "SourceBuilder":
        if len(values) == 0:
            temp = []
        elif keys is not None:
            temp = [self.x_comma] * ((len(keys) << 2) - 1)
            temp[0::4] = keys
            temp[1::4] = itertools.repeat(":", times=len(keys))
            temp[2::4] = values
        else:
            temp = [self.x_comma] * ((len(values) << 1) - 1)
            temp[0::2] = values

        if self.verbose is True:
            temp.append("\n")

        self.cache.extendleft((self.x_left_big_brace, *temp, self.x_right_big_brace))
        return self

    def build(self, root: NodeBase) -> str:
        logger.debug("Converting syntax tree to source")
        # To speed up pre-order visiting, we use stack-based iteration instead of
        # recursion.
        pre_ord_stack = [root]  # pre-order traverse stack
        shift = 0  # indent level iff. indent is on
        new_line = False  # new line flag, iff. indent is on

        while len(pre_ord_stack) > 0:
            x = pre_ord_stack.pop()
            # Pure string value, should send it directly to tokens
            if isinstance(x, str):
                # iff. indent is on
                if self.verbose is True:
                    if x == self.x_left_big_brace:
                        shift += self.indent
                    elif x == self.x_right_big_brace:
                        shift -= self.indent
                    if new_line is True:
                        if shift > 0:
                            self._make(" " * shift)
                        new_line = False
                    if x.endswith("\n"):
                        new_line = True
                self._make(x)
            # a node
            # We need to split it into tokens and subnodes and put 'em back to stack
            elif isinstance(x, NodeBase):
                x.tokenize(sb=self)
                pre_ord_stack.extend(self.cache)
                self.cache.clear()
            # Undefined behaviors goes here
            else:
                logger.error(
                    f"Bad node {x}! Maybe the node is missing some key attributes?"
                )

        result = "".join(self.tokens)
        self.tokens.clear()
        return result

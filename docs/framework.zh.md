# 框架文档.zh

`py-solc-ast`拓展性有点差，并且有性能问题，框架把它重写了

在新的框架下，现有的模块仅需100～200行就可搞定

P.S. `py-solc-ast`原先会将属性为`body`的`Block`节点给去掉，转化为一个节点列表，并改名为
`nodes`，所以现在对于函数等含有`body`的语句，大致的结构为

```
FunctionDefinition.body -> Block
FunctionDefinition.body.statements -> Block.statements -> [...]
```

## 流程

`main()` -> `obfuscator.Obfuscator().run()` -> `plugins.*.run()`
-> `solidity.nodes.SourceBuilder().build()`

## 参数

`python -m solo [-h] [--version] [--verbose] [--output out.sol] filepath [--jobs [{rename,const,bogus,dfo,cff} ...]]`

- `--verbose` 开启缩进和 DEBUG 日志
- `--output` 规定输出文件，否则输出为`[filename].out.sol`
- `--jobs` 规定使用的模块，该模块必须要在`__main__.py`中注册开启，如下：
  - rename: `identifierRenaming.py`
  - dfo: `dataFlowObfuscation.py`
  - cff: `controlFlowFlatten.py`
  - const: `opaqueConstants.py`
  - bogus: `opaquePredicates.py`

P.S. 至于为啥要用这么多缩写是因为打字起来太烦了。。。模块名字我也用了缩写

## 生成新的节点

框架的辅助函数都位于`solidity/*.py`

`nodes.py` 主要负责树节点对象的创建以及源码的转换，例如，如果想要创建一个无根空子树

```solidity
if(x) {
    return y;
} else {
    return z;
}
```

你需要

```py
node = IfStatement(
    condition=Identifier(name="x"),
    trueBody=Block(statements=[
        Return(expression=Identifier(name="y"))
    ]),
    falseBody=Block(statements=[
        Return(expression=Identifier(name="z"))
    ]),
)
```

是不是很方便？无需费力写AST字典了，内部的父子关系全都会自动设置好

如果你觉得还是有点麻烦，可以试试`utils.py`里的工具函数，例如

```solidity
x+y
```

可以这样生成

```py
node = ADD(SYM(x), SYM(y))
```

## 改变当前的节点

之所以之前的版本中难以挂靠节点，本质上是因为设置父子关系不方便，
现在的框架支持自动设置这两者，只需

```py
if_statement_node.cond = cond_node
```

如果属性是个列表怎么办？还是一样！框架甚至可以自动搜寻列表并设置父子关系

```py
block_node.statements = [var_dec_node, var_dec_node, return_node]
```

如果不使用赋值而是列表的成员函数呢？也一样！简而言之，可以将节点的类型为列表的属性当作
正常列表一样使用

```py
struct_node.members.insert(var_dec_node)
```

当然，你可能会觉得不同的节点使用不同的列表属性，不方便记忆

没关系，对于主体为列表的节点，直接使用`node.main`!

```py
source_unit_node.main is source_unit_node.nodes
block_node.main is block_node.body
struct_node.main is struct_node.members
# ...
```

在`utils.py`中，还有一个函数`replace_with()`，可以无缝将当前节点替换为新的节点，
维护所有的父子关系

## 节点的固定成员

* `node.fields` 在AST树上，节点的全部子属性
* `node.parent` 节点的父节点，如果将一个有父节点的节点挂靠到别的父节点上，框架将会深度拷贝之，请小心这里的性能问题
* `node.children` 一个字典，键为子节点，值为该子节点位于父节点的哪个属性上

对于主体为列表的节点，可以将它当作可迭代元素使用，例如

```py
for statement_node in block_node:
    pass
```

P.S. `FunctionDefinition`不是这样的节点，`FunctionDefinition.body`这个`Block`节点才是！类似的还有`IfStatement`，`ForStatement`等这类含有`body`的节点

对于`SourceUnit`节点，有两个生成器成员，分别为`functions`和`contracts`，不用再费力写
BFS查找啦

```py
for func_node in source_unit_node.functions:
    pass
```

对于`ContractDefinition`节点，也有一个生成器成员`functions`

也可以添加其它节点的生成器成员，只要不与其原来的属性重名即可，给一个参考原型

```py
    @property
    def functions(self) -> "Generator[FunctionDefinition]":
        bfs_queue: deque = deque([self])  # BFS deque
        while len(bfs_queue) > 0:
            n = bfs_queue.popleft()
            if isinstance(n, (FunctionDefinition, ModifierDefinition)):
                yield n
            elif isinstance(n, (ContractDefinition, SourceUnit)):
                for decl in n:
                    bfs_queue.append(decl)
```

## 添加新的模块

请将模块仿照`__main__.py`里的`plugins`注册命令行参数，并且在`plugins`文件夹下创建模块

模块没有别的要求，只需定义一个`run()`函数，如下

```py
def run(node: SourceUnit) -> SourceUnit:
    pass
```

导入辅助工具模块的方法

```py
from ..solidity.nodes import *
from ..solidity.utils import *
from .opaqueConstants import random_name
# ...
```

## 添加新的节点支持

只需将新的节点定义为`node.py`中的类并继承`NodeBase`

如果想开启可迭代功能和`main`成员，请继承
`IterableNodeBase`并复写成员`BODY_ATTR`为该节点的主体列表名字，如

```py
class Block(IterableNodeBase):

    BODY_ATTR = "statements"
    
    # ...
```

另外，请复写`tokenize`函数，其原型为

```py
def tokenize(self, sb: SourceBuilder):
    pass
```

从而使得节点可以被转化为源代码

`SourceBuilder`的API如下

* `add(item)` 添加一个新的token，可以是字符串或者节点
* `add_all(items)` 添加列表中的所有token
* `add_semi()` 添加一个分号，在调试模式下会有换行和缩进
* `add_blk(body)` 以块模式（左右花括号）添加一个列表，在调试模式下会有换行和缩进
* `add_tuple(elements, format="()")` 以元组模式添加一个列表，可以规定元组使用的括号样式
* `add_dict(values, names=None)`
  以字典模式添加一个列表，如果`names`为列表，则输出键值对模式的字典，注意`names`（如果有）要和`values`一样长

请按语法顺序调用上面的API，可以连续调用哦，如

```py
sb.add(node.typeName).add(node.name).add_semi()
```

无需考虑缩进，换行和空格，这些框架都会自动做好

import logging
import random
from copy import copy
from collections import deque
from solcast.nodes import NodeBase

logger = logging.getLogger(__name__)

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

    def add_bb(
        self,
        state: int,
        next_state: int,
        body: list = [],
        cond: NodeBase | None = None,
        jump_state: int | None = None,
    ):
        if state in self.blocks:
            raise ValueError("Conflict state, check it again")

        if state not in self.states:
            raise ValueError("Unknown state, check it again")

        self.blocks[state] = BasicBlock(
            state=state,
            next_state=next_state,
            body=body,
            cond=cond,
            jump_state=jump_state,
        )

    def get_bb(self, state):
        return self.blocks[state]

    @staticmethod
    def gen_cfg(body: list):
        cfg = CFG()
        bfs_queue = deque(
            [StateSegment(body=body, state=cfg.init_state, next_state=cfg.end_state)]
        )

        while len(bfs_queue) > 0:
            ss: StateSegment = bfs_queue.popleft()
            continue_at = getattr(ss, "continue_at", None)
            break_to = getattr(ss, "break_to", None)

            for i in range(len(ss.body)):
                x = ss.body[i]

                # Jump out statements
                if x.nodeType == "Continue":
                    if continue_at is None:
                        raise ValueError(
                            "A continue statement in non-loop environment, maybe the AST is broken??"
                        )
                    cfg.add_bb(state=ss.state, next_state=continue_at, body=ss.body[:i])
                    break
                elif x.nodeType == "Break":
                    if break_to is None:
                        raise ValueError(
                            "A break statement in non-loop environment, maybe the AST is broken??"
                        )
                    cfg.add_bb(state=ss.state, next_state=break_to, body=ss.body[:i])
                    break

                # Do BFS on the final branch if present
                # Otherwise, the final state should be ss's next state
                if x.nodeType in CFG.BRANCH_STMT:
                    if i == len(ss.body) - 1:
                        final_state = ss.next_state
                    else:
                        final_state = cfg.gen_state()
                        bfs_queue.append(
                            StateSegment(
                                state=final_state,
                                next_state=ss.next_state,
                                body=ss.body[i + 1 :],
                                continue_at=continue_at,
                                break_to=break_to,
                            )
                        )

                if x.nodeType == "IfStatement":
                    # Do BFS on the true branch
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

                    # Do BFS on the false branch if present
                    if hasattr(x, "falseBody") and len(x.falseBody) > 0:
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
                    else:
                        false_state = final_state

                    cfg.add_bb(
                        body=ss.body[:i],
                        state=ss.state,
                        next_state=false_state,
                        cond=x.condition,
                        jump_state=true_state,
                    )

                    break

                elif x.nodeType == "ForStatement":
                    cond_state = cfg.gen_state()
                    loop_state = cfg.gen_state()

                    true_state = cfg.gen_state()
                    bfs_queue.append(
                        StateSegment(
                            state=true_state,
                            next_state=loop_state,
                            body=[*x.nodes, x.loopExpression],
                            continue_at=loop_state,
                            break_to=final_state,
                        )
                    )

                    # Add the beginning block
                    cfg.add_bb(
                        state=ss.state,
                        next_state=cond_state,
                        body=[*ss.body[:i], x.initializationExpression],
                    )

                    # Add the condition block
                    cfg.add_bb(
                        state=cond_state,
                        next_state=final_state,
                        cond=x.condition,
                        jump_state=true_state,
                    )

                    # Add the loop block, eg. i+=1
                    cfg.add_bb(
                        state=loop_state, next_state=cond_state, body=[x.loopExpression]
                    )

                    break

                elif x.nodeType.endswith("WhileStatement"):
                    # Pre-compute state of the condition block
                    cond_state = cfg.gen_state()

                    # Do BFS on while body
                    if len(x.nodes) == 0:
                        true_state = cond_state
                    else:
                        true_state = cfg.gen_state()
                        bfs_queue.append(
                            StateSegment(
                                state=true_state,
                                next_state=cond_state,
                                body=x.nodes,
                                continue_at=cond_state,
                                break_to=final_state,
                            )
                        )

                    # Add the beginning block
                    if x.nodeType == "WhileStatement":  # while
                        cfg.add_bb(
                            state=ss.state, next_state=cond_state, body=ss.body[:i]
                        )
                    else:  # do-while
                        cfg.add_bb(
                            state=ss.state, next_state=true_state, body=ss.body[:i]
                        )

                    # Add the condition block (*body* is empty)
                    cfg.add_bb(
                        state=cond_state,
                        next_state=final_state,
                        cond=x.condition,
                        jump_state=true_state,
                    )

                    break
            else:
                cfg.add_bb(ss.state, ss.next_state, body=ss.body)

        return cfg

def obfuscate(node: NodeBase) -> NodeBase:

    logger.debug(f"Applying CFF on {node}")


    # traverse the ast to insert opaque predicates

    bfs_queue = deque([node])  # BFS deque
    while len(bfs_queue) > 0:

        n = bfs_queue.popleft()

        if n.nodeType in ("FunctionDefinition", "ModifierDefinition"):
            if hasattr(n, "nodes"):
                cfg = CFG.gen_cfg(n.nodes)

                # Purge function body
                for x in n.nodes:
                    n._children.remove(x)
                    x._parent = None
                n.nodes = []

                s_name = random_name()
                s_dec_stmt = ast_var_dec_stmt(name=s_name, value=cfg.init_state)

                if_list = []
                for state in cfg.blocks:
                    cond = ast_eq(ast_id(s_name), ast_num(state))
                    if_list.append(ast_if_stmt(cond=cond, true_body=[])) # true body to be filled

                exit_cond = ast_ne(ast_id(s_name), ast_num(cfg.end_state))
                while_stmt = ast_while_stmt(cond=exit_cond, body=if_list, do=False)

                as_node(n, ast=while_stmt, at="nodes", list_idx=0)
                as_node(n, ast=s_dec_stmt, at="nodes", list_idx=0)
        
        if n.nodeType in ("ContractDefinition", "SourceUnit"):
            for child in n._children:
                bfs_queue.append(child)
    
    logger.debug("CFF done!")


    return node
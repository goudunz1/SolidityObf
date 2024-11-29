import logging
import random
from copy import copy
from typing import Iterable

from ..solidity.nodes import *
from ..solidity.utils import *
from .opaqueConstants import random_name

logger = logging.getLogger(__name__)


class StateBlock:

    def __init__(self, state: int, next_state: int, body: Iterable = []):
        self.state = state
        self.body = list(body)
        self.next_state = next_state


class StateSegment(StateBlock):

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


class BasicBlock(StateBlock):

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

    BRANCH_STMT = (IfStatement, ForStatement, WhileStatement, DoWhileStatement)
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
        self.blocks: dict[int, BasicBlock] = {}
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

    def get_bb(self, state: int):
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
                if isinstance(x, Continue):
                    if continue_at is None:
                        raise ValueError(
                            "A continue statement in non-loop environment, maybe the AST is broken??"
                        )
                    cfg.add_bb(state=ss.state, next_state=continue_at, body=ss.body[:i])
                    break
                elif isinstance(x, Break):
                    if break_to is None:
                        raise ValueError(
                            "A break statement in non-loop environment, maybe the AST is broken??"
                        )
                    cfg.add_bb(state=ss.state, next_state=break_to, body=ss.body[:i])
                    break

                # Do BFS on the final branch if present
                # Otherwise, the final state should be ss's next state
                if isinstance(x, CFG.BRANCH_STMT):
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

                if isinstance(x, IfStatement):
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

                elif isinstance(x, ForStatement):
                    cond_state = cfg.gen_state()
                    loop_state = cfg.gen_state()

                    true_state = cfg.gen_state()
                    bfs_queue.append(
                        StateSegment(
                            state=true_state,
                            next_state=loop_state,
                            body=[*x.body, x.loopExpression],
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

                elif isinstance(x, (WhileStatement, DoWhileStatement)):
                    # Pre-compute state of the condition block
                    cond_state = cfg.gen_state()

                    # Do BFS on while body
                    if len(x.body) == 0:
                        true_state = cond_state
                    else:
                        true_state = cfg.gen_state()
                        bfs_queue.append(
                            StateSegment(
                                state=true_state,
                                next_state=cond_state,
                                body=x.body,
                                continue_at=cond_state,
                                break_to=final_state,
                            )
                        )

                    # Add the beginning block
                    if isinstance(x, WhileStatement):  # while
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


def run(node: SourceUnit) -> SourceUnit:

    # for test
    sb = SourceBuilder()

    logger.debug(f"Applying CFF on {node}")

    # traverse the ast to insert opaque predicates
    for func in node.functions:
        if hasattr(func, "body"):
            body: Block = func.body
            cfg = CFG.gen_cfg(body)

            state_name = random_name()
            state_stmt = EVAR("uint", state_name, cfg.init_state, stmt=True)
            exit_cond = NE(SYM(state_name), NUM(cfg.end_state))

            switch_body = []
            for state in cfg.blocks:
                if state == cfg.end_state:
                    continue

                bb = cfg.blocks[state]
                case_body = copy(bb.body)
                if hasattr(bb, "cond"):
                    state_update = IF(
                        cond=bb.cond,
                        true_body=ASSIGN(SYM(state_name), NUM(bb.jump_state)),
                        false_body=ASSIGN(SYM(state_name), NUM(bb.next_state)),
                    )
                else:
                    state_update = ASSIGN(SYM(state_name), NUM(bb.next_state))
                case_body.append(state_update)
                case_body.append(Continue())

                case_cond = EQ(SYM(state_name), NUM(state))
                switch_body.append(IF(cond=case_cond, true_body=BLK(case_body)))

            while_stmt = WHILE(cond=exit_cond, body=BLK(switch_body), do=False)
            body.main = [state_stmt, while_stmt]

    logger.debug("CFF done!")

    return node

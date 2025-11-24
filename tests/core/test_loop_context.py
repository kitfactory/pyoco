import pytest

from pyoco.core.context import Context, LoopFrame, LoopStack


def test_loop_stack_push_pop_and_paths():
    stack = LoopStack()
    frame1 = stack.push(LoopFrame(name="outer", type="repeat", index=0))
    assert frame1.path == "outer[0]"
    frame2 = stack.push(LoopFrame(name="inner", type="foreach", index=3))
    assert frame2.path == "outer[0].inner[3]"
    assert stack.current is frame2
    popped = stack.pop()
    assert popped is frame2
    assert stack.current is frame1


def test_context_exposes_loop_properties():
    ctx = Context()
    ctx.push_loop(LoopFrame(name="outer", type="repeat"))
    assert ctx.loop.name == "outer"
    ctx.push_loop(LoopFrame(name="inner", type="foreach", index=1))
    assert len(ctx.loops) == 2
    ctx.pop_loop()
    ctx.pop_loop()
    with pytest.raises(RuntimeError):
        ctx.pop_loop()

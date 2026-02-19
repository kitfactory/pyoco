import pytest

from pyoco.dsl.spike_parser import (
    DSLSyntaxSpikeError,
    ForEachTerm,
    PipeRefTerm,
    RepeatTerm,
    SwitchTerm,
    TaskTerm,
    UntilTerm,
    parse_pipeline_spike,
    tokenize_spike,
)


def test_tokenize_spike_supports_template_and_blocks():
    tokens = tokenize_spike("switch(on={{k}}){A: B; default: C;} >> Z")
    kinds = [t.kind for t in tokens]
    assert "TEMPLATE" in kinds
    assert "LBRACE" in kinds
    assert "RBRACE" in kinds
    assert "SHIFT" in kinds


def test_parse_spike_full_pipeline():
    graph = """
    A
    >> switch(on={{k}}){
         B: pipe(BX);
         C: "C >> Z";
         default: Warn;
       }
    >> repeat(count=3, collect=list){
         pipe(BX)
       }
    >> foreach(over={{items}}, item=it, index=i, collect=list){
         pipe(ProcessOne)
         >> switch(on={{it_kind}}){
              image: ImgTask;
              text: TxtTask;
              default: Skip;
            }
       }
    >> until(cond={{done}}, max_iter=20, collect=last){
         Train >> Validate
       }
    >> AFTER
    """
    parsed = parse_pipeline_spike(graph)
    assert len(parsed.terms) == 6
    assert isinstance(parsed.terms[0], TaskTerm)
    assert isinstance(parsed.terms[1], SwitchTerm)
    assert isinstance(parsed.terms[2], RepeatTerm)
    assert isinstance(parsed.terms[3], ForEachTerm)
    assert isinstance(parsed.terms[4], UntilTerm)
    assert isinstance(parsed.terms[5], TaskTerm)

    switch_term = parsed.terms[1]
    assert switch_term.on == "{{k}}"
    assert [c.value for c in switch_term.cases] == ["B", "C"]
    assert switch_term.default is not None
    quoted_case = switch_term.cases[1].branch
    assert [t.name for t in quoted_case.terms if isinstance(t, TaskTerm)] == ["C", "Z"]

    repeat_term = parsed.terms[2]
    assert repeat_term.count == "3"
    assert repeat_term.collect == "list"
    assert isinstance(repeat_term.body.terms[0], PipeRefTerm)

    foreach_term = parsed.terms[3]
    assert foreach_term.over == "{{items}}"
    assert foreach_term.item == "it"
    assert foreach_term.index == "i"
    assert foreach_term.collect == "list"

    until_term = parsed.terms[4]
    assert until_term.cond == "{{done}}"
    assert until_term.max_iter == "20"
    assert until_term.collect == "last"


def test_parse_spike_rejects_single_gt():
    with pytest.raises(DSLSyntaxSpikeError) as exc:
        parse_pipeline_spike("A > B")
    assert "Use '>>' only" in str(exc.value)


def test_parse_spike_rejects_unterminated_template():
    with pytest.raises(DSLSyntaxSpikeError) as exc:
        tokenize_spike("switch(on={{k){A: B;}")
    assert "Unterminated template expression" in str(exc.value)


def test_parse_spike_handles_nested_control_terms():
    graph = """
    repeat(count=2){
      switch(on={{mode}}){
        alpha: foreach(over={{items}}, item=it){ pipe(P1) >> TaskX };
        default: until(cond={{done}}, max_iter=3){ TaskY };
      }
    }
    """
    parsed = parse_pipeline_spike(graph)
    assert len(parsed.terms) == 1
    repeat_term = parsed.terms[0]
    assert isinstance(repeat_term, RepeatTerm)
    inner = repeat_term.body.terms[0]
    assert isinstance(inner, SwitchTerm)
    assert len(inner.cases) == 1
    assert inner.default is not None


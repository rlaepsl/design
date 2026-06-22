"""Pipeline 오케스트레이션 동작 테스트."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code", "pipeline-orchestration"))

from pipeline import Pipeline, Stage  # noqa: E402


def _ok_stage(name):
    return Stage(name, "Test", run=lambda ctx: {"v": 1}, gate=lambda out: [])


def test_all_pass_completes():
    pipe = Pipeline([_ok_stage("a"), _ok_stage("b")])
    result = pipe.execute({"job": "x"})
    assert result.ok is True
    assert result.halted_at is None
    assert [t.stage for t in result.trace] == ["a", "b"]


def test_failing_gate_halts_after_max_attempts():
    bad = Stage("bad", "Test", run=lambda ctx: {"v": 1}, gate=lambda out: ["always_fails"])
    pipe = Pipeline([_ok_stage("a"), bad, _ok_stage("c")], max_attempts=3)
    result = pipe.execute({"job": "x"})
    assert result.ok is False
    assert result.halted_at == "bad"
    # 'bad' 단계는 3회 시도 후 중단, 'c'는 실행되지 않음
    bad_attempts = [t for t in result.trace if t.stage == "bad"]
    assert len(bad_attempts) == 3
    assert all(t.stage != "c" for t in result.trace)


def test_retry_then_succeed():
    state = {"n": 0}

    def run(ctx):
        state["n"] += 1
        return {"n": state["n"]}

    def gate(out):
        return [] if out["n"] >= 2 else ["not_ready"]   # 1회 실패 후 통과

    pipe = Pipeline([Stage("retry", "Test", run, gate)], max_attempts=3)
    result = pipe.execute({"job": "x"})
    assert result.ok is True
    retry_traces = [t for t in result.trace if t.stage == "retry"]
    assert len(retry_traces) == 2
    assert retry_traces[0].passed is False
    assert retry_traces[1].passed is True


def test_context_passed_between_stages():
    produce = Stage("produce", "Test", run=lambda ctx: {"items": [1, 2, 3]}, gate=lambda out: [])
    consume = Stage("consume", "Test",
                    run=lambda ctx: {"count": len(ctx["produce"]["items"])},
                    gate=lambda out: [] if out["count"] == 3 else ["wrong_count"])
    pipe = Pipeline([produce, consume])
    result = pipe.execute({"job": "x"})
    assert result.ok is True
    assert result.context["consume"]["count"] == 3

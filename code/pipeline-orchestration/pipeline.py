#!/usr/bin/env python3
"""
pipeline.py — 멀티에이전트 파이프라인 + 검증 게이트 (구조 데모)

디자인 자동화 파이프라인의 핵심 골격을 공개용으로 재현한다.

    analyze  →  plan  →  produce  →  verify

각 단계는 서로 다른 '에이전트'가 맡고, 단계 사이의 '게이트'가 산출물을 점검한다.
게이트를 통과하지 못하면 같은 단계를 재시도하고(피드백 전달), 끝내 실패하면 멈춘다.

핵심 아이디어:
  - 역할 분리   — 하나의 거대한 AI가 아니라, 단계별 전담 + 단계간 계약(contract)
  - 품질 게이트 — 통과하지 못한 산출물은 다음 단계로 넘어가지 못한다
  - 추적성     — 모든 단계/재시도/게이트 결과를 trace로 남긴다

실제 시스템에서는 각 단계가 Gemini / Codex / Claude 이고, 게이트는 결정론적 검증 하네스다.
이 데모는 회사/고객 데이터 없이 '구조'만 보여준다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Stage:
    """파이프라인 한 단계: 담당 에이전트 + 실행 함수 + 게이트 함수."""
    name: str
    agent: str                              # 담당 (표시용: Gemini/Codex/Claude/Harness)
    run: Callable[[dict], dict]             # 컨텍스트 -> 산출물
    gate: Callable[[dict], list[str]]       # 산출물 -> 이슈 목록(빈 리스트면 통과)


@dataclass
class StepTrace:
    stage: str
    agent: str
    attempt: int
    passed: bool
    issues: list[str]


@dataclass
class PipelineResult:
    ok: bool
    context: dict
    trace: list[StepTrace] = field(default_factory=list)
    halted_at: Optional[str] = None


class Pipeline:
    """단계들을 순서대로 실행하며, 게이트 실패 시 재시도/중단을 관리한다."""

    def __init__(self, stages: list[Stage], max_attempts: int = 3):
        self.stages = stages
        self.max_attempts = max_attempts

    def execute(self, job: dict) -> PipelineResult:
        ctx: dict = dict(job)
        result = PipelineResult(ok=True, context=ctx)

        for stage in self.stages:
            passed = False
            for attempt in range(1, self.max_attempts + 1):
                output = stage.run(ctx)
                issues = stage.gate(output)
                result.trace.append(
                    StepTrace(stage.name, stage.agent, attempt, not issues, issues)
                )
                if not issues:
                    ctx[stage.name] = output            # 계약: 다음 단계로 전달
                    passed = True
                    break
                # 게이트 실패 → 피드백을 남겨 재시도에 반영
                ctx.setdefault("_feedback", {})[stage.name] = issues

            if not passed:
                result.ok = False
                result.halted_at = stage.name           # 통과 못하면 다음 단계로 안 넘어간다
                return result

        return result


# --------------------------------------------------------------------------
# 데모: 가짜 '포스터 제작' 작업을 흘려보낸다. (produce 단계가 1회 실패 후 재시도 성공)
# --------------------------------------------------------------------------
def _demo() -> None:
    VALID_LABELS = {"관찰", "출처확인", "추론", "확인 필요", "제안"}

    def analyze_run(ctx):
        return {"observations": [
            {"text": "제목이 자료에 표시됨", "label": "관찰", "source": "SRC-1"},
            {"text": "대비로 보아 제목 강조 의도", "label": "추론", "source": "SRC-1"},
        ]}

    def analyze_gate(out):
        issues = []
        for o in out["observations"]:
            if o["label"] not in VALID_LABELS:
                issues.append(f"invalid_label:{o['label']}")
            if o["label"] not in {"확인 필요", "제안"} and not o.get("source"):
                issues.append(f"missing_source:{o['text'][:8]}")
        return issues

    def plan_run(ctx):
        obs = ctx["analyze"]["observations"]
        return {"goal": "여름 캠페인 포스터", "uses_sources": [o["source"] for o in obs if o.get("source")]}

    def plan_gate(out):
        return [] if out.get("uses_sources") else ["plan_has_no_source_reference"]

    attempts = {"produce": 0}

    def produce_run(ctx):
        attempts["produce"] += 1
        elements = [{"type": "path"}, {"type": "text"}]
        if attempts["produce"] == 1:
            elements.append({"type": "raster"})   # 무손실 원칙 위반(첫 시도) → 게이트가 잡는다
        return {"elements": elements}

    def produce_gate(out):
        rasters = [e for e in out["elements"] if e["type"] == "raster"]
        return [f"raster_present:{len(rasters)}"] if rasters else []

    def verify_run(ctx):
        return {"final": True, "element_count": len(ctx["produce"]["elements"])}

    def verify_gate(out):
        return [] if out.get("final") else ["not_finalized"]

    pipe = Pipeline([
        Stage("analyze", "Gemini", analyze_run, analyze_gate),
        Stage("plan", "Codex", plan_run, plan_gate),
        Stage("produce", "Claude", produce_run, produce_gate),
        Stage("verify", "Harness", verify_run, verify_gate),
    ])

    result = pipe.execute({"job": "poster"})
    print(f"=> 파이프라인 {'PASS ✅' if result.ok else 'FAIL ❌ (halted at ' + str(result.halted_at) + ')'}\n")
    for t in result.trace:
        flag = "✅" if t.passed else "❌"
        extra = "" if t.passed else f"  issues={t.issues}"
        print(f"  {flag} {t.stage:<8} [{t.agent:<7}] attempt {t.attempt}{extra}")


if __name__ == "__main__":
    _demo()

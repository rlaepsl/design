# pipeline-orchestration — 멀티에이전트 + 검증 게이트 (데모)

이 프로젝트의 **심장**입니다. 디자인 자동화를 하나의 거대한 AI에게 맡기지 않고,
단계별 전담 에이전트 + 단계 사이의 검증 게이트로 나눠 처리하는 골격을 재현합니다.

```
analyze ─▶ plan ─▶ produce ─▶ verify
(Gemini)  (Codex)  (Claude)   (Harness)
   └────────── 게이트 실패 시 재시도 / 중단 ──────────┘
```

## 설계

| 개념 | 구현 |
|---|---|
| **역할 분리** | 각 `Stage` 가 담당 에이전트 + 실행 함수를 가진다 |
| **품질 게이트** | 각 단계의 `gate()` 가 산출물을 점검 — 통과 못하면 다음 단계로 못 감 |
| **재시도 + 피드백** | 게이트 실패 시 이슈를 컨텍스트에 남겨 같은 단계를 다시 실행 |
| **중단** | `max_attempts` 안에 통과 못하면 `halted_at` 으로 멈춤 |
| **추적성** | 모든 단계·재시도·게이트 결과를 `trace` 로 남김 |

## 실행

```bash
python pipeline.py
```

```
=> 파이프라인 PASS ✅

  ✅ analyze  [Gemini ] attempt 1
  ✅ plan     [Codex  ] attempt 1
  ❌ produce  [Claude ] attempt 1  issues=['raster_present:1']   ← 무손실 원칙 위반
  ✅ produce  [Claude ] attempt 2                                ← 피드백 반영 후 재시도 성공
  ✅ verify   [Harness] attempt 1
```

`produce` 단계가 첫 시도에 래스터를 포함해 게이트에 걸리고, 피드백을 받아 두 번째 시도에서
통과하는 **재시도 루프**를 그대로 보여줍니다.

> 실제 시스템에서는 각 단계가 Gemini / Codex / Claude 이고, 게이트는 결정론적 검증 하네스입니다.
> 이 데모는 회사/고객 데이터 없이 구조만 보여줍니다.

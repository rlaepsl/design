# 코드 데모

이 폴더의 코드는 메인 README에서 설명한 **멀티에이전트 AI 디자인 자동화 파이프라인**의
핵심 기법을 **공개용으로 새로 작성한 실행 가능한 독립 예제**입니다.

> ⚠️ 회사/고객 자료는 포함하지 않습니다. 실제 운영 코드가 아니라, 같은 엔지니어링 아이디어를
> 누구나 읽고 실행할 수 있도록 최소 예제로 재작성한 것입니다.

파이프라인 흐름 순서대로:

| # | 폴더 | 보여주는 역량 | 실행 |
|---|---|---|---|
| 1 | [`pipeline-orchestration/`](pipeline-orchestration/) | **역할 분리 + 검증 게이트 + 재시도** — 프로젝트의 골격 | `python pipeline.py` |
| 2 | [`data-contract/`](data-contract/) | 단계 사이 **입력 계약(학습표) 스키마 + 검증기** | `python validate_learning_table.py --csv sample_learning_table.csv` |
| 3 | [`illustrator-automation/`](illustrator-automation/) | Python+ExtendScript로 **Illustrator 직접 구동** + 앵커-패리티 검증 | `python run_extract.py --name 로고 --mock` |
| 4 | [`claim-verification/`](claim-verification/) | **출처 라벨링**으로 환각을 결정론적으로 차단 | `python verify_claims.py --claims sample_claims.jsonl` |

설계 사상은 [`../docs/`](../docs/) 에 정리되어 있습니다.
테스트는 [`../tests/`](../tests/) (15종), 푸시마다 GitHub Actions로 실행됩니다.

# 학습표 스키마 (learning table schema)

학습표는 **분석 단계 → 제작 단계** 사이의 입력 계약(CSV)입니다.
각 행이 하나의 부품을 정의합니다: *"어느 소스의 / 어느 영역을 / 어떻게 추출할지."*

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `part_id` | string | 부품 고유 ID (비어있지 않음, 중복 금지) |
| `name` | string | 사람이 읽는 부품 이름 |
| `category` | string | 분류 (예: `logo`, `picto`, `template`) |
| `source_name` | string | 소스 파일 식별자 (확장자 없음) |
| `norm_basis` | string | 정규화 기준. `design_bounds`(디자인 경계) 권장 |
| `nx`, `ny` | float [0,1] | 영역 좌상단 좌표 (정규화) |
| `nw`, `nh` | float [0,1] | 영역 폭/높이 (정규화). `nx+nw ≤ 1`, `ny+nh ≤ 1` |
| `recurse_flag` | bool | 하위 그룹까지 재귀 수집 여부 (`true`/`false`) |
| `color_mode` | enum | `as_is` \| `light_on_dark` (어두운 배경용 흰 요소) |
| `text_handling` | enum | `include` \| `exclude` (텍스트 프레임 포함 여부) |
| `notes` | string | 비고 (선택) |

## 정규화 좌표 규약

- 원점 = 좌상단, y는 아래로 증가 (이미지 좌표계와 동일)
- 기준 = **디자인 경계(design_bounds)** — 아트보드가 아니라 실제 그려진 내용의 union
- 0~1 범위로 정규화하므로 소스 해상도/크기와 무관하게 같은 영역을 가리킨다

검증: [`validate_learning_table.py`](validate_learning_table.py) 가 이 계약을 강제한다.

# data-contract — 단계 사이의 입력 계약 + 검증기 (데모)

멀티에이전트 파이프라인에서 **단계와 단계는 '계약'으로 연결**됩니다. 분석 단계가 만든
구조화된 표(학습표)를 제작 단계가 받아 부품을 추출하는데, 잘못된 표가 들어가면 추출이
깨집니다. 그래서 **단계 사이에서 입력을 먼저 검증**합니다.

## 파일

| 파일 | 역할 |
|---|---|
| [`learning_table_schema.md`](learning_table_schema.md) | 학습표 컬럼/타입/규약 정의 |
| `validate_learning_table.py` | 스키마 계약 검증기 (결정론적) |
| `sample_learning_table.csv` | 합성 샘플 (고객/회사 데이터 없음) |

## 검사 항목

- 필수 컬럼 존재, `part_id` 비어있지 않음 + 중복 없음
- 정규화 좌표 `nx, ny, nw, nh` 가 0~1 실수이고 경계를 안 벗어남
- `recurse_flag` 가 `true/false`, `color_mode`·`text_handling` 가 허용된 값

## 실행

```bash
python validate_learning_table.py --csv sample_learning_table.csv
```

```
verdict : pass
rows    : 3
  (모든 행이 계약을 통과)
```

이 표가 [`../illustrator-automation/`](../illustrator-automation/) 의 추출기를 구동하는 입력입니다.

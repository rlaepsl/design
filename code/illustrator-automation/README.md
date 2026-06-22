# illustrator-automation — AI가 일러스트레이터를 직접 구동 (데모)

사람이 Adobe Illustrator를 손으로 클릭하던 반복 작업을 **Python + ExtendScript로 자동화**하고,
결과물의 무결성을 **사람 눈이 아니라 결정론적 지표**로 검증하는 데모입니다.

## 무엇을 보여주나

소스 `.ai`에서 이름이 붙은 그룹을 찾아 새 문서로 **네이티브 복제**(.ai→.ai, SVG 왕복 없음)하고,
복제 전/후 **앵커(정점) 수가 1:1로 일치**하는지, **래스터가 0**인지 검증합니다.

### 왜 "앵커 패리티(anchor parity)"인가

벡터를 SVG로 내보냈다 다시 들여오면(왕복) 패스가 근사화되어 앵커 수가 바뀌거나 래스터가 끼어듭니다.
`소스 앵커수 == 결과 앵커수` 이고 `raster == 0` 이면 **무손실 네이티브 추출**이 수학적으로 보장됩니다.

## 파일

| 파일 | 역할 |
|---|---|
| `run_extract.py` | Python 오케스트레이터 — 사본 생성, JSX 주입, `win32com`으로 Illustrator 구동, JSON 리포트 판정 |
| `anchor_parity.jsx` | Illustrator 내부에서 실행되는 ExtendScript — 그룹 탐색·앵커 합산·네이티브 복제·패리티 판정 |

## 설계 원칙

- **원본 무수정** — 코드 수준에서 강제 (사본만 열고, JSX는 `DONOTSAVECHANGES`)
- **SVG 왕복 금지** — `pageItem.duplicate(targetDoc, PLACEATEND)` 네이티브 복제만
- **검증 자동화** — PASS/FAIL을 앵커수·래스터수로 결정 (사람 검수 의존 제거)

## 실행

```bash
# 요구사항: Windows + Adobe Illustrator + pywin32
python run_extract.py --source path/to/source.ai --name 로고 --out ./out
```

```
group        : 로고  (found=True)
src anchors  : 214
out anchors  : 214
raster       : 0
parity_match : True
raster_zero  : True
=> PASS ✅ (무손실 네이티브 추출)
```

> 입력 `.ai` 파일은 회사 자료 보호를 위해 포함하지 않습니다(데모 코드만 공개).
> 이 코드는 제 개인 프로젝트에서 쓰는 기법을 공개용으로 새로 작성한 것입니다.

"""
run_extract.py — Python에서 Adobe Illustrator를 직접 구동하는 자동화 데모 (Windows COM)

흐름:
  1) 소스 .ai를 스크래치 사본으로 복사 (원본 보호)
  2) anchor_parity.jsx 에 경로/그룹명을 주입
  3) win32com 으로 Illustrator 애플리케이션을 띄워 DoJavaScript 실행
  4) JSX 가 남긴 JSON 리포트를 읽어 앵커-패리티 PASS/FAIL 판정

핵심 아이디어:
  - 사람이 일러스트레이터를 손으로 클릭하던 반복 작업을, AI/스크립트가 그대로 수행한다.
  - "원본 무수정"을 코드 수준에서 강제한다 (사본만 열고, JSX는 DONOTSAVECHANGES).
  - 결과물의 무결성을 사람 눈이 아니라 결정론적 지표(앵커수 == 1:1, raster == 0)로 검증한다.

사용:
  python run_extract.py --source path/to/source.ai --name 로고 --out ./out

요구사항: Windows + Adobe Illustrator + pywin32 (win32com).
  ※ 입력 .ai 는 회사 자료 보호를 위해 이 저장소에 포함하지 않습니다(데모 코드만 공개).

이 파일은 제 개인 프로젝트에서 쓰는 기법을 공개용으로 새로 작성한 데모입니다.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def build_jsx(source_copy: str, name: str, ai_out: str, outdir: str) -> str:
    """JSX 템플릿의 플레이스홀더를 실제 값으로 치환해 실행용 JSX를 만든다."""
    template = os.path.join(HERE, "anchor_parity.jsx")
    with open(template, "r", encoding="utf-8") as fp:
        jsx = fp.read()
    jsx = (
        jsx.replace("__SOURCE__", source_copy.replace("\\", "/"))
           .replace("__NAME__", name)
           .replace("__AI_OUT__", ai_out.replace("\\", "/"))
           .replace("__OUTDIR__", outdir.replace("\\", "/"))
    )
    run_jsx = os.path.join(outdir, "_run_parity.jsx")
    with open(run_jsx, "w", encoding="utf-8") as fp:
        fp.write(jsx)
    return run_jsx


def main() -> int:
    parser = argparse.ArgumentParser(description="Illustrator 그룹 추출 + 앵커-패리티 검증 데모")
    parser.add_argument("--source", help="소스 .ai 경로 (--mock 시 생략 가능)")
    parser.add_argument("--name", required=True, help="추출할 그룹 이름")
    parser.add_argument("--out", default=os.path.join(HERE, "out"), help="출력 폴더")
    parser.add_argument("--mock", action="store_true",
                        help="Illustrator 없이 합성 리포트로 판정 흐름만 시연(크로스플랫폼)")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    report_path = os.path.join(args.out, "parity.json")

    if args.mock:
        # Illustrator/Windows 없이 판정 로직만 시연한다
        print("[MOCK] Illustrator 미사용 — 합성 리포트로 판정 흐름만 보여줍니다.")
        report = {"name": args.name, "found": True, "src_anchors": 214,
                  "out_anchors": 214, "raster": 0, "parity_match": True,
                  "raster_zero": True, "ok": True, "error": None}
    else:
        if not args.source or not os.path.exists(args.source):
            print(f"FAIL: source 없음: {args.source}  (Illustrator 없이 보려면 --mock)")
            return 1

        # 1) 원본 보호 — 스크래치 사본만 연다
        scratch = os.path.join(args.out, "_scratch")
        os.makedirs(scratch, exist_ok=True)
        source_copy = os.path.join(scratch, "_src_" + os.path.basename(args.source))
        shutil.copy2(args.source, source_copy)
        ai_out = os.path.join(args.out, f"{args.name}.ai")

        # 2) 실행용 JSX 생성
        run_jsx = build_jsx(source_copy, args.name, ai_out, args.out)
        if os.path.exists(report_path):
            os.remove(report_path)

        # 3) win32com 으로 Illustrator 구동 (Windows 전용)
        try:
            import win32com.client
        except ImportError:
            print("이 데모는 Windows + Illustrator + pywin32 환경에서 실행됩니다.")
            print("(흐름만 보려면 --mock 옵션을 쓰세요.)")
            print(f"생성된 실행 JSX: {run_jsx}")
            return 2

        app = win32com.client.Dispatch("Illustrator.Application")
        try:
            with open(run_jsx, "r", encoding="utf-8") as fp:
                app.DoJavaScript(fp.read())
        except Exception as exc:  # JSX 비동기 — 결과 파일로 확인
            print("DoJavaScript 예외(결과 파일로 확인):", exc)

        # 4) JSX 가 남긴 JSON 리포트 폴링
        for _ in range(120):
            if os.path.exists(report_path):
                break
            time.sleep(1)

        if not os.path.exists(report_path):
            print("WARN: parity.json 미생성 — Illustrator 화면/오류 수동 확인.")
            return 1
        with open(report_path, "r", encoding="utf-8") as fp:
            report = json.load(fp)

    print(f"group        : {report.get('name')}  (found={report.get('found')})")
    print(f"src anchors  : {report.get('src_anchors')}")
    print(f"out anchors  : {report.get('out_anchors')}")
    print(f"raster       : {report.get('raster')}")
    print(f"parity_match : {report.get('parity_match')}")
    print(f"raster_zero  : {report.get('raster_zero')}")
    print(f"=> {'PASS ✅ (무손실 네이티브 추출)' if report.get('ok') else 'FAIL ❌'}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

/*
 * anchor_parity.jsx — Adobe Illustrator ExtendScript 데모
 *
 * 개념: 소스 .ai에서 이름이 붙은 그룹을 찾아 새 문서로 "네이티브 복제"(.ai→.ai,
 *   SVG 왕복 없음)하고, 복제 전/후의 앵커(정점) 수가 1:1로 일치하는지 검증한다.
 *
 * 왜 앵커 패리티(anchor parity)인가:
 *   벡터를 SVG로 내보냈다 다시 들여오면(왕복) 패스가 근사화되어 앵커 수가 바뀌거나
 *   래스터 이미지가 끼어든다. "소스 앵커수 == 결과 앵커수" 이고 "raster == 0" 이면
 *   무손실 네이티브 추출이 수학적으로 보장된다. 이것이 품질 게이트의 판정 기준.
 *
 * 안전 원칙: 원본은 절대 저장하지 않는다 (열기 → DONOTSAVECHANGES).
 *
 * 경로/이름은 Python 러너(run_extract.py)가 주입한다:
 *   __SOURCE__   소스 .ai 사본의 절대경로
 *   __NAME__     추출할 그룹 이름
 *   __AI_OUT__   추출 결과 .ai 저장 경로
 *   __OUTDIR__   리포트(JSON) 출력 폴더
 *
 * 이 파일은 제 개인 프로젝트에서 쓰는 기법을 공개용으로 새로 작성한 데모입니다.
 */
#target illustrator

/* ---------- 미니 JSON 인코더 (ExtendScript엔 JSON 전역이 없다) ---------- */
function jsonEnc(v) {
    if (v === null || v === undefined) return "null";
    var t = typeof v;
    if (t == "number") return isFinite(v) ? String(v) : "null";
    if (t == "boolean") return String(v);
    if (t == "string") return '"' + v.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n") + '"';
    if (v instanceof Array) {
        var a = [];
        for (var i = 0; i < v.length; i++) a.push(jsonEnc(v[i]));
        return "[" + a.join(",") + "]";
    }
    if (t == "object") {
        var p = [];
        for (var k in v) if (v.hasOwnProperty(k)) p.push(jsonEnc(k) + ":" + jsonEnc(v[k]));
        return "{" + p.join(",") + "}";
    }
    return "null";
}

function writeText(path, txt) {
    var f = new File(path);
    f.encoding = "UTF-8";
    f.open("w");
    f.write(txt);
    f.close();
}

/* ---------- 앵커수: 컨테이너를 재귀로 합산 (1:1 패리티 지표) ---------- */
function anchorsOf(item) {
    var tn = item.typename;
    if (tn == "PathItem") return item.pathPoints.length;
    if (tn == "CompoundPathItem") {
        var s = 0;
        for (var i = 0; i < item.pathItems.length; i++) s += item.pathItems[i].pathPoints.length;
        return s;
    }
    if (tn == "GroupItem") {
        var s = 0;
        for (var i = 0; i < item.pageItems.length; i++) s += anchorsOf(item.pageItems[i]);
        return s;
    }
    return 0; // TextFrame / RasterItem / PlacedItem 은 앵커 없음
}

/* ---------- leaf 종류별 통계 (raster 검출용) ---------- */
function tally(item, acc) {
    var tn = item.typename;
    if (tn == "GroupItem") {
        for (var i = 0; i < item.pageItems.length; i++) tally(item.pageItems[i], acc);
        return acc;
    }
    acc.leaves++;
    acc.anchors += anchorsOf(item);
    if (tn == "RasterItem" || tn == "PlacedItem") acc.raster++;
    return acc;
}
function newAcc() { return { leaves: 0, anchors: 0, raster: 0 }; }

/* ---------- 이름으로 그룹 찾기 ---------- */
function findNamedGroup(doc, name) {
    for (var li = 0; li < doc.layers.length; li++) {
        var lyr = doc.layers[li];
        for (var gi = 0; gi < lyr.groupItems.length; gi++) {
            if (String(lyr.groupItems[gi].name) === name) return lyr.groupItems[gi];
        }
    }
    return null;
}

function main() {
    var report = { ok: false, name: "__NAME__", found: false,
                   src_anchors: 0, out_anchors: 0, raster: 0,
                   parity_match: false, raster_zero: false, error: null };
    var src = null;
    try {
        var sf = new File("__SOURCE__");
        if (!sf.exists) { report.error = "SOURCE_NOT_FOUND"; writeText("__OUTDIR__/parity.json", jsonEnc(report)); return; }

        src = app.open(sf);                          // 원본 사본을 연다 (저장 안 함)
        var group = findNamedGroup(src, "__NAME__");
        if (!group) { report.error = "GROUP_NOT_FOUND: __NAME__"; src.close(SaveOptions.DONOTSAVECHANGES); writeText("__OUTDIR__/parity.json", jsonEnc(report)); return; }
        report.found = true;

        var srcAcc = tally(group, newAcc());
        report.src_anchors = srcAcc.anchors;

        // 네이티브 복제: pageItem.duplicate(targetDoc, PLACEATEND). SVG 왕복 없음.
        var dst = app.documents.add(DocumentColorSpace.RGB);
        var dup = group.duplicate(dst.layers[0], ElementPlacement.PLACEATEND);

        var outAcc = tally(dup, newAcc());
        report.out_anchors = outAcc.anchors;
        report.raster = outAcc.raster;

        // 결과만 .ai로 저장 (소스는 건드리지 않는다)
        var aiOpt = new IllustratorSaveOptions();
        try { aiOpt.compatibility = Compatibility.ILLUSTRATOR17; } catch (e) {}
        dst.saveAs(new File("__AI_OUT__"), aiOpt);

        // 판정: 소스 앵커수 == 결과 앵커수 && raster == 0
        report.parity_match = (report.src_anchors === report.out_anchors);
        report.raster_zero  = (report.raster === 0);
        report.ok = report.parity_match && report.raster_zero;

        src.close(SaveOptions.DONOTSAVECHANGES);     // 원본 사본: 저장 없이 닫기
    } catch (e) {
        report.error = e.toString() + " @line " + (e.line || "?");
        try { if (src) src.close(SaveOptions.DONOTSAVECHANGES); } catch (e2) {}
    }
    writeText("__OUTDIR__/parity.json", jsonEnc(report));
}
main();

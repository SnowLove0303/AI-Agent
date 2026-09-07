#!/usr/bin/env python3
"""Mechanical source-fact extractor for the unified MSDS pipeline (v3.15).

Business role: the overwrite core is *extract -> standardize (CN) -> render
CN -> translate EN from the standardized model*.  This module does the first
mechanical step only: it reads a nonstandard source DOCX and produces a
standardized CN semantic draft plus an explicit human/agent review queue.

Mechanical (deterministic, auditable) vs review (judgment needed):

* AUTO: S1 supplier block verbatim; S3 component rows split into
  name/CAS/content; S4-S7 label/value pairs verbatim; S9 property rows
  verbatim with missing-sentinel marking; S10/S12-S16 endpoint rows verbatim;
  S2 H/P coded-statement segmentation (regex); embedded-image inventory.
* REVIEW: model fallback to filename; S3 multi-line misalignment; label
  ingredient phrasing variants; S2 per-route synthesis; S9 ambiguous
  missing-vs-applicability wording; S11 endpoint mapping (incl. the
  主要粘膜刺激性 alias), multi-study splits, combined 生殖毒性 splits,
  STOT/overall synthesis; any table whose row count differs from the
  expected nonstandard shape.

Output JSON shape (sections mirror the generator fact shape)::

    {"model": ..., "source_sha256": ...,
     "sections": {"s1": [[label, value], ...], ...},
     "review": [{"section": ..., "issue": ..., "detail": ...}],
     "images": [{"name": ..., "size": ...}]}

Values use ``\\n``-joined logical lines; missing sentinels are kept verbatim
(the build stage applies the omission policy).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from section2_hp_policy import _CODE_RE, is_missing_data_value, split_coded_statements  # noqa: E402

try:
    from docx import Document
except ImportError:  # pragma: no cover
    Document = None


MODEL_RE = re.compile(r"\b([A-Z]{1,4}-\d{3,4}[A-Z0-9]*)\b")
CAS_RE = re.compile(r"\b\d{2,7}-\d{2}-\d\b")
LABEL_INGREDIENT_RE = re.compile(r"(列在标签上|有害成分|label)")
SIGNAL_RE = re.compile(r"信号词\s*[：:]\s*(.*)")
CATEGORY_RE = re.compile(r"(类别\s*\S*|\(H\d+[a-zA-Z]*\))")
MISSING_HINT_RE = re.compile(r"(无适用资料|无数据资料|暂无|未提供|不详)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_cells(row):
    out, seen = [], set()
    for cell in row.cells:
        key = id(cell._tc)
        if key not in seen:
            seen.add(key)
            out.append(cell)
    return out


def _clean(text: str) -> str:
    return re.sub(r"[\t\u3000]+", " ", text or "").strip()


def cell_lines(cell) -> list[str]:
    parts = []
    for paragraph in cell.paragraphs:
        text = _clean(paragraph.text)
        if text:
            parts.append(text)
    return parts


def row_texts(table, index) -> list[str]:
    return [_clean(" / ".join(cell_lines(cell))) for cell in unique_cells(table.rows[index])]


class Extraction:
    def __init__(self):
        self.review: list[dict] = []

    def flag(self, section: str, issue: str, detail: str = "") -> None:
        self.review.append({"section": section, "issue": issue, "detail": detail})


def extract_s1(table, ext: Extraction) -> list:
    rows = []
    for index in range(1, len(table.rows)):
        cells = row_texts(table, index)
        label = cells[0] if cells else ""
        value = cells[1] if len(cells) > 1 else ""
        rows.append([label, value])
    return rows


def extract_model(table, source: Path, ext: Extraction) -> str:
    if len(table.rows) > 1:
        cells = row_texts(table, 1)
        if len(cells) > 1 and cells[1].strip():
            return cells[1].strip()
    match = MODEL_RE.search(source.name)
    if match:
        ext.flag("s1", "model-from-filename", match.group(1))
        return match.group(1)
    ext.flag("s1", "model-missing", "no model in S1 value or filename")
    return ""


def extract_s2(table, ext: Extraction) -> dict:
    """Split the merged S2 cell into classified logical lines."""
    text = "\n".join(
        paragraph.text.strip()
        for row in table.rows[1:]
        for cell in unique_cells(row)
        for paragraph in cell.paragraphs
        if paragraph.text.strip()
    )
    lines = [line.strip() for line in re.split(r"[\r\n]+", text) if line.strip()]
    out = {"ghs_classes": [], "h_statements": [], "p_statements": [],
           "signal": "", "label_ingredients": [], "other": [], "raw_lines": lines}
    for index, line in enumerate(lines):
        signal = SIGNAL_RE.search(line)
        if signal:
            out["signal"] = signal.group(1).strip()
            continue
        if LABEL_INGREDIENT_RE.search(line):
            ingredient = re.split(r"[:：]", line, maxsplit=1)
            tail = ingredient[1].strip() if len(ingredient) > 1 else ""
            if not tail and index + 1 < len(lines):
                # Required output pattern keeps the ingredient on the next
                # line; accept it only when the next line carries no code.
                follower = lines[index + 1]
                if not _CODE_RE.search(follower):
                    tail = follower
            if tail:
                out["label_ingredients"].append(tail)
            else:
                ext.flag("s2", "label-ingredient-phrasing",
                         f"ingredient line without explicit value: {line[:60]}")
            continue
        if "类别" in line:
            # GHS classification lines stay whole; code-splitting them would
            # shred "类别 3 (H226)" into fragments.
            out["ghs_classes"].append(line)
            continue
        codes = split_coded_statements(line)
        if codes and any(re.match(r"^[HP]|EUH", code) for code in codes):
            for code in codes:
                (out["p_statements"] if code.startswith("P") else out["h_statements"]).append(code)
            continue
        if CATEGORY_RE.search(line) and ("类别" in line or "H3" in line or "H2" in line):
            out["ghs_classes"].append(line)
            continue
        if MISSING_HINT_RE.search(line):
            out["other"].append(line)
            ext.flag("s2", "ambiguous-missing-wording", line[:80])
            continue
        out["other"].append(line)
    if not out["label_ingredients"]:
        ext.flag("s2", "label-ingredients-absent",
                 "no explicit label-ingredient line; generator will suppress the row")
    if not out["signal"]:
        ext.flag("s2", "signal-missing",
                 "no explicit signal word in source; confirm before writing")
    ext.flag("s2", "per-route-synthesis",
             "draft 2.8 per-route rows from H codes; confirm wording")
    return out


def extract_pairs(table, ext: Extraction, section: str) -> list:
    rows = []
    for index in range(1, len(table.rows)):
        cells = row_texts(table, index)
        label = cells[0] if cells else ""
        value = cells[1] if len(cells) > 1 else ""
        rows.append([label, value])
    return rows


def extract_s3(table, ext: Extraction) -> list:
    rows = []
    for index in range(1, len(table.rows)):
        cells = unique_cells(table.rows[index])
        texts = [" / ".join(cell_lines(cell)) for cell in cells]
        rows.append(texts)
    data = [row for row in rows[3:] if any(cell.strip() for cell in row)]
    split_rows = []
    for row in data:
        columns = [[part.strip() for part in cell.split(" / ") if part.strip()] for cell in row]
        width = max((len(column) for column in columns), default=0)
        if width > 1 and not all(len(column) == width for column in columns):
            ext.flag("s3", "component-misalignment", " / ".join(row)[:80])
        for item in range(width):
            split_rows.append([
                columns[0][item] if item < len(columns[0]) else "",
                columns[1][item] if len(columns) > 1 and item < len(columns[1]) else "",
                columns[2][item] if len(columns) > 2 and item < len(columns[2]) else "",
            ])
    for row in split_rows:
        if row[1] and row[1] != "商业机密" and not CAS_RE.search(row[1]):
            ext.flag("s3", "cas-format", " / ".join(row)[:80])
    return rows[:3] + split_rows


def extract_s9(table, ext: Extraction) -> list:
    rows = []
    for index in range(1, len(table.rows)):
        cells = row_texts(table, index)
        label = cells[0] if cells else ""
        value = cells[1] if len(cells) > 1 else ""
        entry: dict = {"label": label, "value": value}
        if is_missing_data_value(value):
            entry["omit"] = True
        elif MISSING_HINT_RE.search(value):
            entry["omit"] = True
            ext.flag("s9", "ambiguous-missing-wording", f"{label}: {value[:60]}")
        rows.append(entry)
    return rows


def extract_s11(table, ext: Extraction) -> list:
    """Keep endpoint rows verbatim; split multi-study blocks for review."""
    rows = []
    for index in range(1, len(table.rows)):
        cells = row_texts(table, index)
        rows.append(cells)
    for cells in rows:
        joined = " / ".join(cells)
        if cells and ("粘膜刺激" in joined):
            ext.flag("s11", "alias-mucosa-to-eye",
                     "route source 主要粘膜刺激性 to 11.3; preserve value")
        if len([part for part in re.split(r"物种\s*[：:]", joined)]) > 2:
            ext.flag("s11", "multi-study-block", joined[:80])
        if "生殖毒性" in joined and ("生育" in joined or "胚胎" in joined or "致畸" in joined):
            ext.flag("s11", "repro-split",
                     "split combined reproductive text into fertility/teratogenicity/in-vitro")
    if len(rows) < 5:
        ext.flag("s11", "thin-source", f"only {len(rows)} endpoint rows")
    return rows


def extract_images(source: Path) -> list[dict]:
    found = []
    with zipfile.ZipFile(source) as archive:
        for name in sorted(archive.namelist()):
            if name.startswith("word/media/") and not name.endswith("/"):
                found.append({"name": Path(name).name, "size": len(archive.read(name))})
    return found


def coverage_fingerprint(document, sections: dict) -> dict:
    """Prove no source character goes missing: every non-empty source line
    (whitespace-normalized) must appear in the extracted sections dump,
    except R0 section headings which are template structure by design."""
    corpus = re.sub(r"\s+", " ", json.dumps(sections, ensure_ascii=False))
    skipped, unmapped = [], []
    for ti, table in enumerate(document.tables):
        for ri, row in enumerate(table.rows):
            for ci, cell in enumerate(unique_cells(row)):
                if ri == 0:
                    if cell.text.strip():
                        skipped.append({"table": ti, "row": ri})
                    continue
                for line in cell.text.splitlines():
                    text = re.sub(r"\s+", " ", line).strip()
                    if text and text not in corpus:
                        unmapped.append({"table": ti, "row": ri, "cell": ci,
                                         "text": text[:80]})
    return {"heading_skipped": skipped, "unmapped": unmapped}


def extract_en_skeleton(sections: dict, cas_rows: list) -> dict:
    """Mechanical EN prefill only: CAS numbers, content percentages, standard
    codes and phone/fax digits copied verbatim.  All prose stays empty for
    professional translation; nothing is machine-translated here."""
    phones = []
    for label, value in sections.get("s1", []):
        if isinstance(value, str) and re.search(r"电话|传真|Tel|Fax|86-", label):
            phones.append([label, value])
    standards, in_standards = [], False
    for label, value in sections.get("s15", []):
        text = f"{label} {value}".strip()
        if "符合下列" in text or "Complies" in text:
            in_standards = True
            continue
        if in_standards and re.search(r"GB|国务院令|State Council|Decree", text):
            standards.append(text)
    return {
        "s3": [{"name_en": "", "cas": row[1] if len(row) > 1 else "",
                "content": row[2] if len(row) > 2 else ""}
               for row in cas_rows if len(row) >= 2],
        "phones": phones,
        "standards": standards,
        "note": "prose left blank for agent translation; verify every copied code",
    }


def extract(source: Path) -> dict:
    if Document is None:
        raise RuntimeError("python-docx is required")
    ext = Extraction()
    document = Document(str(source))
    tables = document.tables
    if len(tables) != 16:
        ext.flag("layout", "table-count", f"expected 16 tables, found {len(tables)}")
    get = lambda i: tables[i] if i < len(tables) else None
    sections = {
        "s1": extract_s1(get(0), ext) if get(0) is not None else [],
        "s2": extract_s2(get(1), ext) if get(1) is not None else {},
        "s3": extract_s3(get(2), ext) if get(2) is not None else [],
        "s4": extract_pairs(get(3), ext, "s4") if get(3) is not None else [],
        "s5": extract_pairs(get(4), ext, "s5") if get(4) is not None else [],
        "s6": extract_pairs(get(5), ext, "s6") if get(5) is not None else [],
        "s7": extract_pairs(get(6), ext, "s7") if get(6) is not None else [],
        "s8": extract_pairs(get(7), ext, "s8") if get(7) is not None else [],
        "s9": extract_s9(get(8), ext) if get(8) is not None else [],
        "s10": extract_pairs(get(9), ext, "s10") if get(9) is not None else [],
        "s11": extract_s11(get(10), ext) if get(10) is not None else [],
        "s12": extract_pairs(get(11), ext, "s12") if get(11) is not None else [],
        "s13": extract_pairs(get(12), ext, "s13") if get(12) is not None else [],
        "s14": extract_pairs(get(13), ext, "s14") if get(13) is not None else [],
        "s15": extract_pairs(get(14), ext, "s15") if get(14) is not None else [],
        "s16": extract_pairs(get(15), ext, "s16") if get(15) is not None else [],
    }
    s3_data = [row for row in sections["s3"] if len(row) == 3 and row[0] not in ("产品类型：", "成分", "化学品名称")]
    coverage = coverage_fingerprint(document, sections)
    if coverage["unmapped"]:
        ext.flag("layout", "coverage-gap",
                 f"{len(coverage['unmapped'])} cells missing from draft; resolve before build")
    return {
        "model": extract_model(get(0), source, ext) if get(0) is not None else "",
        "source": str(source),
        "source_sha256": sha256(source),
        "sections": sections,
        "review": ext.review,
        "images": extract_images(source),
        "coverage": coverage,
        "sections_en_skeleton": extract_en_skeleton(sections, s3_data),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    data = extract(Path(args.source))
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"model": data["model"], "review_count": len(data["review"]),
                      "images": data["images"],
                      "unmapped": data["coverage"]["unmapped"],
                      "en_skeleton_rows": len(data["sections_en_skeleton"]["s3"]),
                      "out": args.out},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

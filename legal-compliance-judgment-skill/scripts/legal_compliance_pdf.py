#!/usr/bin/env python3
"""Render and verify the mandatory written PDF report."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


TITLE = "法律法规合格性检查报告"
STATUSES = ("符合（基于完整资料假设）", "不符合", "不适用", "需补证")


def _soffice() -> str:
    command = shutil.which("soffice")
    if command:
        return command
    candidates = (
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "LibreOffice/program/soffice.com",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "LibreOffice/program/soffice.com",
    )
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError("未找到 LibreOffice soffice，无法生成强制 PDF 报告")


def _text(value: Any, limit: int = 700) -> str:
    text = str(value if value is not None else "—").replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _cell(cell: Any, value: Any, font_size: int = 8) -> None:
    from docx.shared import Pt

    cell.text = _text(value)
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Microsoft YaHei"
            run.font.size = Pt(font_size)


def _add_table(document: Any, headers: list[str], rows: list[list[Any]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = True
    for cell, header in zip(table.rows[0].cells, headers):
        _cell(cell, header, 8)
    for values in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, values):
            _cell(cell, value, 7)


def _render_docx(report: dict[str, Any], path: Path) -> None:
    try:
        from docx import Document
        from docx.enum.section import WD_ORIENT
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Inches, Pt
    except ImportError as exc:
        raise RuntimeError("生成 PDF 需要已安装 python-docx") from exc

    document = Document()
    section = document.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Inches(11.69), Inches(8.27)
    section.left_margin = section.right_margin = Inches(0.45)
    section.top_margin = section.bottom_margin = Inches(0.45)
    document.core_properties.title = f"{TITLE}：{report.get('product_name', '未命名产品')}"

    heading = document.add_heading(TITLE, level=0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in heading.runs:
        run.font.name = "Microsoft YaHei"
        run.font.size = Pt(18)
    document.add_paragraph(f"产品：{_text(report.get('product_name'))}")
    document.add_paragraph(f"生成时间：{_text(report.get('generated_at'))}    判断运行 ID：{_text(report.get('run_id'))}")
    document.add_paragraph(f"判断模式：{_text(report.get('mode'))}    不确定性策略：{_text(report.get('uncertainty_mode'))}")
    document.add_paragraph(f"Report schema: {_text(report.get('report_schema'))}")
    document.add_paragraph("Result statuses: " + ", ".join(str(result.get("status", "")) for result in report.get("results", [])))
    status_codes = {"符合（基于完整资料假设）": "PASS", "不符合": "FAIL", "不适用": "NA", "需补证": "EVIDENCE"}
    document.add_paragraph("Result status codes: " + ", ".join(status_codes.get(str(result.get("status")), "UNKNOWN") for result in report.get("results", [])))
    document.add_paragraph("完整资料约束：输入资料视为完整、确定且唯一的信息源；未提及物质视为不存在，不要求补充该物质报告。")

    document.add_heading("一、输入事实", level=1)
    facts = report.get("facts", {})
    _add_table(document, ["字段", "内容"], [[key, _text(value, 1000)] for key, value in facts.items()])

    document.add_heading("二、条件驱动法规覆盖", level=1)
    selection_rows = [
        [item.get("name"), "适用" if item.get("applicable") else "不适用", item.get("reason"), item.get("source_key", "—")]
        for item in report.get("selection", [])
    ]
    _add_table(document, ["法律法规/标准", "选择", "条件单判断理由", "参考源键"], selection_rows or [["—", "—", "未提供自动选择记录", "—"]])

    document.add_heading("三、逐项合格性判断", level=1)
    result_rows = []
    for result in report.get("results", []):
        matches = "; ".join(f"{item.get('component', {}).get('name', '—')}[{item.get('match_key', '—')}]" for item in result.get("matches", [])) or "—"
        values = "; ".join(f"{item.get('measured', '—')} / {item.get('limit', '—')} / {item.get('rule_evidence', {}).get('unit', '—')}" for item in result.get("matches", [])) or "—"
        evidence = "; ".join(result.get("evidence", [])) or "; ".join(d.get("reason", "") for d in result.get("evidence_details", []) if d.get("reason")) or "—"
        result_rows.append([result.get("standard"), result.get("status"), "是" if result.get("applicable") else "否", result.get("scope_reason"), matches, values, evidence])
    _add_table(document, ["法规/标准", "结果", "适用", "适用性理由", "命中物质/匹配键", "测量值/限值/单位", "证据与闭世界处理"], result_rows or [["—"] * 7])

    document.add_heading("四、汇总与数据追溯", level=1)
    counts = report.get("counts", {})
    document.add_paragraph("；".join(f"{status}：{counts.get(status, 0)}" for status in STATUSES))
    document.add_paragraph(f"数据根目录：{_text(report.get('data_root'), 1000)}")
    document.add_paragraph(f"法规知识库：{_text(report.get('database_path'), 1000)}")
    source_rows = [[source.get("standard"), source.get("file", source.get("directory")), source.get("rows", source.get("files", "—")), source.get("version", "—"), source.get("sha256", "目录登记")] for source in report.get("sources", [])]
    _add_table(document, ["来源", "文件/目录", "行数/文件数", "版本", "SHA-256"], source_rows or [["—", "—", "—", "—", "—"]])
    document.save(path)


def verify_pdf(path: str | Path) -> dict[str, Any]:
    pdf_path = Path(path)
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"PDF 输出不存在或为空: {pdf_path}")
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError as exc:
        raise RuntimeError("校验 PDF 需要已安装 pypdf") from exc
    if not reader.pages:
        raise RuntimeError(f"PDF 没有页面: {pdf_path}")
    if "Report schema:" not in text or "Result statuses:" not in text or not any(code in text for code in ("PASS", "FAIL", "NA", "EVIDENCE")):
        raise RuntimeError(f"PDF 文本校验失败，缺少报告结构标记或判定结果: {pdf_path}")
    return {"path": str(pdf_path), "pages": len(reader.pages), "bytes": pdf_path.stat().st_size}


def write_pdf_report(report: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="legal-compliance-pdf-") as temp_dir:
        work = Path(temp_dir)
        docx_path = work / "legal_compliance_report.docx"
        profile = work / "libreoffice-profile"
        profile.mkdir()
        _render_docx(report, docx_path)
        command = [_soffice(), "--headless", f"-env:UserInstallation={profile.as_uri()}", "--convert-to", "pdf:writer_pdf_Export", "--outdir", str(work), str(docx_path)]
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
        converted = work / "legal_compliance_report.pdf"
        if completed.returncode != 0 or not converted.is_file():
            raise RuntimeError(f"LibreOffice PDF 转换失败: {completed.stderr or completed.stdout}")
        shutil.copyfile(converted, output)
    return verify_pdf(output)

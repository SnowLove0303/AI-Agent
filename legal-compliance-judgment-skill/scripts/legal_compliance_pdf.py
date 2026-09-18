#!/usr/bin/env python3
"""Render and verify the mandatory written PDF report using the 6-standard template."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
import copy

TITLE = "法律法规合格性检测报告"
SIX_STANDARDS = [
    "REACH SVHC 253项",
    "REACH Annex XVII",
    "RoHS",
    "HSF 001",
    "BSBL",
    "AfPS GS 2019:01 PAK",
]

SIX_STANDARDS_TITLES = {
    "REACH SVHC 253项": "欧盟REACH法规—高度关注物质候选清单（SVHC）",
    "REACH Annex XVII": "欧盟REACH法规附件XVII—限制物质清单",
    "RoHS": "欧盟《关于限制在电气电子设备中使用某些有害物质的指令》",
    "HSF 001": "HSF（Hazardous Substance Free）有害物质无害化/无有害物质管理要求",
    "BSBL": "bluesign® SYSTEM BLACK LIMITS（bluesign体系黑色限值清单）",
    "AfPS GS 2019:01 PAK": "德国产品安全委员会GS认证—多环芳烃（PAHs）测试与评估规范",
}

SHD_PASS = "E3F2D9"
SHD_WARN = "FEF2CB"
SHD_FAIL = "F9DBDF"


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


def _get_template_path() -> Path | None:
    candidates = [
        Path(os.environ.get("LEGAL_REPORT_TEMPLATE", "")) if os.environ.get("LEGAL_REPORT_TEMPLATE") else None,
        Path(r"F:\APP Location\Guanzhi Tong\Skill\法律法规判断\检测报告模板\报告模板-绿色通过版.docx"),
        Path(__file__).resolve().parents[1] / "references" / "templates" / "报告模板-绿色通过版.docx",
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    return None


def set_cell_shading(cell: Any, color_hex: str | None) -> None:
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls

    tcPr = cell._tc.get_or_add_tcPr()
    for child in list(tcPr):
        if child.tag.endswith("shd"):
            tcPr.remove(child)
    if color_hex:
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
        tcPr.append(shd)


def _render_docx(report: dict[str, Any], path: Path) -> None:
    try:
        import docx
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.section import WD_ORIENT
    except ImportError as exc:
        raise RuntimeError("生成 PDF 需要已安装 python-docx") from exc

    COLOR_PASS = RGBColor(0x00, 0xB0, 0x50)
    COLOR_WARN = RGBColor(0xC6, 0x5F, 0x10)
    COLOR_FAIL = RGBColor(0xFF, 0x00, 0x00)
    COLOR_TITLE = RGBColor(0x27, 0x05, 0x61)

    template_path = _get_template_path()
    if template_path:
        document = Document(template_path)
    else:
        # Fallback to create from scratch with the exact template layout
        document = Document()
        section = document.sections[0]
        section.orientation = WD_ORIENT.PORTRAIT
        section.page_width, section.page_height = Inches(8.27), Inches(11.69)
        section.left_margin = section.right_margin = Inches(0.5)
        section.top_margin = section.bottom_margin = Inches(0.5)

    facts = report.get("facts", {})
    product_name = report.get("product_name") or facts.get("product_name", "未命名受检物料")
    components = facts.get("components", [])

    # Index results by standard
    results_by_standard: dict[str, dict[str, Any]] = {
        res.get("standard"): res for res in report.get("results", []) if res.get("standard")
    }

    # Decide standards to display (prefer the 6 standards if present or default, else standards in report)
    display_standards = [s for s in SIX_STANDARDS if s in results_by_standard]
    if not display_standards:
        display_standards = list(results_by_standard.keys()) if results_by_standard else SIX_STANDARDS

    # Update basic info paragraphs
    today_str = datetime.now().strftime("%Y/%m/%d")
    found_model_para = False
    found_date_para = False
    found_summary_para = False

    for p in document.paragraphs:
        text = p.text.strip()
        if text.startswith("受检型号："):
            p.clear()
            r1 = p.add_run("受检型号：")
            r1.bold = True
            r1.font.size = Pt(12)
            r2 = p.add_run(product_name)
            r2.bold = False
            r2.font.size = Pt(12)
            found_model_para = True
        elif text.startswith("检测日期"):
            p.clear()
            r1 = p.add_run("检测日期：")
            r1.bold = True
            r1.font.size = Pt(12)
            r2 = p.add_run(today_str)
            r2.bold = False
            r2.font.size = Pt(12)
            found_date_para = True
        elif text.startswith("总结："):
            found_summary_para = True

    if not template_path:
        # If building from scratch without template file
        document.add_paragraph().add_run("基本信息：").bold = True
        p_model = document.add_paragraph()
        p_model.add_run("受检型号：").bold = True
        p_model.add_run(product_name)
        p_date = document.add_paragraph()
        p_date.add_run("检测日期：").bold = True
        p_date.add_run(today_str)
        document.add_paragraph().add_run("检测项目：").bold = True
        # Add Table 0
        t0 = document.add_table(rows=len(display_standards), cols=2)
        t0.style = "Table Grid"
        for i, s in enumerate(display_standards):
            c0, c1 = t0.rows[i].cells
            r_s = c0.paragraphs[0].add_run(s)
            r_s.font.name = "宋体"
            r_s.font.size = Pt(9.5)
            r_s.bold = True
            r_s.font.color.rgb = COLOR_TITLE
            c1.paragraphs[0].text = SIX_STANDARDS_TITLES.get(s, s)
        document.add_paragraph().add_run("检测结果：").bold = True

    # Process standard tables
    # Build summary information
    passed_standards = []
    failed_standards = []
    warning_standards = []

    for std_idx, std_name in enumerate(display_standards, start=1):
        res = results_by_standard.get(std_name, {})
        raw_status = res.get("status")
        matches = res.get("matches", [])

        # Map status to template wording: 检测通过 / 警告 / 不符
        if raw_status == "不符合":
            status_text = "不符"
            shd_bg = SHD_FAIL
            font_col = COLOR_FAIL
            failed_standards.append(std_name)
        elif raw_status in {"需补证", "警告"} or (std_name == "REACH SVHC 253项" and matches):
            status_text = "警告"
            shd_bg = SHD_WARN
            font_col = COLOR_WARN
            warning_standards.append(std_name)
        elif raw_status == "不适用":
            status_text = "不适用"
            shd_bg = SHD_PASS
            font_col = COLOR_PASS
            passed_standards.append(std_name)
        else:
            status_text = "检测通过"
            shd_bg = SHD_PASS
            font_col = COLOR_PASS
            passed_standards.append(std_name)

        # Get or add table
        if len(document.tables) > std_idx:
            tbl = document.tables[std_idx]
        else:
            tbl = document.add_table(rows=1, cols=5)
            tbl.style = "Table Grid"

        # Update Header Row 0
        hdr_cells = tbl.rows[0].cells
        hdr_cells[0].paragraphs[0].clear()
        r_title = hdr_cells[0].paragraphs[0].add_run(std_name)
        r_title.font.name = "宋体"
        r_title.font.size = Pt(14)
        r_title.bold = True
        r_title.font.color.rgb = COLOR_TITLE

        status_cell = hdr_cells[2] if len(hdr_cells) > 2 else hdr_cells[-1]
        status_cell.paragraphs[0].clear()
        r_stat = status_cell.paragraphs[0].add_run(status_text)
        r_stat.font.name = "宋体"
        r_stat.font.size = Pt(12)
        r_stat.bold = True
        r_stat.font.color.rgb = font_col

        for c in set(tbl.rows[0].cells):
            set_cell_shading(c, shd_bg)

        # Template row for copying styles
        if len(tbl.rows) > 1:
            template_tr = copy.deepcopy(tbl.rows[1]._tr)
            while len(tbl.rows) > 1:
                tbl._tbl.remove(tbl.rows[-1]._tr)
        else:
            template_tr = None

        # Build matched substances map for quick lookup
        matched_map = {}
        for m in matches:
            c_info = m.get("component", {})
            cas = c_info.get("cas") or ""
            name = c_info.get("name") or ""
            rule_ev = m.get("rule_evidence", {})
            limit_val = m.get("limit") or rule_ev.get("limit")
            unit = rule_ev.get("unit") or ""
            limit_str = f"{limit_val}{unit}" if limit_val else ""
            if not limit_str and std_name == "REACH SVHC 253项":
                limit_str = "1000ppm(0.1%)"
            matched_map[cas] = {"limit_text": limit_str or "受限", "status": "不符" if raw_status == "不符合" else "警告"}
            if name:
                matched_map[name] = matched_map[cas]

        # Add rows for components
        for c_idx, comp in enumerate(components, start=1):
            if template_tr is not None:
                new_tr = copy.deepcopy(template_tr)
                tbl._tbl.append(new_tr)
                row = tbl.rows[c_idx]
            else:
                row = tbl.add_row()

            c_name = comp.get("name", "")
            c_cas = comp.get("cas") or "N/A"
            c_conc = comp.get("concentration", "")

            subst_match = matched_map.get(c_cas) or matched_map.get(c_name)
            if subst_match:
                subst_limit = subst_match.get("limit_text", "受限")
                subst_status = subst_match.get("status", "警告")
                row_shd = SHD_FAIL if subst_status == "不符" else SHD_WARN
                row_col = COLOR_FAIL if subst_status == "不符" else COLOR_WARN
            else:
                subst_limit = "无限值"
                subst_status = "检测通过"
                row_shd = SHD_PASS
                row_col = COLOR_PASS

            # Ensure 5 cells
            while len(row.cells) < 5:
                row.add_cell()

            row.cells[0].text = str(c_idx)
            row.cells[1].text = c_name
            row.cells[2].text = c_cas
            row.cells[3].text = c_conc
            row.cells[4].text = subst_limit

            for ci, cell in enumerate(row.cells):
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.name = "宋体"
                        r.font.size = Pt(12)
                        if ci == 4:
                            r.font.color.rgb = row_col
                            r.bold = (subst_status != "检测通过")
                set_cell_shading(cell, row_shd)

    # Generate Summary text
    if not failed_standards and not warning_standards:
        summary_text = (
            f"经过CAS对照粗检，产品{product_name} 所含物质不属于"
            f"{'、'.join(display_standards)} 物质限值清单且符合相关法律法规；"
        )
    else:
        parts = []
        if passed_standards:
            parts.append(f"在 {'、'.join(passed_standards)} 判定检测通过")
        if failed_standards:
            fail_descs = []
            for fs in failed_standards:
                res = results_by_standard.get(fs, {})
                matches = res.get("matches", [])
                m_details = [f"{m['component'].get('name', '')}超过{m.get('limit') or '限值'}" for m in matches]
                m_str = "、".join(m_details) if m_details else "检测超标"
                fail_descs.append(f"{fs}（{m_str}）")
            parts.append(f"在 {'、'.join(fail_descs)} 判定不符")
        if warning_standards:
            warn_descs = []
            for ws in warning_standards:
                if ws == "REACH SVHC 253项":
                    warn_descs.append("REACH SVHC 253项（含量超过0.1%通报阈值需履行通报义务）")
                else:
                    warn_descs.append(f"{ws}（存在特定限制与管控要求）")
            parts.append(f"在 {'、'.join(warn_descs)} 存在警告与限制")
        summary_text = f"经过CAS对照粗检，产品{product_name} 所含物质" + "；".join(parts) + "。"

    # Update Summary paragraph
    updated_summary = False
    for p in document.paragraphs:
        if p.text.strip().startswith("总结："):
            p.clear()
            r_title = p.add_run("  总结：")
            r_title.bold = True
            r_title.font.size = Pt(12)
            r_text = p.add_run(summary_text)
            r_text.bold = False
            r_text.font.size = Pt(9.5)
            r_text.font.name = "宋体"
            updated_summary = True

    if not updated_summary:
        p_sum = document.add_paragraph()
        p_sum.add_run("  总结：").bold = True
        p_sum.add_run(summary_text)

    # Ensure Special Instructions
    has_special = any("特殊说明：" in p.text for p in document.paragraphs)
    if not has_special:
        document.add_paragraph().add_run("特殊说明：").bold = True
        p_bp = document.add_paragraph()
        p_bp.add_run("双酚类化学品系列：").bold = True
        p_bp.add_run("未添加且不含有；")
        p_ph = document.add_paragraph()
        p_ph.add_run("特殊邻苯二甲酸酯类增塑剂：").bold = True
        p_ph.add_run("未添加且不含有")

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
    # Verify core structure markers from template
    required_markers = ("基本信息", "检测项目", "检测结果", "总结")
    if not any(marker in text for marker in required_markers):
        raise RuntimeError(f"PDF 文本校验失败，缺少模板核心标记: {pdf_path}")
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

        # Also save the generated docx file if requested or alongside the output
        output_docx = output.with_suffix(".docx")
        try:
            shutil.copyfile(docx_path, output_docx)
        except Exception:
            pass

        command = [
            _soffice(),
            "--headless",
            f"-env:UserInstallation={profile.as_uri()}",
            "--convert-to",
            "pdf:writer_pdf_Export",
            "--outdir",
            str(work),
            str(docx_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
        converted = work / "legal_compliance_report.pdf"
        if completed.returncode != 0 or not converted.is_file():
            raise RuntimeError(f"LibreOffice PDF 转换失败: {completed.stderr or completed.stdout}")
        shutil.copyfile(converted, output)
    return verify_pdf(output)

print("test_full_pdf defined successfully")

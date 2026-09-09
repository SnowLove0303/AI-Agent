#!/usr/bin/env python3
"""Source-pictogram extraction and insertion helpers.

The source DOCX remains the authority for a supplied pictogram.  This helper
copies the first embedded raster image into the cloned template's existing
Section 2 pictogram cell without rebuilding tables or changing cell geometry.
"""
from __future__ import annotations

import io
import zipfile
from copy import deepcopy
from pathlib import Path

from docx.shared import Inches


def extract_first_embedded_image(source_docx: str | Path) -> tuple[str, bytes]:
    source = Path(source_docx)
    with zipfile.ZipFile(source) as archive:
        names = sorted(name for name in archive.namelist() if name.startswith("word/media/") and not name.endswith("/"))
        if not names:
            raise ValueError(f"source DOCX contains no embedded image: {source}")
        name = names[0]
        return Path(name).name, archive.read(name)


def insert_source_pictogram(document, source_docx: str | Path, width_inches: float = 3.25) -> dict:
    """Insert the source's first embedded image into the cloned S2 pictogram row."""
    name, payload = extract_first_embedded_image(source_docx)
    row = document.tables[1].rows[4]
    cell = row.cells[-1]
    if not cell.paragraphs:
        paragraph = cell.add_paragraph()
    else:
        paragraph = cell.paragraphs[0]
    saved_rpr = None
    for existing in paragraph.runs:
        if existing._r.rPr is not None:
            saved_rpr = deepcopy(existing._r.rPr)
            break
    for child in list(paragraph._p):
        if child.tag != "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr":
            paragraph._p.remove(child)
    run = paragraph.add_run()
    if saved_rpr is not None:
        run._r.append(saved_rpr)
    run.add_picture(io.BytesIO(payload), width=Inches(width_inches))
    return {"source_image_name": name, "source_image_bytes": len(payload), "target_table": 1, "target_row": 4}


__all__ = ["extract_first_embedded_image", "insert_source_pictogram"]

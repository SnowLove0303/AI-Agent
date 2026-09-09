"""Normalize the formal Word templates to allow rows to break across pages.

This is a baseline maintenance tool, not a deliverable patcher.  It removes
only row-level ``w:cantSplit`` elements from the supplied template files and
leaves all other OOXML parts byte-for-byte unchanged where possible.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
import zipfile
from pathlib import Path

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_CANT_SPLIT = f"{{{W_NS}}}cantSplit"


def normalize_template(path: Path) -> dict[str, int | str]:
    """Remove row-level cantSplit flags from one formal template atomically."""

    path = path.resolve()
    with zipfile.ZipFile(path, "r") as source_zip:
        names = source_zip.namelist()
        parts = {name: source_zip.read(name) for name in names}
    root = etree.fromstring(parts["word/document.xml"])
    removed = 0
    for tr_pr in root.xpath(
        ".//w:tbl/w:tr/w:trPr", namespaces={"w": W_NS}
    ):
        for cant_split in list(tr_pr):
            if cant_split.tag == W_CANT_SPLIT:
                tr_pr.remove(cant_split)
                removed += 1
    if not removed:
        return {
            "path": str(path),
            "removed": 0,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    parts["word/document.xml"] = etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    fd, staged_name = tempfile.mkstemp(
        prefix=f".{path.stem}.", suffix=".docx", dir=path.parent
    )
    os.close(fd)
    staged = Path(staged_name)
    try:
        with zipfile.ZipFile(staged, "w") as target_zip:
            for name in names:
                target_zip.writestr(name, parts[name])
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)
    return {
        "path": str(path),
        "removed": removed,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("templates", nargs="+", type=Path)
    args = parser.parse_args()
    for template in args.templates:
        print(normalize_template(template))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import importlib.metadata as metadata
import importlib.util
import json
import sys


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def check_com(progid: str) -> dict:
    try:
        import win32com.client

        app = win32com.client.DispatchEx(progid)
        version = str(getattr(app, "Version", "unknown"))
        app.Quit()
        return {"status": "PASS", "version": version}
    except Exception as exc:
        return {"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    result = {
        "schema_version": "recognition-environment-v1",
        "python": sys.version,
        "packages": {
            name: package_version(name)
            for name in ("pdfplumber", "pywin32", "pypdfium2", "python-docx")
        },
        "imports": {
            name: bool(importlib.util.find_spec(name))
            for name in ("pdfplumber", "win32com", "pypdfium2", "docx")
        },
        "word_com": check_com("Word.Application"),
        "wps_com": check_com("Kwps.Application"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

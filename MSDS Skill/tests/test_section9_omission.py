import re
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
task_root = next(path for path in (ROOT / "_task_work", ROOT.parent / "_task_work") if (path / "generate_pu2345_eight.py").exists())
sys.path.insert(0, str(task_root))

from docx import Document
spec = importlib.util.spec_from_file_location("generate_pu2345_eight_test", task_root / "generate_pu2345_eight.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def section9_rows(document):
    return document.tables[8].rows[1:]


def test_pu2345_section9_omits_missing_rows_and_renumbers():
    for language, missing_text, retained_text in (
        ("zh", "无数据", "不适用"),
        ("en", "No data available", "Not applicable"),
    ):
        document = Document(str(generator.template_for(language)))
        facts = generator.source_facts(language, "guanzhi")
        generator.ensure_s3_component_rows(document, component_count=4)
        generator.write_body(document, facts, language)

        policy = generator.suppress_missing_section9_rows_and_renumber(document)
        rows = section9_rows(document)
        labels = [row.cells[0].text.strip() for row in rows]
        values = "\n".join(row.cells[-1].text for row in rows)

        assert policy["removed_count"] == 10
        assert len(rows) == 13
        assert [re.match(r"^(9\.\d+)", label).group(1) for label in labels] == [
            f"9.{index}" for index in range(1, 14)
        ]
        assert missing_text not in values
        assert retained_text in values
        assert ("其他信息" if language == "zh" else "Other information") in "\n".join(labels)

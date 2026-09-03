from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
task_root = next(path for path in (ROOT / "_task_work", ROOT.parent / "_task_work") if (path / "generate_os9015_eight.py").exists())
sys.path.insert(0, str(task_root))
spec = importlib.util.spec_from_file_location("generate_os9015_eight_test", task_root / "generate_os9015_eight.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def test_os9015_section2_and_section11_use_explicit_source_fields():
    facts = generator.source_facts("zh", "guanzhi")
    assert "见2.4-2.6" not in facts["s2"][2][1]
    assert facts["s2"][2][1].splitlines() == ["必须列在标签上的有害成分：", "亲水脂肪族聚异氰酸酯"]
    assert facts["s11"][2][2] == "半数致死剂量（LD50）/大鼠：>2,000 mg/kg"
    assert facts["s11"][6][2] == "轻微刺激"
    assert facts["s11"][9][2] == "在Ames试验中无致突变性。"
    assert facts["s11"][7][2] == "主要粘膜刺激性：轻微刺激"
    assert facts["s11"][16][2] == "无数据"


def test_os9015_english_section11_does_not_add_unrequested_study_details():
    facts = generator.source_facts("en", "guanzhi")
    rendered = "\n".join(" | ".join(map(str, row)) for row in facts["s11"])
    assert "Species:" not in rendered
    assert "Method:" not in rendered
    assert "Study of a similar product" not in rendered
    assert "LD50/oral/rat: >2,000 mg/kg" in rendered

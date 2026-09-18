import csv
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from legal_compliance_db import add_feedback, approve_feedback, build_database, open_db, register_regulation, select_composition_baseline_regulations, select_regulations  # noqa: E402


SOURCE_FILES = [
    ("01_REACH_SVHC_01_物质全量清单(含组成员_545条).csv", ["中文名称", "英文名称", "CAS号", "EC号"]),
    ("02_REACH_附录XVII_02_受限物质明细与组成员(1868条).csv", ["中文名称", "英文名称", "CAS号", "EC号", "限制条件标题"]),
    ("03_EU_RoHS_01_受限物质清单(160条_含已补全类别CAS).csv", ["中文名称", "英文名称", "CAS号", "限值ppm"]),
    ("04_HSF-001_01_有害物质清单(172条_含已补全CAS).csv", ["中文名称", "英文名称", "CAS号", "限值"]),
    ("05_BSBL_01_受限物质总表(1726条_已修复日期并全量补全CAS).csv", ["中文名称", "英文名称", "标准CAS号", "限值(Limit)"]),
    ("06_AfPS_GS_2019_01_PAK_01_限值清单(15单项+2合计).csv", ["中文名称", "英文名称", "CAS号", "Category 1"]),
]


class LegalComplianceDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        csv_root = root / "法律法规物质限制清单_CSV导出"
        csv_root.mkdir()
        for filename, headers in SOURCE_FILES:
            with (csv_root / filename).open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=headers)
                writer.writeheader()
                writer.writerow({key: "" for key in headers})
        (csv_root / "01_REACH_SVHC_04_版本与元数据.csv").write_text("字段,字段值\n版本,fixture\n", encoding="utf-8-sig")
        (root / "欧盟玩具").mkdir()
        self.root = root
        self.db = root / "legal_compliance.db"
        self.summary = build_database(self.db, self.root)

    def tearDown(self):
        self.temp.cleanup()

    def facts(self, **overrides):
        facts = {"product_name": "test", "target_market": ["CN"], "final_use": ["leather coating"], "environment": ["industrial"], "substrates": ["leather", "plastic"], "components": [], "measurements": {}, "special_requirements": [], "assume_complete": True}
        facts.update(overrides)
        return facts

    def test_database_contains_catalog_and_derived_rows(self):
        connection = open_db(self.db)
        try:
            regulation_count = connection.execute("SELECT COUNT(*) FROM regulations").fetchone()[0]
            restriction_count = connection.execute("SELECT COUNT(*) FROM restriction_rules").fetchone()[0]
            self.assertEqual(regulation_count, 42)
            self.assertEqual(restriction_count, 7)
        finally:
            connection.close()

    def test_condition_selector_excludes_downstream_scopes(self):
        selected = {item["name"]: item for item in select_regulations(self.db, self.facts())}
        self.assertFalse(selected["2009/48/EC"]["applicable"])
        self.assertFalse(selected["RoHS"]["applicable"])
        self.assertTrue(selected["HSF 001"]["applicable"])
        self.assertFalse(selected["Mattel RMS2901"]["applicable"])

    def test_composition_baseline_ignores_market_and_use_filters(self):
        selected = select_composition_baseline_regulations(self.db)
        names = [item["name"] for item in selected]
        self.assertEqual(names, [
            "REACH SVHC 253项", "REACH Annex XVII", "REACH Annex XIV", "EU POPs 2019/1021",
            "RoHS", "HSF 001", "BSBL", "91/338/EC",
        ])
        self.assertTrue(all(item["applicable"] for item in selected))
        self.assertEqual({item["source_status"] for item in selected}, {"source-backed", "catalog-only"})

    def test_new_regulation_can_be_registered_without_code_change(self):
        register_regulation(self.db, {"id": "new-reg", "name": "NEW-REG-001", "aliases": ["NEW"], "jurisdiction": ["CN"], "scope_mode": "coating", "source_key": "new-source", "conditions": []}, {"title": "New source", "kind": "official", "uri": "https://example.invalid/new"})
        selected = {item["name"]: item for item in select_regulations(self.db, self.facts(final_use=["waterborne coating"]))}
        self.assertTrue(selected["NEW-REG-001"]["applicable"])

    def test_feedback_requires_approval_before_scope_changes(self):
        feedback_id = add_feedback(self.db, "Mattel RMS2901", {"kind": "add_condition", "condition": {"field": "special_requirements", "operator": "contains_any", "values": ["Mattel"]}})
        before = {item["name"]: item for item in select_regulations(self.db, self.facts())}
        self.assertFalse(before["Mattel RMS2901"]["applicable"])
        approve_feedback(self.db, feedback_id)
        after = {item["name"]: item for item in select_regulations(self.db, self.facts(special_requirements=["Mattel RMS2901"]))}
        self.assertTrue(after["Mattel RMS2901"]["applicable"])


if __name__ == "__main__":
    unittest.main()

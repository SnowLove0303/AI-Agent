import csv
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from legal_compliance_judge import EVIDENCE, FAIL, NA, PASS, component_match, judge  # noqa: E402


FILES = {
    "REACH SVHC 253项": ("01_REACH_SVHC_01_物质全量清单(含组成员_545条).csv", ["中文名称", "英文名称", "CAS号", "EC号"]),
    "REACH Annex XVII": ("02_REACH_附录XVII_02_受限物质明细与组成员(1868条).csv", ["中文名称", "CAS号", "限制条件标题"]),
    "RoHS": ("03_EU_RoHS_01_受限物质清单(160条_含已补全类别CAS).csv", ["中文名称", "CAS号", "限值ppm"]),
    "HSF 001": ("04_HSF-001_01_有害物质清单(172条_含已补全CAS).csv", ["中文名称", "CAS号", "限值"]),
    "BSBL": ("05_BSBL_01_受限物质总表(1726条_已修复日期并全量补全CAS).csv", ["中文名称", "标准CAS号", "限值(Limit)"]),
    "AfPS GS 2019:01 PAK": ("06_AfPS_GS_2019_01_PAK_01_限值清单(15单项+2合计).csv", ["中文名称", "CAS号", "Category 1"]),
}


class LegalComplianceJudgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        csv_root = root / "法律法规物质限制清单_CSV导出"
        csv_root.mkdir()
        for standard, (filename, headers) in FILES.items():
            row = {key: "" for key in headers}
            if standard == "REACH SVHC 253项":
                row.update({"中文名称": "苯并[a]芘", "CAS号": "50-32-8"})
            elif standard == "RoHS":
                row.update({"中文名称": "铅", "CAS号": "7439-92-1", "限值ppm": "1000"})
            elif standard == "AfPS GS 2019:01 PAK":
                row.update({"中文名称": "苯并[a]芘", "CAS号": "50-32-8", "Category 1": "0.2 mg/kg"})
            with (csv_root / filename).open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=headers)
                writer.writeheader()
                writer.writerow(row)
        (root / "欧盟玩具").mkdir()
        self.root = root

    def tearDown(self):
        self.temp.cleanup()

    def facts(self, **overrides):
        facts = {"product_name": "test", "target_market": ["CN"], "final_use": ["leather coating"], "environment": ["industrial"], "substrates": ["leather"], "components": [{"name": "polyurethane dispersion", "cas": "9009-54-5", "concentration": "40%"}], "special_requirements": [], "assume_complete": True}
        facts.update(overrides)
        return facts

    def test_complete_facts_returns_pass_for_no_match(self):
        report = judge(self.facts(), ["REACH SVHC 253项", "HSF 001"], self.root)
        self.assertEqual(report["results"][0]["status"], PASS)

    def test_scope_returns_not_applicable_for_non_eee(self):
        report = judge(self.facts(), ["RoHS"], self.root)
        self.assertEqual(report["results"][0]["status"], NA)

    def test_opaque_customer_rule_requires_evidence(self):
        report = judge(self.facts(), ["Mattel RMS2901"], self.root)
        self.assertEqual(report["results"][0]["status"], EVIDENCE)

    def test_cas_match_is_traceable(self):
        facts = self.facts(components=[{"name": "benzo[a]pyrene", "cas": "50-32-8", "concentration": "0.1 mg/kg"}])
        report = judge(facts, ["REACH SVHC 253项"], self.root)
        self.assertEqual(report["results"][0]["matches"][0]["component"]["cas"], "50-32-8")

    def test_limit_exceedance_is_nonconforming(self):
        facts = self.facts(final_use=["toy coating"], components=[{"name": "benzo[a]pyrene", "cas": "50-32-8", "concentration": "0.3 mg/kg"}])
        report = judge(facts, ["AfPS GS 2019:01 PAK"], self.root)
        self.assertEqual(report["results"][0]["status"], FAIL)

    def test_alias_and_group_name_match(self):
        self.assertTrue(component_match({"name": "NMP"}, {"英文名称": "N-Methyl-2-pyrrolidone"}))
        self.assertTrue(component_match({"name": "邻苯二甲酸酯"}, {"中文名称": "邻苯二甲酸酯类"}))


if __name__ == "__main__":
    unittest.main()

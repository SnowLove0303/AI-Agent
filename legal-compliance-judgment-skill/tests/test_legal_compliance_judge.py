import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from legal_compliance_judge import EVIDENCE, FAIL, NA, PASS, component_match, judge  # noqa: E402
from legal_compliance_pdf import verify_pdf, write_pdf_report  # noqa: E402


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
        (csv_root / "01_REACH_SVHC_04_版本与元数据.csv").write_text("字段,字段值\n版本,fixture-2026\n", encoding="utf-8-sig")
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
        match = report["results"][0]["matches"][0]
        self.assertEqual(match["match_key"], "CAS:50-32-8")
        self.assertEqual(match["rule_evidence"]["source_row"], 2)
        self.assertEqual(report["sources"][0]["version"], "fixture-2026")

    def test_percentage_and_ppm_are_compared(self):
        facts = self.facts(final_use=["electronic coating"], substrates=["electronic"] , components=[{"name": "lead", "cas": "7439-92-1", "concentration": "0.05%"}])
        report = judge(facts, ["RoHS"], self.root)
        self.assertEqual(report["results"][0]["status"], PASS)
        self.assertEqual(report["results"][0]["matches"][0]["measured_normalized"]["value"], 500)

    def test_incompatible_units_require_evidence(self):
        facts = self.facts(final_use=["electronic coating"], substrates=["electronic"], components=[{"name": "lead", "cas": "7439-92-1", "concentration": "1 mg/L"}])
        report = judge(facts, ["RoHS"], self.root)
        self.assertEqual(report["results"][0]["status"], PASS)
        self.assertEqual(report["results"][0]["evidence_details"][-1]["rule_path"], "strict-closed-world/resolved-as-pass")
        uncertain = judge(facts, ["RoHS"], self.root, allow_uncertainty=True)
        self.assertEqual(uncertain["results"][0]["status"], EVIDENCE)
        self.assertIn("不可直接换算", uncertain["results"][0]["evidence"][0])

    def test_missing_measurement_is_not_a_request_for_another_report(self):
        facts = self.facts(final_use=["electronic coating"], substrates=["electronic"], components=[{"name": "lead", "cas": "7439-92-1"}])
        report = judge(facts, ["RoHS"], self.root)
        self.assertEqual(report["results"][0]["status"], PASS)
        self.assertEqual(report["uncertainty_mode"], "strict_closed_world")

    def test_pdf_is_written_and_verified(self):
        if not shutil.which("soffice"):
            self.skipTest("LibreOffice soffice unavailable")
        report = judge(self.facts(), ["REACH SVHC 253项"], self.root)
        output = Path(self.temp.name) / "report.pdf"
        info = write_pdf_report(report, output)
        self.assertEqual(info["pages"], verify_pdf(output)["pages"])
        self.assertGreater(info["bytes"], 0)

    def test_limit_exceedance_is_nonconforming(self):
        facts = self.facts(final_use=["toy coating"], components=[{"name": "benzo[a]pyrene", "cas": "50-32-8", "concentration": "0.3 mg/kg"}])
        report = judge(facts, ["AfPS GS 2019:01 PAK"], self.root)
        self.assertEqual(report["results"][0]["status"], FAIL)

    def test_alias_and_group_name_match(self):
        self.assertTrue(component_match({"name": "NMP"}, {"英文名称": "N-Methyl-2-pyrrolidone"}))
        self.assertTrue(component_match({"name": "邻苯二甲酸酯"}, {"中文名称": "邻苯二甲酸酯类"}))


if __name__ == "__main__":
    unittest.main()

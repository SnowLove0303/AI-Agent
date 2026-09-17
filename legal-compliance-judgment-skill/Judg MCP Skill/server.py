"""
Substance Regulatory Compliance MCP Server
Provides tool-based regulatory checking for chemical substances across:
- EU RoHS 2.0 (2011/65/EU & (EU) 2015/863)
- REACH SVHC Candidate List (253 items)
- REACH Annex XVII (86 restriction entries)
- BSBL v8.0 Restricted Substance List (51 categories)
- HSF-001 Hazardous Substance Free Standard
- AfPS GS 2019:01 PAK (Polycyclic Aromatic Hydrocarbons)

Features:
- Dual-engine: Live Docker Web API (http://127.0.0.1:18765) + Direct Local SQLite DB Fallback
- Multilingual lookup: Query by CAS number, EC number, Chinese chemical name, or English name
- Concentration limit evaluation: Checks if measured % or ppm exceeds regulatory limits
- Batch compliance evaluation for multi-component formulations / MSDS / TDS
"""

import sys
import os
import re
import json
import sqlite3
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("substance-compliance-mcp")

# Database and API Paths
DOCKER_API_BASE = "http://127.0.0.1:18765"
DB_DIR = Path(r"F:\APP Location\Guanzhi Tong\旧版\03_数据库\法规数据库\物质限制清单")

# Standard Regulation Registry Names
REGULATION_NAMES = {
    "REACH_SVHC": "欧盟 REACH 高度关注物质 (SVHC) 候选清单",
    "REACH_ANNEX_XVII": "欧盟 REACH 附录 XVII 限制物质清单",
    "EU_ROHS": "欧盟 RoHS 2.0 限制物质清单 (2011/65/EU & (EU) 2015/863)",
    "HSF_001": "企业 HSF-001 有害物质控制清单",
    "BSBL": "BSBL 限制物质清单 (BSBL v8.0)",
    "AFPS_PAK": "德国 AfPS GS 2019:01 PAK 多环芳烃限制清单"
}

# Standard RoHS Threshold Limits (in ppm)
ROHS_LIMITS_PPM = {
    "cadmium": 100.0,
    "cd": 100.0,
    "lead": 1000.0,
    "pb": 1000.0,
    "mercury": 1000.0,
    "hg": 1000.0,
    "hexavalent chromium": 1000.0,
    "cr(vi)": 1000.0,
    "pbb": 1000.0,
    "pbde": 1000.0,
    "dehp": 1000.0,
    "bbp": 1000.0,
    "dbp": 1000.0,
    "dibp": 1000.0
}

# REACH SVHC Standard General Notification Threshold
SVHC_THRESHOLD_PCT = 0.1  # 0.1% w/w = 1000 ppm

# Common Chemical Names to CAS Index (Fast Resolver)
COMMON_NAME_TO_CAS = {
    # Heavy metals
    "铅": "7439-92-1", "lead": "7439-92-1", "pb": "7439-92-1",
    "汞": "7439-97-6", "mercury": "7439-97-6", "水银": "7439-97-6", "hg": "7439-97-6",
    "镉": "7440-43-9", "cadmium": "7440-43-9", "cd": "7440-43-9",
    "六价铬": "18540-29-9", "chromium vi": "18540-29-9", "cr vi": "18540-29-9",
    "镍": "7440-02-0", "nickel": "7440-02-0",
    "砷": "7440-38-2", "arsenic": "7440-38-2",
    "锑": "7440-36-0", "antimony": "7440-36-0",
    "钡": "7440-39-3", "barium": "7440-39-3",
    "钴": "7440-48-4", "cobalt": "7440-48-4",
    "硒": "7782-49-2", "selenium": "7782-49-2",
    # Plasticizers / Phthalates
    "邻苯二甲酸二(2-乙基己)酯": "117-81-7", "dehp": "117-81-7", "dop": "117-81-7",
    "邻苯二甲酸甲苯基丁酯": "85-68-7", "bbp": "85-68-7",
    "邻苯二甲酸二丁酯": "84-74-2", "dbp": "84-74-2",
    "邻苯二甲酸二异丁酯": "84-69-5", "dibp": "84-69-5",
    "邻苯二甲酸二异壬酯": "28553-12-0", "dinp": "28553-12-0",
    "邻苯二甲酸二异癸酯": "26761-40-0", "didp": "26761-40-0",
    "邻苯二甲酸二正辛酯": "117-84-0", "dnop": "117-84-0",
    # Flame retardants
    "多溴联苯": "59536-65-1", "pbbs": "59536-65-1", "pbb": "59536-65-1",
    "多溴二苯醚": "1163-19-5", "pbdes": "1163-19-5", "pbde": "1163-19-5",
    "十溴二苯醚": "1163-19-5", "decabde": "1163-19-5",
    "六溴环十二烷": "25637-99-4", "hbcdd": "25637-99-4",
    "得克隆": "13560-89-9", "dechlorane plus": "13560-89-9",
    "多氯萘": "70776-03-3", "pcn": "70776-03-3", "pcns": "70776-03-3",
    # Bisphenols & Monomers
    "双酚a": "80-05-7", "bisphenol a": "80-05-7", "bpa": "80-05-7",
    "双酚s": "80-09-1", "bisphenol s": "80-09-1", "bps": "80-09-1",
    "双酚af": "1478-61-1", "bisphenol af": "1478-61-1", "bpaf": "1478-61-1",
    "丙烯酰胺": "79-06-1", "acrylamide": "79-06-1",
    "氯乙烯": "75-01-4", "vinyl chloride": "75-01-4",
    "二氯甲烷": "75-09-2", "dichloromethane": "75-09-2", "dcm": "75-09-2",
    "三氯乙烯": "79-01-6", "trichloroethylene": "79-01-6", "tce": "79-01-6",
    # PAHs
    "苯并[a]芘": "50-32-8", "benzo[a]pyrene": "50-32-8", "bap": "50-32-8",
    "苯并[e]芘": "192-97-2", "benzo[e]pyrene": "192-97-2",
    "苯并[a]蒽": "56-55-3", "benzo[a]anthracene": "56-55-3",
    "䓛": "218-01-9", "chrysene": "218-01-9",
    "菲": "85-01-8", "phenanthrene": "85-01-8",
    "蒽": "120-12-7", "anthracene": "120-12-7",
    "芘": "129-00-0", "pyrene": "129-00-0",
    "萘": "91-20-3", "naphthalene": "91-20-3",
    # PFAS
    "全氟辛酸": "335-67-1", "perfluorooctanoic acid": "335-67-1", "pfoa": "335-67-1",
    "全氟辛烷磺酸": "1763-23-1", "perfluorooctane sulfonic acid": "1763-23-1", "pfos": "1763-23-1",
    "全氟己烷磺酸": "355-46-4", "perfluorohexane sulfonic acid": "355-46-4", "pfhxs": "355-46-4",
    "全氟丁烷磺酸": "375-73-5", "perfluorobutane sulfonic acid": "375-73-5", "pfbs": "375-73-5",
    "全氟己酸": "307-24-4", "perfluorohexanoic acid": "307-24-4", "pfhxa": "307-24-4",
    "全氟丁酸": "375-22-4", "perfluorobutanoic acid": "375-22-4", "pfba": "375-22-4",
    # Organotins
    "氧化双(三丁基锡)": "56-35-9", "tbto": "56-35-9", "三丁基锡": "56-35-9",
    "二月桂酸二辛基锡": "3648-18-8", "dote": "15571-58-1",
    # Dyes
    "孔雀石绿": "569-64-2", "malachite green": "569-64-2", "碱性绿4": "569-64-2",
    "结晶紫": "548-62-9", "crystal violet": "548-62-9", "碱性紫3": "548-62-9",
    # Inorganics
    "硼酸": "10043-35-3", "boric acid": "10043-35-3",
    "重铬酸钠": "10588-01-9", "sodium dichromate": "10588-01-9",
    "四硼酸二钠": "1330-43-4", "disodium tetraborate": "1330-43-4"
}

def _resolve_to_cas(query: str) -> Optional[str]:
    """Resolve an input query (CAS, EC, or chemical name) to standard CAS format."""
    q = str(query or "").strip().lower()
    if not q:
        return None
    # 1. Direct CAS pattern
    m = re.search(r"\b\d{2,7}-\d{2,7}-\d\b", q)
    if m:
        return m.group(0)
    # 2. Lookup common dictionary
    if q in COMMON_NAME_TO_CAS:
        return COMMON_NAME_TO_CAS[q]
    # 3. Clean and check partial dictionary
    clean_q = re.sub(r"[()（）\s_-]", "", q)
    for k, v in COMMON_NAME_TO_CAS.items():
        if clean_q == re.sub(r"[()（）\s_-]", "", k):
            return v
    # 4. Search local SQLite database for matching Chinese or English name
    try:
        cas_from_db = _search_cas_in_local_db(q)
        if cas_from_db:
            return cas_from_db
    except Exception:
        pass
    return None

def _search_cas_in_local_db(name_keyword: str) -> Optional[str]:
    """Search for CAS number by substance name across local SQLite databases."""
    kw = f"%{name_keyword}%"
    # Check SVHC
    p_svhc = DB_DIR / "REACH-SVHC-253项-物质数据库-2026-02-04.db"
    if p_svhc.exists():
        with sqlite3.connect(p_svhc) as conn:
            row = conn.execute(
                "SELECT CAS号 FROM reach_svhc_substance WHERE (中文名称 LIKE ? OR 英文名称 LIKE ?) AND CAS号 IS NOT NULL AND CAS号 != '' LIMIT 1",
                (kw, kw)
            ).fetchone()
            if row and re.search(r"\d{2,7}-\d{2,7}-\d", row[0]):
                return re.search(r"\d{2,7}-\d{2,7}-\d", row[0]).group(0)
    # Check Annex XVII
    p_xvii = DB_DIR / "REACH-Annex-XVII-限制物质数据库.db"
    if p_xvii.exists():
        with sqlite3.connect(p_xvii) as conn:
            row = conn.execute(
                "SELECT CAS号 FROM annex_xvii_substance WHERE (中文名称 LIKE ? OR 英文名称 LIKE ?) AND CAS号 IS NOT NULL AND CAS号 != '' LIMIT 1",
                (kw, kw)
            ).fetchone()
            if row and re.search(r"\d{2,7}-\d{2,7}-\d", row[0]):
                return re.search(r"\d{2,7}-\d{2,7}-\d", row[0]).group(0)
    # Check BSBL
    p_bsbl = DB_DIR / "BSBL-物质限制清单-2026-08-27.db"
    if p_bsbl.exists():
        with sqlite3.connect(p_bsbl) as conn:
            row = conn.execute(
                "SELECT cas_no FROM bsbl_register WHERE (chinese_name LIKE ? OR english_name LIKE ?) AND cas_no IS NOT NULL AND cas_no != '' LIMIT 1",
                (kw, kw)
            ).fetchone()
            if row and re.search(r"\d{2,7}-\d{2,7}-\d", row[0]):
                return re.search(r"\d{2,7}-\d{2,7}-\d", row[0]).group(0)
    return None

def _query_docker_api(identifier: str) -> Optional[Dict[str, Any]]:
    """Query live Docker Web container compliance endpoint."""
    try:
        url = f"{DOCKER_API_BASE}/api/compliance/check?identifier={urllib.parse.quote(identifier)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-MCP/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("ok"):
                    return data.get("result", {})
    except Exception:
        pass
    return None

def _query_local_databases(identifier: str) -> Dict[str, Any]:
    """Fallback query against local SQLite and JSON databases."""
    result: Dict[str, Any] = {
        "query": identifier,
        "reach": {"matched": False, "records": []},
        "annex_xvii": {"matched": False, "records": []},
        "rohs": {"matched": False, "records": []},
        "hsf_001": {"matched": False, "records": []},
        "bsbl": {"matched": False, "records": []},
        "afps": {"matched": False, "records": []}
    }
    
    # 1. REACH SVHC
    p_svhc = DB_DIR / "REACH-SVHC-253项-物质数据库-2026-02-04.db"
    if p_svhc.exists():
        try:
            with sqlite3.connect(p_svhc) as conn:
                conn.row_factory = sqlite3.Row
                recs = []
                for row in conn.execute("SELECT * FROM reach_svhc_substance"):
                    cas_list = re.findall(r"\d{2,7}-\d{2,7}-\d", str(row["CAS号"] or ""))
                    ec_list = re.findall(r"\d{2,7}-\d{2,7}-\d", str(row["EC号"] or ""))
                    if identifier in cas_list or identifier in ec_list:
                        recs.append(dict(row))
                result["reach"] = {"matched": bool(recs), "records": recs}
        except Exception:
            pass

    # 2. REACH Annex XVII
    p_xvii = DB_DIR / "REACH-Annex-XVII-限制物质数据库.db"
    if p_xvii.exists():
        try:
            with sqlite3.connect(p_xvii) as conn:
                conn.row_factory = sqlite3.Row
                recs = []
                for row in conn.execute("SELECT * FROM annex_xvii_substance"):
                    cas_list = re.findall(r"\d{2,7}-\d{2,7}-\d", str(row["CAS号"] or ""))
                    ec_list = re.findall(r"\d{2,7}-\d{2,7}-\d", str(row["EC号"] or ""))
                    if identifier in cas_list or identifier in ec_list:
                        recs.append(dict(row))
                result["annex_xvii"] = {"matched": bool(recs), "records": recs}
        except Exception:
            pass

    # 3. EU RoHS
    p_rohs = DB_DIR / "EU-RoHS-2011-65-EU-2015-863-限制物质数据库.db"
    if p_rohs.exists():
        try:
            with sqlite3.connect(p_rohs) as conn:
                conn.row_factory = sqlite3.Row
                recs = []
                for row in conn.execute("SELECT * FROM rohs_restricted_substance"):
                    cas_list = re.findall(r"\d{2,7}-\d{2,7}-\d", str(row["CAS号"] or ""))
                    ec_list = re.findall(r"\d{2,7}-\d{2,7}-\d", str(row["EC号"] or ""))
                    if identifier in cas_list or identifier in ec_list:
                        recs.append(dict(row))
                result["rohs"] = {"matched": bool(recs), "records": recs}
        except Exception:
            pass

    # 4. HSF-001
    p_hsf = DB_DIR / "HSF-001-有害物质清单.db"
    if p_hsf.exists():
        try:
            with sqlite3.connect(p_hsf) as conn:
                conn.row_factory = sqlite3.Row
                recs = []
                for row in conn.execute("SELECT * FROM hsf_001_substance"):
                    cas_list = re.findall(r"\d{2,7}-\d{2,7}-\d", str(row["CAS号"] or ""))
                    if identifier in cas_list:
                        recs.append(dict(row))
                result["hsf_001"] = {"matched": bool(recs), "records": recs}
        except Exception:
            pass

    # 5. BSBL
    p_bsbl = DB_DIR / "BSBL-物质限制清单-2026-08-27.db"
    if p_bsbl.exists():
        try:
            with sqlite3.connect(p_bsbl) as conn:
                conn.row_factory = sqlite3.Row
                recs = []
                for row in conn.execute(
                    "SELECT r.* FROM bsbl_identifier i JOIN bsbl_register r ON r.register_id=i.register_id WHERE i.identifier=?",
                    (identifier,)
                ):
                    recs.append(dict(row))
                if not recs:
                    # Also check direct cas_no or cas_raw
                    for row in conn.execute(
                        "SELECT * FROM bsbl_register WHERE cas_no LIKE ? OR cas_raw LIKE ?",
                        (f"%{identifier}%", f"%{identifier}%")
                    ):
                        recs.append(dict(row))
                result["bsbl"] = {"matched": bool(recs), "records": recs}
        except Exception:
            pass

    # 6. AfPS PAK
    p_afps = DB_DIR / "AfPS-GS-2019-01-PAK.json"
    if p_afps.exists():
        try:
            data = json.loads(p_afps.read_text(encoding="utf-8"))
            recs = []
            for r in data.get("rows", []):
                cas_str = str(r.get("CAS号") or "")
                if identifier in re.findall(r"\d{2,7}-\d{2,7}-\d", cas_str):
                    recs.append(r)
            result["afps"] = {"matched": bool(recs), "records": recs}
        except Exception:
            pass

    return result

def _get_substance_info(raw_query: str, cas_id: str, compliance_raw: Dict[str, Any]) -> Dict[str, str]:
    """Extract standard chemical names and identifiers from raw records."""
    name_cn = ""
    name_en = ""
    ec_no = ""
    
    # Try finding in SVHC records
    svhc_recs = compliance_raw.get("reach", {}).get("records", [])
    if svhc_recs:
        name_cn = svhc_recs[0].get("中文名称", "")
        name_en = svhc_recs[0].get("英文名称", "")
        ec_no = svhc_recs[0].get("EC号", "")
        
    # Try RoHS records
    if not name_cn:
        rohs_recs = compliance_raw.get("rohs", {}).get("records", [])
        if rohs_recs:
            name_cn = rohs_recs[0].get("中文名称", "")
            name_en = rohs_recs[0].get("英文名称", "")
            ec_no = rohs_recs[0].get("EC号", "")

    # Try BSBL records
    if not name_cn:
        bsbl_recs = compliance_raw.get("bsbl", {}).get("records", [])
        if bsbl_recs:
            name_cn = bsbl_recs[0].get("chinese_name", "") or bsbl_recs[0].get("中文名称", "")
            name_en = bsbl_recs[0].get("english_name", "") or bsbl_recs[0].get("英文名称", "")
            ec_no = bsbl_recs[0].get("ec_no", "") or bsbl_recs[0].get("EC号", "")

    # Try AfPS records
    if not name_cn:
        afps_recs = compliance_raw.get("afps", {}).get("records", [])
        if afps_recs:
            name_cn = afps_recs[0].get("中文名称", "")
            name_en = afps_recs[0].get("英文名称", "")

    # Fallback to query if no record found
    if not name_cn:
        name_cn = raw_query if not re.match(r"^\d{2,7}-\d{2,7}-\d$", raw_query) else "未知名录化合物"
    if not name_en:
        name_en = "-"

    return {
        "cas": cas_id,
        "ec": ec_no or "-",
        "name_cn": name_cn,
        "name_en": name_en
    }

# =========================================================================
# MCP Tools Definitions
# =========================================================================

@mcp.tool()
def check_substance_compliance(
    substance: str,
    concentration_pct: Optional[float] = None,
    concentration_ppm: Optional[float] = None,
    regulations: Optional[List[str]] = None,
    material_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    检查某种化学物质是否符合主流法律法规及限制物质清单。
    
    支持法规体系：
    - EU_ROHS: 欧盟 RoHS 2.0 (电子电气设备有害物质限制，10项受限物)
    - REACH_SVHC: 欧盟 REACH 高度关注物质候选清单 (253项，0.1% w/w 申报阈值)
    - REACH_ANNEX_XVII: 欧盟 REACH 附录 XVII 强制限制物质清单 (86大类限制条目)
    - BSBL: BSBL 鞋服高分子材料物质限制清单 v8.0 (51个管控大类)
    - HSF_001: 企业 HSF 无有害物质工程受控清单
    - AFPS_PAK: 德国 GS 认证 AfPS 2019:01 PAK 多环芳烃分级限制
    
    参数说明:
    - substance: 待查询物质，支持标准 CAS号 (如 '7439-92-1')、EC号 (如 '231-100-4')、中文品名 (如 '双酚A', '铅', '孔雀石绿') 或英文品名 (如 'Lead', 'Bisphenol A')
    - concentration_pct: 检出浓度百分比（% w/w），例如 0.05 代表 0.05% (500 ppm)
    - concentration_ppm: 检出浓度百万分比（ppm 或 mg/kg），例如 500 代表 500 ppm
    - regulations: 可选过滤的法规范围列表。若留空或为 None，默认全量检查所有 6 大法规
    - material_type: 可选材质类型 (如 'metal', 'plastic', 'textile', 'leather')，用于辅助判定材质特定限值
    """
    raw_query = str(substance or "").strip()
    if not raw_query:
        return {"error": "查询物质名称或标识不能为空"}

    # Resolve to CAS / Identifier
    cas_id = _resolve_to_cas(raw_query)
    if not cas_id:
        return {
            "query": raw_query,
            "status": "UNRESOLVED",
            "overall_verdict": "UNKNOWN",
            "summary": f"未能解析物质 '{raw_query}' 的有效 CAS/EC 标识，请提供标准 CAS 号或准确化学品名。",
            "matched_regulations_count": 0,
            "regulations": {}
        }

    # Normalize concentration to both % and ppm
    pct = concentration_pct
    ppm = concentration_ppm
    if pct is not None and ppm is None:
        ppm = pct * 10000.0
    elif ppm is not None and pct is None:
        pct = ppm / 10000.0

    # 1. Query Dual Engine (Docker Web API first, fallback to SQLite)
    raw_result = _query_docker_api(cas_id)
    engine_used = "Docker_API"
    if not raw_result:
        raw_result = _query_local_databases(cas_id)
        engine_used = "Local_SQLite_Fallback"

    # 2. Extract substance identity
    substance_info = _get_substance_info(raw_query, cas_id, raw_result)

    # 3. Analyze each regulation
    filter_regs = set(r.upper() for r in regulations) if regulations else None
    
    eval_results: Dict[str, Any] = {}
    violations = []
    warnings = []

    # --- 3.1 EU RoHS ---
    if not filter_regs or "EU_ROHS" in filter_regs or "ROHS" in filter_regs:
        rohs_data = raw_result.get("rohs", {})
        is_matched = bool(rohs_data.get("matched"))
        rohs_recs = rohs_data.get("records", [])
        
        limit_ppm = 1000.0
        # Determine specific limit (Cadmium is 100 ppm / 0.01%, others are 1000 ppm / 0.1%)
        cas_or_name = f"{substance_info.get('cas', '')} {substance_info.get('name_cn', '')} {substance_info.get('name_en', '')}".lower()
        if "7440-43-9" in cas_or_name or "镉" in cas_or_name or "cadmium" in cas_or_name:
            limit_ppm = 100.0
        else:
            for r in rohs_recs:
                c_val = str(r.get("限值ppm") or r.get("均质材料限值") or "")
                if ("0.01%" in c_val) or (re.search(r"\b100\b(?!\s*0)", c_val) and not re.search(r"\b1000\b", c_val)):
                    limit_ppm = 100.0
                    break

        if is_matched:
            sub_verdict = "RESTRICTED_LISTED"
            details = f"列入 EU RoHS 2.0 受限物质清单 (限值: {limit_ppm} ppm / {limit_ppm/10000.0}% w/w)"
            if ppm is not None:
                if ppm > limit_ppm:
                    sub_verdict = "NON_COMPLIANT"
                    violations.append(f"RoHS超标: 检出浓度 {ppm} ppm 超过法规限值 {limit_ppm} ppm")
                else:
                    sub_verdict = "COMPLIANT"
            else:
                warnings.append(f"列入 RoHS 受限清单，要求均质材料中浓度不得超过 {limit_ppm} ppm")

            eval_results["EU_ROHS"] = {
                "regulation_name": REGULATION_NAMES["EU_ROHS"],
                "matched": True,
                "verdict": sub_verdict,
                "limit_ppm": limit_ppm,
                "limit_display": f"{limit_ppm} ppm ({limit_ppm/10000.0}% w/w)",
                "measured_ppm": ppm,
                "details": details,
                "records_count": len(rohs_recs)
            }
        else:
            eval_results["EU_ROHS"] = {
                "regulation_name": REGULATION_NAMES["EU_ROHS"],
                "matched": False,
                "verdict": "COMPLIANT_NOT_LISTED",
                "details": "未列入 EU RoHS 2.0 限制物质清单，不受均质材料 100/1000 ppm 限值约束。"
            }

    # --- 3.2 REACH SVHC ---
    if not filter_regs or "REACH_SVHC" in filter_regs or "SVHC" in filter_regs:
        svhc_data = raw_result.get("reach", {})
        is_matched = bool(svhc_data.get("matched"))
        svhc_recs = svhc_data.get("records", [])

        if is_matched:
            sub_verdict = "RESTRICTED_LISTED"
            details = "列入 ECHA REACH 高度关注物质 (SVHC) 候选清单。"
            if pct is not None:
                if pct > SVHC_THRESHOLD_PCT:
                    sub_verdict = "DUTY_TRIGGERED"
                    violations.append(f"REACH SVHC通报义务触发: 浓度 {pct}% (w/w) > 0.1% 阈值，需履行供应链安全信息传递及SCIP通报义务")
                else:
                    sub_verdict = "COMPLIANT_BELOW_THRESHOLD"
                    details += f" 当前浓度 {pct}% (w/w) ≤ 0.1%，低于强制通报与授权阈值。"
            else:
                warnings.append("列入 REACH SVHC 候选清单，在物品/配方中若含量 >0.1% (w/w) 需履行通报及传递义务")

            eval_results["REACH_SVHC"] = {
                "regulation_name": REGULATION_NAMES["REACH_SVHC"],
                "matched": True,
                "verdict": sub_verdict,
                "threshold_display": "0.1% (w/w) / 1000 ppm",
                "measured_pct": pct,
                "details": details,
                "records_count": len(svhc_recs)
            }
        else:
            eval_results["REACH_SVHC"] = {
                "regulation_name": REGULATION_NAMES["REACH_SVHC"],
                "matched": False,
                "verdict": "COMPLIANT_NOT_LISTED",
                "details": "未列入现行有效 REACH SVHC 候选清单。"
            }

    # --- 3.3 REACH Annex XVII ---
    if not filter_regs or "REACH_ANNEX_XVII" in filter_regs or "ANNEX_XVII" in filter_regs:
        xvii_data = raw_result.get("annex_xvii", {})
        is_matched = bool(xvii_data.get("matched"))
        xvii_recs = xvii_data.get("records", [])

        if is_matched:
            entry_nos = list(set(str(r.get("条目号") or "") for r in xvii_recs))
            details = f"列入 REACH 附录 XVII 强制限制条目: 第 {', '.join(entry_nos)} 条"
            warnings.append(f"REACH 附录 XVII 限制: 列入第 {', '.join(entry_nos)} 条，存在特定市场用途禁令或特定含量限制")
            eval_results["REACH_ANNEX_XVII"] = {
                "regulation_name": REGULATION_NAMES["REACH_ANNEX_XVII"],
                "matched": True,
                "verdict": "RESTRICTED_CONDITIONAL",
                "restricted_entries": entry_nos,
                "details": details,
                "records_count": len(xvii_recs)
            }
        else:
            eval_results["REACH_ANNEX_XVII"] = {
                "regulation_name": REGULATION_NAMES["REACH_ANNEX_XVII"],
                "matched": False,
                "verdict": "COMPLIANT_NOT_LISTED",
                "details": "未列入 REACH 附录 XVII 强制限制清单。"
            }

    # --- 3.4 BSBL ---
    if not filter_regs or "BSBL" in filter_regs:
        bsbl_data = raw_result.get("bsbl", {})
        is_matched = bool(bsbl_data.get("matched"))
        bsbl_recs = bsbl_data.get("records", [])

        if is_matched:
            categories = list(set(str(r.get("类别(Category)") or r.get("category") or r.get("类别") or "") for r in bsbl_recs))
            limits = [str(r.get("限值(Limit)") or r.get("limit_value") or "") for r in bsbl_recs if str(r.get("限值(Limit)") or r.get("limit_value") or "")]
            details = f"列入 BSBL 限制物质清单 (管控类别: {', '.join(categories[:3])})"
            warnings.append(f"BSBL 受限: 归属于 {', '.join(categories[:2])} 限制大类")
            eval_results["BSBL"] = {
                "regulation_name": REGULATION_NAMES["BSBL"],
                "matched": True,
                "verdict": "RESTRICTED_LISTED",
                "categories": categories,
                "limit_samples": limits[:3],
                "details": details,
                "records_count": len(bsbl_recs)
            }
        else:
            eval_results["BSBL"] = {
                "regulation_name": REGULATION_NAMES["BSBL"],
                "matched": False,
                "verdict": "COMPLIANT_NOT_LISTED",
                "details": "未列入 BSBL 物质限制清单。"
            }

    # --- 3.5 HSF-001 ---
    if not filter_regs or "HSF_001" in filter_regs or "HSF" in filter_regs:
        hsf_data = raw_result.get("hsf_001", {})
        is_matched = bool(hsf_data.get("matched"))
        hsf_recs = hsf_data.get("records", [])

        if is_matched:
            eval_results["HSF_001"] = {
                "regulation_name": REGULATION_NAMES["HSF_001"],
                "matched": True,
                "verdict": "RESTRICTED_CONTROLLED",
                "details": "列入企业 HSF-001 有害物质控制清单，需满足无有害物质准入审查。",
                "records_count": len(hsf_recs)
            }
            warnings.append("列入企业 HSF-001 有害物质受控清单")
        else:
            eval_results["HSF_001"] = {
                "regulation_name": REGULATION_NAMES["HSF_001"],
                "matched": False,
                "verdict": "COMPLIANT_NOT_LISTED",
                "details": "未列入企业 HSF-001 有害物质控制清单。"
            }

    # --- 3.6 AfPS PAK ---
    if not filter_regs or "AFPS_PAK" in filter_regs or "PAK" in filter_regs:
        afps_data = raw_result.get("afps", {})
        is_matched = bool(afps_data.get("matched"))
        afps_recs = afps_data.get("records", [])

        if is_matched:
            eval_results["AFPS_PAK"] = {
                "regulation_name": REGULATION_NAMES["AFPS_PAK"],
                "matched": True,
                "verdict": "RESTRICTED_PAH",
                "details": "列入德国 GS 认证 AfPS GS 2019:01 PAK 15项多环芳烃强制管控清单。",
                "records_count": len(afps_recs)
            }
            warnings.append("列入德国 GS 认证 AfPS PAK 15项受控多环芳烃清单")
        else:
            eval_results["AFPS_PAK"] = {
                "regulation_name": REGULATION_NAMES["AFPS_PAK"],
                "matched": False,
                "verdict": "COMPLIANT_NOT_LISTED",
                "details": "未列入德国 AfPS GS 2019:01 PAK 受限多环芳烃清单。"
            }

    # 4. Synthesize Overall Verdict
    matched_count = sum(1 for v in eval_results.values() if v.get("matched"))
    
    if violations:
        overall_verdict = "NON_COMPLIANT"
        summary = f"【不合规 / 存在超标】物质 '{substance_info['name_cn']}' ({cas_id}) 存在超标违规项: {'; '.join(violations)}。"
    elif matched_count > 0:
        overall_verdict = "RESTRICTED_CONDITIONAL"
        summary = f"【受法规限制】物质 '{substance_info['name_cn']}' ({cas_id}) 命中 {matched_count} 项法规限制清单: {'; '.join(warnings)}。使用前须满足相应限量或特定用途豁免条件。"
    else:
        overall_verdict = "COMPLIANT"
        summary = f"【合规 / 未受限】物质 '{substance_info['name_cn']}' ({cas_id}) 未列入所查询的 {len(eval_results)} 项法规限制清单中，符合通用合规要求。"

    return {
        "query": raw_query,
        "resolved_substance": substance_info,
        "overall_verdict": overall_verdict,
        "matched_regulations_count": matched_count,
        "summary": summary,
        "violations": violations,
        "warnings": warnings,
        "regulations": eval_results,
        "data_source_engine": engine_used
    }

@mcp.tool()
def batch_check_compliance(
    components: List[Dict[str, Any]],
    regulations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    批量检查物料或配方中多个组分的法律法规合规性（适用于 MSDS / TDS 配方筛查）。
    
    参数说明:
    - components: 组分列表。每个组分格式形如：
      {"substance": "7439-92-1", "name": "铅", "concentration_ppm": 500, "concentration_pct": 0.05}
    - regulations: 可选法规范围过滤列表
    """
    if not components:
        return {"error": "组分列表 components 不能为空"}

    results = []
    total_violations = []
    total_restricted_items = []
    
    for comp in components:
        sub = comp.get("substance") or comp.get("cas") or comp.get("name") or ""
        pct = comp.get("concentration_pct")
        ppm = comp.get("concentration_ppm")
        mat = comp.get("material_type")
        
        eval_res = check_substance_compliance(
            substance=sub,
            concentration_pct=pct,
            concentration_ppm=ppm,
            regulations=regulations,
            material_type=mat
        )
        results.append(eval_res)
        
        if eval_res.get("violations"):
            total_violations.extend(eval_res["violations"])
        if eval_res.get("matched_regulations_count", 0) > 0:
            total_restricted_items.append(eval_res.get("resolved_substance", {}).get("name_cn", sub))

    overall_pass = (len(total_violations) == 0)
    
    return {
        "total_components_checked": len(components),
        "overall_pass": overall_pass,
        "verdict": "PASS" if overall_pass else "FAIL",
        "restricted_substances_found": list(set(total_restricted_items)),
        "violations_found": total_violations,
        "components_evaluation": results
    }

@mcp.tool()
def search_regulatory_substances(
    keyword: str,
    regulation: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    在六大法规受限清单中模糊检索符合关键字的受限化学物质。
    
    参数说明:
    - keyword: 检索关键词，如 '铅', '苯', 'tin', 'phthalate', '117-'
    - regulation: 指定检索的法规范围 (如 'REACH_SVHC', 'EU_ROHS', 'BSBL', 'REACH_ANNEX_XVII')
    - limit: 返回最大记录条数 (默认 20 条)
    """
    kw = f"%{keyword.strip()}%"
    matched_items = []
    
    # Search SVHC
    if not regulation or regulation.upper() in ("REACH_SVHC", "SVHC"):
        p_svhc = DB_DIR / "REACH-SVHC-253项-物质数据库-2026-02-04.db"
        if p_svhc.exists():
            with sqlite3.connect(p_svhc) as conn:
                for row in conn.execute(
                    "SELECT 'REACH_SVHC' as reg, 中文名称, 英文名称, CAS号, EC号, 物质描述 FROM reach_svhc_substance WHERE 中文名称 LIKE ? OR 英文名称 LIKE ? OR CAS号 LIKE ? LIMIT ?",
                    (kw, kw, kw, limit)
                ):
                    matched_items.append({
                        "regulation": "REACH SVHC",
                        "name_cn": row[1],
                        "name_en": row[2],
                        "cas": row[3],
                        "ec": row[4],
                        "desc": row[5]
                    })

    # Search RoHS
    if not regulation or regulation.upper() in ("EU_ROHS", "ROHS"):
        p_rohs = DB_DIR / "EU-RoHS-2011-65-EU-2015-863-限制物质数据库.db"
        if p_rohs.exists():
            with sqlite3.connect(p_rohs) as conn:
                for row in conn.execute(
                    "SELECT 'EU_ROHS' as reg, 中文名称, 英文名称, CAS号, EC号, 均质材料限值 FROM rohs_restricted_substance WHERE 中文名称 LIKE ? OR 英文名称 LIKE ? OR CAS号 LIKE ? LIMIT ?",
                    (kw, kw, kw, limit)
                ):
                    matched_items.append({
                        "regulation": "EU RoHS",
                        "name_cn": row[1],
                        "name_en": row[2],
                        "cas": row[3],
                        "ec": row[4],
                        "limit": row[5]
                    })

    # Search BSBL
    if not regulation or regulation.upper() in ("BSBL",):
        p_bsbl = DB_DIR / "BSBL-物质限制清单-2026-08-27.db"
        if p_bsbl.exists():
            with sqlite3.connect(p_bsbl) as conn:
                for row in conn.execute(
                    "SELECT 'BSBL' as reg, chinese_name, english_name, cas_no, category, limit_value FROM bsbl_register WHERE chinese_name LIKE ? OR english_name LIKE ? OR cas_no LIKE ? LIMIT ?",
                    (kw, kw, kw, limit)
                ):
                    matched_items.append({
                        "regulation": "BSBL v8.0",
                        "name_cn": row[1],
                        "name_en": row[2],
                        "cas": row[3],
                        "category": row[4],
                        "limit": row[5]
                    })

    return {
        "keyword": keyword,
        "count": len(matched_items[:limit]),
        "results": matched_items[:limit]
    }

@mcp.tool()
def get_regulation_info(regulation: str) -> Dict[str, Any]:
    """
    获取指定法规物质限制标准的官方依据、最新有效版本、管控范围及核心限量要求。
    
    参数说明:
    - regulation: 法规标识代码，支持 'REACH_SVHC', 'EU_ROHS', 'REACH_ANNEX_XVII', 'BSBL', 'HSF_001', 'AFPS_PAK'
    """
    key = regulation.upper().replace("-", "_").strip()
    
    info_map = {
        "REACH_SVHC": {
            "name": REGULATION_NAMES["REACH_SVHC"],
            "version": "2026-02-04 (ECHA 官方第 32 批更新基线)",
            "scope": "欧盟化学品 REACH 法规候选清单；针对均质材料/物品中含有 >0.1% (w/w) SVHC 的通报与供应链信息传递义务。",
            "core_threshold": "0.1% (w/w) / 1000 ppm",
            "items_count": "231 项主条目，覆盖 545 条细分物质与异构体组成员"
        },
        "EU_ROHS": {
            "name": REGULATION_NAMES["EU_ROHS"],
            "version": "2011/65/EU 及其修订指令 (EU) 2015/863",
            "scope": "电子电气设备 (EEE) 均质材料中的有害物质限制（铅、汞、镉、六价铬、PBB、PBDE、4项邻苯二甲酸酯 DEHP/BBP/DBP/DIBP）。",
            "core_threshold": "镉 (Cd): 0.01% (100 ppm)；其余 9 项受限物: 0.1% (1000 ppm)",
            "items_count": "10 大类受控物质，160 条材料级代表性化合物筛查明细"
        },
        "REACH_ANNEX_XVII": {
            "name": REGULATION_NAMES["REACH_ANNEX_XVII"],
            "version": "现行有效版本 (包含全部最新修订条目)",
            "scope": "欧盟市场上制造、投放市场或使用的特定危险物质、配制品和物品的强制限制/禁用。",
            "core_threshold": "按条目各异 (如特定用途禁用、0.005%~0.1% 限量等)",
            "items_count": "86 个限制条目，1868 条受限具体化学物质及组成员"
        },
        "BSBL": {
            "name": REGULATION_NAMES["BSBL"],
            "version": "BSBL v8.0 (2026-08-27 基线)",
            "scope": "鞋服、纺织、高分子涂层与材料制造行业严苛化学品限制标准（针对原料、助剂及成品）。",
            "core_threshold": "按材质分类设定（ppm ~ mg/kg 级严格限量）",
            "items_count": "51 个分类大类，1726 条细分受控化学物质全量总表"
        },
        "HSF_001": {
            "name": REGULATION_NAMES["HSF_001"],
            "version": "企业工程技术受控标准",
            "scope": "企业无有害物质 (Hazardous Substance Free) 绿色产品设计、原料准入及供应链合规筛查。",
            "core_threshold": "按企业材料判定标准 (不符合 / 豁免 / 禁用)",
            "items_count": "172 条具体受限化学品及映射 CAS 记录"
        },
        "AFPS_PAK": {
            "name": REGULATION_NAMES["AFPS_PAK"],
            "version": "AfPS GS 2019:01 PAK (自 2020-07-01 强制实施)",
            "scope": "德国 GS 认证关于消费品、玩具、工具及与皮肤接触材料中多环芳烃 (PAHs) 的严格迁移/含量限值。",
            "core_threshold": "依据 Category 1 到 Category 3b 分级限制 (0.2 mg/kg ~ 50 mg/kg)",
            "items_count": "15 种特定 PAH 单项物质 + 2 项合计限值 (共17行，分5类接触等级)"
        }
    }
    
    return info_map.get(key, {"error": f"未知的法规代码: {regulation}。支持: {list(info_map.keys())}"})

if __name__ == "__main__":
    # Run FastMCP via standard stdio transport
    mcp.run(transport="stdio")

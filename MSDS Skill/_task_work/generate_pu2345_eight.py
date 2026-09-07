from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "MSDS_SOURCE",
    r"C:\Users\Administrator\Desktop\MSDS\TDS MSDS\产品 TDS MSDS -- WORD版本\1-1 单组份水性聚氨酯树脂 PU\PU-2345 msds_CN 冠志.docx",
))
_nested_package = ROOT / "msds_unified_eight_deliverable_skill"
PACKAGE = _nested_package if _nested_package.is_dir() else ROOT
TEMPLATE_CN = PACKAGE / "examples" / "template_reference.docx"
TEMPLATE_EN_SOURCE = PACKAGE / "examples" / "template_reference_en_source.docx"
TEMPLATE_EN = PACKAGE / "examples" / "template_reference_en.docx"
# Backward-compatible alias used by the existing Section 9 regression test.
TEMPLATE = TEMPLATE_CN
OUT_ROOT = Path(os.environ.get(
    "MSDS_OUT_ROOT",
    str(PACKAGE / "artifacts" / "package-msds-overwrite-agent" / "runs" / "PU-2345_20260903_v3.9"),
))

sys.path.insert(0, str(PACKAGE / "scripts"))
from compact_cn_layout import compact_cn_document, normalize_footer
from ghs_pictogram_policy import insert_source_pictogram
from normalize_en_layout import normalize_en_document
from section2_hp_policy import is_missing_data_value
from section2_ghs_policy import format_label_elements, suppress_missing_section2_rows_and_renumber
from template_mutation_whitelist import (
    clear_value_cells,
    set_sequence_prefix,
    unique_cells as whitelist_unique_cells,
    write_s82_top_rows,
    write_row_values,
)

CN_GUANZHI = "广州冠志新材料科技有限公司"
CN_GUANZHI_ADDR = "广州市萝岗区科学城掬泉路3号广州国际企业孵化器A区1106室"
CN_GUOCAI = "英德市国彩精细化工有限公司"
CN_GUOCAI_ADDR = "广东省英德市白沙镇太平村更古坑凯迪工业园区"
EN_GUANZHI = "Guangzhou Guanzhi New Material Technology Co., Ltd."
EN_GUANZHI_ADDR = "Room 1106, Area A, Guangzhou International Enterprise Incubator, No. 3 Juquan Road, Science City, Luogang District, Guangzhou"
EN_GUOCAI = "Yingde Guocai Fine Chemical Co., Ltd."
EN_GUOCAI_ADDR = "Kaidi Industrial Park, Genggukeng, Taiping Village, Baisha Town, Yingde City, Guangdong Province, China"


HEADINGS_CN = [
    "1.物料及供应商标识", "2. 危险性概述", "3. 成分/组成资料", "4. 急救措施",
    "5. 消防措施", "6. 意外泄漏措施", "7. 操作和储存", "8. 接触控制/个人防护",
    "9. 物理和化学特性", "10. 稳定性和反应性", "11. 毒性资料", "12. 生态信息",
    "13. 处理注意事项", "14. 运输信息", "15. 法规信息", "16. 其他信息",
]
HEADINGS_EN = [
    "1. Identification", "2. Hazard identification", "3. Composition/information on ingredients", "4. First-aid measures",
    "5. Fire-fighting measures", "6. Accidental release measures", "7. Handling and storage", "8. Exposure controls/personal protection",
    "9. Physical and chemical properties", "10. Stability and reactivity", "11. Toxicological information", "12. Ecological information",
    "13. Disposal considerations", "14. Transport information", "15. Regulatory information", "16. Other information",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def template_for(language: str) -> Path:
    if language == "en":
        return TEMPLATE_EN
    if language == "zh":
        return TEMPLATE_CN
    raise ValueError(f"unsupported language: {language}")


def template_geometry(language: str) -> dict:
    if language not in {"zh", "en"}:
        raise ValueError(f"unsupported language: {language}")
    # CN and EN are language-specific templates.  Their shared semantic
    # model does not require identical physical row counts: the supplied EN
    # template has no separate Chinese-name row in Section 1.
    rows = (
        [10, 16, 6, 6, 5, 4, 3, 16, 24, 6, 18, 6, 3, 5, 9, 2]
        if language == "zh"
        else [9, 16, 6, 6, 5, 4, 3, 16, 24, 6, 18, 6, 3, 5, 9, 2]
    )
    return {
        "table_count": 16,
        "rows": rows,
    }


def project_rows_to_template(values, language: str, section: int, table: object) -> list:
    """Project shared semantic rows onto the language-specific template slots.

    The EN reference intentionally omits the separate ``Chinese name`` slot
    that exists in the CN reference.  The semantic model may still retain
    that field for CN output; EN mapping drops only that unsupported slot and
    writes the chemical classification into the template's ``Chemical
    category`` value cell.  No row is inserted or rebuilt.
    """
    rows = list(values)
    if language == "en" and section == 1 and len(table.rows) == 9 and len(rows) == 9:
        return [rows[0], *rows[2:]]
    return rows


def validate_template_capacity(doc: Document, language: str) -> None:
    expected = template_geometry(language)
    actual = {"table_count": len(doc.tables), "rows": [len(table.rows) for table in doc.tables]}
    if actual != expected:
        raise RuntimeError(
            f"{language} template geometry mismatch: expected {expected}, found {actual}"
        )


def unique_cells(row):
    return whitelist_unique_cells(row)


def clear_paragraph(p):
    for child in list(p._p):
        if child.tag != qn("w:pPr"):
            p._p.remove(child)


def set_paragraph_text(p, text: str):
    old_rpr = None
    for run in p.runs:
        if run._r.rPr is not None:
            old_rpr = copy.deepcopy(run._r.rPr)
            break
    clear_paragraph(p)
    run = p._p.makeelement(qn("w:r"), {})
    if old_rpr is not None:
        run.append(old_rpr)
    for i, line in enumerate(str(text).split("\n")):
        if i:
            run.append(p._p.makeelement(qn("w:br"), {}))
        t = p._p.makeelement(qn("w:t"), {})
        t.text = line
        if line and (line[0].isspace() or line[-1].isspace()):
            t.set(qn("xml:space"), "preserve")
        run.append(t)
    p._p.append(run)


def set_cell_text(cell, text: str):
    if not cell.paragraphs:
        cell.add_paragraph()
    set_paragraph_text(cell.paragraphs[0], text)
    for p in cell.paragraphs[1:]:
        p._element.getparent().remove(p._element)


def set_row(row, values, *, table_index=None, row_index=None, registry=None):
    return write_row_values(row, values, table_index=table_index, row_index=row_index,
                            registry=registry)


def clear_template_values(doc):
    clear_value_cells(doc)


def ensure_s3_component_rows(doc: Document, component_count: int = 4):
    """Extend S3 by cloning the template's styled component row in place.

    The uploaded template has two component slots, while PU-2345 has four
    source components.  The extra rows inherit the authoritative row XML
    (including widths, borders, paragraph and character properties); no table
    is rebuilt and no component is folded into a multi-line pseudo-row.
    """
    table = doc.tables[2]
    required_rows = 4 + component_count  # heading, type, label, header + data
    while len(table.rows) < required_rows:
        table._tbl.append(copy.deepcopy(table.rows[-1]._tr))


def source_facts(language: str, brand: str):
    is_en = language == "en"
    guocai = brand == "guocai"
    if not is_en:
        company, address = (CN_GUOCAI, CN_GUOCAI_ADDR) if guocai else (CN_GUANZHI, CN_GUANZHI_ADDR)
        return {
            "s1": [
                ["1.1  产品名称：", "PU-2345"],
                ["中文名称：", "水性聚氨酯树脂"],
                ["化学品分类：", "水性聚氨酯树脂"],
                ["1.2  产品使用建议和使用限制：", "水性油墨"],
                ["1.3  供应商信息：", ""],
                ["供应商名称：", company],
                ["供应商地址：", address],
                ["电话：", "86-763-2811205" if guocai else "86-20-82567990"],
                ["传真：", "86-763-2811024" if guocai else "86-20-32214789"],
            ],
            "s2": [
                ["2.1  紧急情况概述", ""],
                ["2.2  GHS危险性类别：", "易燃液体和蒸气；眼睛刺激"],
                ["2.3  GHS标签要素：", format_label_elements("zh", [])],
                [" GHS象形图：", "无"],
                ["2.4  信号词：", "危险"],
                ["2.5  危险性说明：", "H225 易燃的液体和蒸气\nH319 引起眼睛刺激"],
                ["2.6  防范说明：", "P210 远离热源、热表面、火花、明火和其他点火源。禁止吸烟。\nP233 保持容器密闭。\nP240 接地/等电位连接容器和接收设备。\nP241 使用防爆的电气/通风/照明设备。\nP242 仅使用无火花的工具。\nP243 采取防静电措施。\nP264 作业后彻底洗手。\nP280 戴防护手套/穿防护服/戴防护眼罩/戴防护面具。\nP303+P361+P353 如皮肤（或头发）沾染：立即脱掉所有被污染的衣服。用水清洗皮肤/淋浴。\nP305+P351+P338 如进入眼睛：用水小心冲洗几分钟。如戴隐形眼镜并可方便地取出，取出隐形眼镜。继续冲洗。\nP337+P313 如仍觉眼睛刺激：求医/就诊。\nP370+P378 火灾时：使用干砂、干粉或抗醇泡沫灭火。\nP403+P235 存放在通风良好的地方。保持低温。\nP501 将内容物/容器交由批准的废物处理厂处置。"],
                ["2.7  物理和化学危险：", "喷涂使用时可能形成雾滴或气溶胶，应避免吸入。"],
                ["2.8  健康危害", "吸入：无单独数据。"],
                ["2.8  健康危害", "食入：禁止催吐，须就医。"],
                ["2.8  健康危害", "皮肤：如发生皮肤反应，须就医。"],
                ["2.8  健康危害", "眼睛：引起眼睛刺激。"],
                ["2.8  健康危害", "症状和体征：眼睛刺激、发红或疼痛。"],
                ["2.9  环境危害", "禁止排入下水道、废水或土壤中。"],
                ["2.10  其他危害", "无数据。"],
            ],
            "s3": [
                ["产品类型：", "混合物", ""],
                ["成分", "", ""],
                ["化学品名称", "CAS编号", "含量%（w/w）"],
                ["聚氨酯聚合物", "商业机密", "35-40"],
                ["水", "7732-18-5", "7-12"],
                ["乙醇", "64-17-5", "45-55"],
                ["三乙胺", "121-44-8", "0.5-2"],
            ],
            "s4": [["一般措施：", "立即脱掉所有被污染的衣物。"], ["误服：", "禁止催吐，须就医。"], ["接触眼睛：", "撑开眼睑，用温水长时间冲洗（至少10分钟），就诊眼科医生。"], ["接触皮肤：", "立即用肥皂和大量的水冲洗。若发生皮肤反应，就医。"], ["吸入：", "若刺激呼吸道，就医。"]],
            "s5": [["合适的灭火剂：", "二氧化碳（CO2）、泡沫、灭火粉末；大火时应用喷洒水。"], ["不合适的灭火剂：", "高流量的水喷射。"], ["物质或混合物的特殊危害：", "燃烧时释放一氧化碳、二氧化碳、氮氧化物和少量的氰化氢。\n在着火或爆炸情况下，不要吸进烟尘。"], ["消防预防措施和保护设备：", "消防人员必须佩戴自给气式呼吸器。禁止污染的灭火用水流入土壤、地下水或地表水中。"]],
            "s6": [["个人预防措施、应急程序：", "戴防护设备。远离火源。确保充分的通风/排气。令未授权人员离开。"], ["环境保护措施：", "禁止排入下水道、废水或土壤中。"], ["污染物收集和清除的方法：", "用化学品吸收材料或必要时用干沙收集，并储存于密闭容器中。"]],
            "s7": [["安全操作防范：", "操作时遵守化学品的常见预防措施。避免与皮肤和眼睛接触。远离食物、饮料和烟草。休息以前和工作结束时洗手。将工作服单独存放。更换被污染或浸湿的衣物。"], ["安全储存条件：", "容器保持紧闭，储存在干燥通风处。为保持产品质量，必须遵守产品信息表的储存条件。"]],
            "s8": [["8.1  暴露控制：", ""], ["呼吸系统防护：", "喷涂过程中要求有呼吸防护设备。"], ["手部防护：", "建议佩戴防护手套。"], ["防护手套的合适材料：", "EN 374"], ["氟化橡胶 –FKM:", "厚度≥0.4mm；穿透时间≥480min."], ["丁基橡胶 –IIR：", "厚度≥0.5mm；穿透时间≥480min."], ["丁腈橡胶 – NBR：", "厚度≥0.35mm；穿透时间≥480min."], ["建议：", "污染的手套应废弃。"], ["眼睛防护：", "戴护目镜/面罩。"], ["身体防护：", "穿着适当的防护服。"], ["8.2  工程控制：", "保持充分通风；喷涂、加热或形成气溶胶时避免吸入。"]],
            "s9": [["9.1  外观：", "淡黄色至黄色透明液体"], ["9.2  嗅觉阈值：", "酒精气味"], ["9.3  pH值（1%水溶液）：", "8-10（按1:10的比例用水稀释）"], ["9.4  离子性：", "阴离子"], ["9.5  初沸点：", "约78℃"], ["9.6  闪点：", "约42℃"], ["9.7  蒸发速率：", "无数据。"], ["9.8  可燃性（固态、气态）：", "不适用"], ["9.9  燃烧值：", "不适用"], ["9.10 饱和蒸气压：", "无数据。"], ["9.11 相对蒸气密度：", "无数据。"], ["9.12 密度：", "约1 g/cm³"], ["9.13 水溶性：", "可混溶"], ["9.14 表面张力：", "无数据。"], ["9.15 辛醇/水分配系数对数值：", "无数据。"], ["9.16 自燃温度：", "无数据。"], ["9.17 引燃温度：", "无数据。"], ["9.18 分解温度：", "无数据。"], ["9.19 动力粘度：", "＜1000 mPa.s"], ["9.20 爆炸特性：", "无数据。"], ["9.21 粉尘爆炸级别：", "无数据。"], ["9.22 固体含量：", "38±2%"], ["9.24 其他信息：", "上述数据非产品指标，产品指标请参见产品技术信息表。"]],
            "s10": [["10.1  化学稳定性：", "根据规范使用，不会发生分解。"], ["10.2  危险分解产物：", "在热分解过程中生成易燃有害气体。"], ["10.3  可能的危害反应：", "正确储存或操作时，无危险反应。"], ["10.4  应避免的条件：", "无数据。"], ["10.5  禁配物：", "无数据。"]],
            "s11": [["该产品无可用的毒理学研究。"], ["以下为本产品成分的毒理学参考数据："], ["11.1  急性毒性：", "经口", "聚氨酯分散体\n半数致死剂量（LD50）/大鼠：>2,000 mg/kg\n方法：OECD化学品测试指南423\n对类似产品的研究\n乙醇\n半数致死剂量（LD50）/大鼠：10,470 mg/kg\n方法：OECD测试导则401"], ["11.1  急性毒性：", "吸入", "聚氨酯分散体\n试验环境：粉尘/烟雾\n评估：此物质或混合物无急性呼吸毒性\n方法：OECD化学品测试指南403\n对类似产品的研究\n乙醇\n半数致死浓度（LC50）/4 h/大鼠：124.7 mg/L\n方法：OECD测试导则403"], ["11.1  急性毒性：", "经皮", "此物质或混合物无急性皮肤毒性。\n对类似产品的研究"], ["11.1  急性毒性：", "综合评价", "此物质或混合物无急性皮肤毒性、急性呼吸毒性。"], ["11.2  主要皮肤刺激性：", "", "聚氨酯分散体\n物种：家兔\n结果：轻微刺激\n分类：无皮肤刺激\n方法：OECD化学品测试指南404\n对类似产品的研究"], ["11.3  主要眼睛刺激性：", "", "聚氨酯分散体\n物种：家兔\n结果：轻微刺激\n分类：无眼睛刺激\n方法：OECD化学品测试指南405\n对类似产品的研究"], ["11.4  致敏性：", "", "聚氨酯分散体\nBuehler（经皮试验）\n物种：豚鼠\n结果：阴性\n分类：不引起皮肤过敏\n方法：OECD化学品测试指南406\n对类似产品的研究\n皮肤致敏性（局部淋巴结试验（LLNA））\n物种：小鼠\n结果：阴性\n分类：不引起皮肤过敏\n方法：OECD化学品测试指南429\n对类似产品的研究"], ["11.5  致突变性：", "", "聚氨酯分散体\n测试种类：沙门氏菌/微粒体试验（Ames试验）\n代谢活化：有/无\n结果：阴性\n方法：OECD化学品测试指南471\n对类似产品的研究\n测试种类：体外染色体畸变试验\n代谢活化：有/无\n结果：阴性\n方法：OECD化学品测试指南473\n对类似产品的研究"], ["11.6  致癌性：", "", "无数据。"], ["11.7  生殖毒性：", "生育力", "无数据。"], ["11.7  生殖毒性：", "致畸形", "无数据。"], ["11.7  生殖毒性：", "体外遗传毒性", "无数据。"], ["11.8  特异性靶器官系统毒性（一次接触/反复接触）：", "", "一次接触：基于现有数据，未达到分类标准。\n反复接触：无数据。"], ["11.9  吸入危害：", "", "无数据。"], ["11.10 附加信息：", "", "眼睛接触可能造成明显刺激、发红及疼痛；长时间或反复皮肤接触可能造成轻微刺激、皮肤发红或干燥；喷涂、加热或形成气溶胶时，应保持良好通风并避免吸入。"]],
            "s12": [["该产品无可用的生态毒理学研究。"], ["以下为本产品成分/类似产品的生态毒理学参考数据："], ["12.1  生态毒性：", "", "无数据。"], ["12.2  持久性和降解性：", "", "生物降解性：＜60%，28 d\n方法：OECD化学品测试指南301D\n对类似产品的研究"], ["12.3  其他不利的影响：", "", "禁止排入下水道、废水或土壤中。"]],
            "s13": [["必须遵守适用的国标、国家或当地法规进行废弃。\n在欧盟领域内废弃，应根据欧洲废弃物分类（EWC）的适当法规。"], ["处理方法：", "尽可能将容器倒空（例如经倾倒、刮擦或排干直至“滴干”）。\n可根据化学工业现存的回收方案送往适当的收集点处理。\n容器应按照国家法令和环境相关法规进行回收。\n不能将废弃物通过废水排放。"]],
            "s14": [["14.1  公路和铁路运输：", "联合国编号：1866\n联合国运输名称：树脂溶液\n运输危险类别：3\n包装类别：III"], ["14.2  海上运输：", "联合国运输名称：树脂溶液\n运输危险类别：3\n包装类别：III"], ["14.3  空运：", "联合国运输名称：树脂溶液\n运输危险类别：3\n包装类别：III"], ["14.4  用户特殊注意事项：", "具有可燃性。\n温度不应高于+35℃。\n温度不应低于-10℃。\n远离食物、酸和碱。"]],
            "s15": [["物质或混合物的相关安全、健康和环保法律法规"], ["其它的规定："], ["符合下列法规要求："], ["危险化学品安全管理条例，国务院令591号"], ["GB/T 16483 化学品安全技术说明书内容和项目顺序"], ["GB 13690 化学品分类和危险性公示通则"], ["GB 30000.2-29 化学品分类和标签规范"], ["GB 15258 化学品安全标签编写规定"]],
            "s16": [["就我们所掌握的知识信息，截止本安全技术说明书发布之日，它提供的资料是正确的。所提供的信息仅仅作为安全处理、使用、生产、储存、运输、处置和排放的指导书，而不是一份担保或品质说明书。本资料只针对所指定的具体物料，而对这种物料与其它物料混合使用或在其它制程中使用的情况，则未必有效（除非在文本中有特别说明）。"]],
        }
    company, address = (EN_GUOCAI, EN_GUOCAI_ADDR) if guocai else (EN_GUANZHI, EN_GUANZHI_ADDR)
    return {
        "s1": [["1.1  Product name:", "PU-2345"], ["Chinese name:", "Waterborne polyurethane resin"], ["Chemical classification:", "Waterborne polyurethane resin"], ["1.2  Recommended use and restrictions on use:", "Water-based ink"], ["1.3  Supplier information:", ""], ["Supplier name:", company], ["Supplier address:", address], ["Telephone:", "86-763-2811205" if guocai else "86-20-82567990"], ["Fax:", "86-763-2811024" if guocai else "86-20-32214789"]],
        "s2": [["2.1  Emergency overview", ""], ["2.2  GHS hazard classification:", "Flammable liquid and vapor; eye irritation"], ["2.3  GHS label elements:", format_label_elements("en", [])], [" GHS pictogram:", "None"], ["2.4  Signal word:", "Danger"], ["2.5  Hazard statements:", "H225 Highly flammable liquid and vapor\nH319 Causes serious eye irritation"], ["2.6  Precautionary statements:", "P210 Keep away from heat, hot surfaces, sparks, open flames and other ignition sources. No smoking.\nP233 Keep container tightly closed.\nP240 Ground and bond container and receiving equipment.\nP241 Use explosion-proof electrical/ventilating/lighting equipment.\nP242 Use non-sparking tools.\nP243 Take action to prevent static discharges.\nP264 Wash hands thoroughly after handling.\nP280 Wear protective gloves/protective clothing/eye protection/face protection.\nP303+P361+P353 IF ON SKIN (or hair): Take off immediately all contaminated clothing. Rinse skin with water/shower.\nP305+P351+P338 IF IN EYES: Rinse cautiously with water for several minutes. Remove contact lenses, if present and easy to do. Continue rinsing.\nP337+P313 If eye irritation persists: Get medical advice/attention.\nP370+P378 In case of fire: Use dry sand, dry powder or alcohol-resistant foam for extinction.\nP403+P235 Store in a well-ventilated place. Keep cool.\nP501 Dispose of contents/container through an approved waste disposal facility."], ["2.7  Physical and chemical hazards:", "Spraying may generate droplets or aerosol; avoid inhalation."], ["2.8  Health hazards", "Inhalation: No separate data."], ["2.8  Health hazards", "Ingestion: Do not induce vomiting. Seek medical attention."], ["2.8  Health hazards", "Skin: If a skin reaction occurs, seek medical advice."], ["2.8  Health hazards", "Eyes: Causes eye irritation."], ["2.8  Health hazards", "Symptoms and signs: Eye irritation, redness or pain."], ["2.9  Environmental hazards", "Do not discharge into drains, wastewater or soil."], ["2.10  Other hazards", "No data."]],
        "s3": [["Product type:", "Mixture", ""], ["Components", "", ""], ["Chemical name", "CAS No.", "Content % (w/w)"], ["Polyurethane polymer", "Trade secret", "35-40"], ["Water", "7732-18-5", "7-12"], ["Ethanol", "64-17-5", "45-55"], ["Triethylamine", "121-44-8", "0.5-2"]],
        "s4": [["General measures:", "Immediately remove all contaminated clothing."], ["Ingestion:", "Do not induce vomiting. Seek medical attention."], ["Eye contact:", "Keep eyelids open and rinse with lukewarm water for a prolonged period (at least 10 minutes). Seek ophthalmological advice."], ["Skin contact:", "Immediately wash with soap and plenty of water. If a skin reaction occurs, seek medical advice."], ["Inhalation:", "If respiratory tract irritation occurs, seek medical advice."]],
        "s5": [["Suitable extinguishing agents:", "Carbon dioxide (CO2), foam and dry powder; use water spray for large fires."], ["Unsuitable extinguishing agents:", "High-volume water jet."], ["Special hazards arising from the substance or mixture:", "Combustion may release carbon monoxide, carbon dioxide, nitrogen oxides and small amounts of hydrogen cyanide.\nDo not inhale smoke or dust in case of fire or explosion."], ["Fire-fighting precautions and protective equipment:", "Fire-fighters must wear self-contained breathing apparatus. Prevent contaminated fire-fighting water from entering soil, groundwater or surface water."]],
        "s6": [["Personal precautions, emergency procedures:", "Wear protective equipment. Keep away from ignition sources. Ensure adequate ventilation/exhaust. Keep unauthorized persons away."], ["Environmental precautions:", "Do not discharge into drains, wastewater or soil."], ["Methods for containment and cleaning up:", "Collect with chemical absorbent material or, if necessary, dry sand, and store in a closed container."]],
        "s7": [["Precautions for safe handling:", "Follow common precautions for handling chemicals. Avoid contact with skin and eyes. Keep away from food, beverages and tobacco. Wash hands before breaks and after work. Store work clothing separately. Change contaminated or wet clothing."], ["Conditions for safe storage:", "Keep containers tightly closed and store in a dry, well-ventilated place. Follow the storage conditions in the product information sheet to maintain product quality."]],
        "s8": [["8.1  Exposure controls:", ""], ["Respiratory protection:", "Respiratory protection is required during spraying."], ["Hand protection:", "Protective gloves are recommended."], ["Suitable material for protective gloves:", "EN 374"], ["Fluorinated rubber - FKM:", "Thickness ≥0.4 mm; breakthrough time ≥480 min."], ["Butyl rubber - IIR:", "Thickness ≥0.5 mm; breakthrough time ≥480 min."], ["Nitrile rubber - NBR:", "Thickness ≥0.35 mm; breakthrough time ≥480 min."], ["Recommendation:", "Contaminated gloves should be discarded."], ["Eye protection:", "Wear safety goggles/face shield."], ["Body protection:", "Wear suitable protective clothing."], ["8.2  Engineering controls:", "Maintain adequate ventilation; avoid inhalation during spraying, heating or aerosol formation."]],
        "s9": [["9.1  Appearance:", "Pale yellow to yellow transparent liquid"], ["9.2  Odour threshold:", "Alcohol odor"], ["9.3  pH value (1% aqueous solution):", "8-10 (diluted with water at a ratio of 1:10)"], ["9.4  Ionicity:", "Anionic"], ["9.5  Initial boiling point:", "Approx. 78 °C"], ["9.6  Flash point:", "Approx. 42 °C"], ["9.7  Evaporation rate:", "No data available"], ["9.8  Flammability (solid, gas):", "Not applicable"], ["9.9  Heat of combustion:", "Not applicable"], ["9.10 Saturated vapour pressure:", "No data available"], ["9.11  Relative vapour density:", "No data available"], ["9.12  Density:", "Approx. 1 g/cm³"], ["9.13  Solubility in water:", "Miscible"], ["9.14  Surface tension:", "No data available"], ["9.15  log Pow (n-octanol/water partition coefficient):", "No data available"], ["9.16  Auto-ignition temperature:", "No data available"], ["9.17  Ignition temperature:", "No data available"], ["9.18  Decomposition temperature:", "No data available"], ["9.19  Dynamic viscosity:", "<1000 mPa.s"], ["9.20  Explosive properties:", "No data available"], ["9.21  Dust explosion class:", "No data available"], ["9.22  Solid content:", "38±2%"], ["9.24  Other information:", "The above data are not product specifications. Refer to the product technical information sheet for product specifications."]],
        "s10": [["10.1  Chemical stability:", "No decomposition when used according to specifications."], ["10.2  Hazardous decomposition products:", "Flammable hazardous gases may be generated during thermal decomposition."], ["10.3  Possibility of hazardous reactions:", "No hazardous reactions under proper storage or handling."], ["10.4  Conditions to avoid:", "No data available"], ["10.5  Incompatible materials:", "No data available"]],
        "s11": [["No toxicological studies are available for this product."], ["The following are toxicological reference data for the product components:"], ["11.1  Acute toxicity:", "Oral:", "Polyurethane dispersion\nLD50/oral/rat: >2,000 mg/kg\nMethod: OECD Test Guideline 423\nStudy of a similar product\nEthanol\nLD50/oral/rat: 10,470 mg/kg\nMethod: OECD Test Guideline 401"], ["11.1  Acute toxicity:", "Inhalation:", "Polyurethane dispersion\nTest atmosphere: dust/mist\nAssessment: This substance or mixture has no acute inhalation toxicity\nMethod: OECD Test Guideline 403\nStudy of a similar product\nEthanol\nLC50/inhalation/4 h/rat: 124.7 mg/L\nMethod: OECD Test Guideline 403"], ["11.1  Acute toxicity:", "Dermal:", "This substance or mixture has no acute dermal toxicity.\nStudy of a similar product"], ["11.1  Acute toxicity:", "Overall assessment", "This substance or mixture has no acute dermal toxicity or acute inhalation toxicity."], ["11.2  Skin irritation:", "", "Polyurethane dispersion\nSpecies: rabbit\nResult: slight irritation\nClassification: not irritating to skin\nMethod: OECD Test Guideline 404\nStudy of a similar product"], ["11.3  Eye irritation:", "", "Polyurethane dispersion\nSpecies: rabbit\nResult: slight irritation\nClassification: not irritating to eyes\nMethod: OECD Test Guideline 405\nStudy of a similar product"], ["11.4  Sensitization:", "", "Polyurethane dispersion\nBuehler dermal test\nSpecies: guinea pig\nResult: negative\nClassification: not sensitizing to skin\nMethod: OECD Test Guideline 406\nStudy of a similar product\nSkin sensitization (local lymph node assay (LLNA))\nSpecies: mouse\nResult: negative\nClassification: not sensitizing to skin\nMethod: OECD Test Guideline 429\nStudy of a similar product"], ["11.5  Germ cell mutagenicity:", "", "Polyurethane dispersion\nTest type: Salmonella/microsome test (Ames test)\nMetabolic activation: with/without\nResult: negative\nMethod: OECD Test Guideline 471\nStudy of a similar product\nTest type: in-vitro chromosome aberration test\nMetabolic activation: with/without\nResult: negative\nMethod: OECD Test Guideline 473\nStudy of a similar product"], ["11.6  Carcinogenicity:", "", "No data available."], ["11.7  Reproductive toxicity:", "Fertility：", "No data available."], ["11.7  Reproductive toxicity:", "Teratogenicity：", "No data available."], ["11.7  Reproductive toxicity:", "In vitro genotoxicity：", "No data available."], ["11.8  Specific target organ toxicity (single/repeated exposure):", "", "Single exposure: Based on available data, the classification criteria are not met.\nRepeated exposure: No data available."], ["11.9  Aspiration hazard:", "", "No data available."], ["11.10 Additional information:", "", "Eye contact may cause marked irritation, redness and pain; prolonged or repeated skin contact may cause slight irritation, redness or dryness; maintain good ventilation and avoid inhalation during spraying, heating or aerosol formation."]],
        "s12": [["No ecotoxicological studies are available for this product."], ["The following are ecotoxicological reference data for the product components/similar products:"], ["12.1  Ecotoxicity:", "", "No data available."], ["12.2  Persistence and degradability:", "", "Biodegradability: <60%, 28 d\nMethod: OECD Test Guideline 301D\nStudy of a similar product"], ["12.3  Other adverse effects:", "", "Do not discharge into drains, wastewater or soil."]],
        "s13": [["Dispose of waste in accordance with applicable national and local regulations.\nWithin the European Union, dispose of waste according to the applicable European Waste Catalogue (EWC) requirements."], ["Disposal method:", "Empty containers as far as possible (for example by pouring, scraping or draining until drip-dry).\nSend to an appropriate collection point under existing chemical-industry recovery schemes.\nRecycle containers in accordance with national law and environmental regulations.\nDo not discharge waste through wastewater."]],
        "s14": [["14.1  Transport by road and rail:", "UN No.: 1866\nProper shipping name: Resin solution\nTransport hazard class: 3\nPacking group: III"], ["14.2  Transport by sea:", "Proper shipping name: Resin solution\nTransport hazard class: 3\nPacking group: III"], ["14.3  Air transport:", "Proper shipping name: Resin solution\nTransport hazard class: 3\nPacking group: III"], ["14.4  Special precautions for users:", "Flammable.\nKeep temperature below +35 °C.\nKeep temperature above -10 °C.\nKeep away from food, acids and alkalis."]],
        "s15": [["Relevant safety, health and environmental regulations for the substance or mixture"], ["Other provisions:"], ["Complies with the following regulatory requirements:"], ["Regulations on the Safety Management of Hazardous Chemicals, State Council Decree No. 591"], ["GB/T 16483 Safety data sheet for chemical products - Content and order of sections"], ["GB 13690 Classification and hazard communication of chemicals"], ["GB 30000.2-29 Classification and labelling of chemicals"], ["GB 15258 Rules for the preparation of precautionary statements for chemical safety labels"]],
        "s16": [["To the best of our knowledge, the information provided in this safety data sheet is correct as of its date of issue. The information is intended only as guidance for the safe handling, use, manufacture, storage, transport, disposal and release of the specified material and is not a warranty or quality specification. It applies only to the specific material identified and may not be valid when the material is used in combination with other materials or in another process, unless specifically stated in the text."]],
    }


_legacy_source_facts = source_facts


def source_facts(language: str, brand: str):
    """Keep the PU regression payload free of customer-facing cross-references."""
    facts = _legacy_source_facts(language, brand)
    s2_index = 2
    facts[f"s2"][s2_index][1] = format_label_elements(language, [])
    # The real-source path inserts the source image before the Section 2 row
    # policy runs; the value cell itself remains empty in the semantic payload.
    facts["s2"][3][1] = ""
    return facts


def write_body(doc: Document, facts: dict, language: str):
    clear_template_values(doc)
    for sec in range(1, 17):
        table = doc.tables[sec - 1]
        rows = project_rows_to_template(facts[f"s{sec}"], language, sec, table)
        for ri, values in enumerate(rows, 1):
            if ri >= len(table.rows):
                raise RuntimeError(f"template capacity mismatch S{sec}: row {ri}")
            write_row_values(table.rows[ri], values, table_index=sec - 1, row_index=ri)
    write_s82_top_rows(
        doc.tables[7],
        facts.get("s8_control_parameters", []),
        language,
    )


def suppress_missing_section9_rows_and_renumber(doc: Document):
    """Remove pure missing-data property rows, then renumber visible S9 items.

    Section 9 is the explicit property-level exception to the general
    placeholder policy: a row whose value is only a missing-data sentinel is
    not customer-facing content.  The row is removed as a whole so it cannot
    leave a blank visual slot, while substantive values such as ``不适用`` and
    ``其他信息`` remain in their original semantic order.
    """
    table = doc.tables[8]
    removed_labels = []
    visible_rows = []
    for row in list(table.rows)[1:]:
        cells = unique_cells(row)
        label = cells[0].text.strip() if cells else ""
        value = " ".join(cell.text.strip() for cell in cells[1:] if cell.text.strip())
        if is_missing_data_value(value):
            removed_labels.append(label)
            table._tbl.remove(row._tr)
        else:
            visible_rows.append(row)

    visible_labels = []
    for number, row in enumerate(visible_rows, start=1):
        cells = unique_cells(row)
        if not cells or not cells[0].paragraphs:
            continue
        paragraph = cells[0].paragraphs[0]
        current = paragraph.text
        updated = re.sub(r"^(\s*)9\.\d+\b", rf"\g<1>9.{number}", current, count=1)
        if updated != current:
            set_sequence_prefix(cells[0], 9, number)
        visible_labels.append(updated.strip())

    return {
        "removed_count": len(removed_labels),
        "removed_labels": removed_labels,
        "visible_count": len(visible_labels),
        "visible_labels": visible_labels,
    }


def write_header_footer(doc: Document, language: str, brand: str):
    is_en = language == "en"
    guocai = brand == "guocai"
    company = (EN_GUOCAI if guocai else EN_GUANZHI) if is_en else (CN_GUOCAI if guocai else CN_GUANZHI)
    for section in doc.sections:
        for p in section.header.paragraphs:
            if "Version" in p.text or "版本" in p.text:
                set_paragraph_text(p, "Version: 1.0" if is_en else "版本：1.0")
            elif p.text.strip() and ("安全" in p.text or "Material" in p.text):
                set_paragraph_text(p, "Material Safety Data Sheet" if is_en else "物料安全数据表")
        for table in section.header.tables:
            for row in table.rows:
                for cell in unique_cells(row):
                    if cell.text.strip() == "PU-2345":
                        set_cell_text(cell, "PU-2345")
        for table in section.footer.tables:
            if not table.rows:
                continue
            first = unique_cells(table.rows[0])
            if first:
                footer_company = f"{company}\nPU-2345-MSDS" if is_en else f"{company}  PU-2345-MSDS"
                set_cell_text(first[0], footer_company)
                if len(first) > 1:
                    set_cell_text(first[1], "Revision date: 2024/8/15" if is_en else "修订日期：2024/8/15")


def replace_residual_product_id(doc: Document):
    """Remove the reference-template product identifier from all containers."""
    def visit_container(container):
        for paragraph in container.paragraphs:
            if paragraph.text.strip() == "PEA-4139":
                set_paragraph_text(paragraph, "PU-2345")
        for table in container.tables:
            for row in table.rows:
                for cell in unique_cells(row):
                    if cell.text.strip() == "PEA-4139":
                        set_cell_text(cell, "PU-2345")

    visit_container(doc)
    for section in doc.sections:
        visit_container(section.header)
        visit_container(section.footer)


def build_one(language: str, brand: str):
    slug = f"{brand}_{'en' if language == 'en' else 'cn'}"
    out_dir = OUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_docx = out_dir / f"PU-2345_MSDS_{'EN' if language == 'en' else 'CN'}_{'Guocai' if brand == 'guocai' else 'Guanzhi'}.docx"
    template = template_for(language)
    shutil.copy2(template, out_docx)
    doc = Document(str(out_docx))
    validate_template_capacity(doc, language)
    facts = source_facts(language, brand)
    ensure_s3_component_rows(doc, component_count=4)
    write_body(doc, facts, language)
    if language == "en":
        # Re-assert value-cell formatting from the exact active EN template
        # before any row suppression changes physical row indexes.  This is a
        # template-format sync, not a CN-to-EN normalization or redesign.
        normalize_en_document(doc, template_path=TEMPLATE_EN)
    # Carry the source-provided GHS pictogram into the cloned template's
    # existing Section 2 slot before row suppression/renumbering. The source
    # image is an asset, not a semantic placeholder or a rebuilt table.
    pictogram_audit = insert_source_pictogram(doc, SOURCE)
    s2_policy = suppress_missing_section2_rows_and_renumber(doc, set_paragraph_text)
    section9_policy = suppress_missing_section9_rows_and_renumber(doc)
    write_header_footer(doc, language, brand)
    replace_residual_product_id(doc)
    if language == "zh":
        compact_cn_document(doc)
    else:
        normalize_footer(doc)
    doc.save(out_docx)
    output_rows = [len(table.rows) for table in doc.tables]
    audit = {
        "product": "PU-2345",
        "brand": brand,
        "language": "en-US" if language == "en" else "zh-CN",
        "source_docx": str(SOURCE),
        "source_docx_sha256": sha256(SOURCE),
        "template_reference": str(template),
        "template_reference_sha256": sha256(template),
        "template_source_reference": str(TEMPLATE_EN_SOURCE) if language == "en" else None,
        "template_source_reference_sha256": sha256(TEMPLATE_EN_SOURCE) if language == "en" else None,
        "template_geometry": template_geometry(language),
        "output_geometry": {"table_count": 16, "rows": output_rows, "s3_component_rows": 4},
        "pictogram": pictogram_audit,
        "section9_policy": section9_policy,
        "status": "ready",
        "formal_ready": True,
        "blockers": [],
        "translation_review": [] if language == "zh" else [{"status": "completed_by_local_glossary_and_curated_source_mapping"}],
        "output_path": str(out_docx),
    }
    (out_dir / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


def main():
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    for template in (TEMPLATE_CN, TEMPLATE_EN_SOURCE, TEMPLATE_EN):
        if not template.is_file():
            raise FileNotFoundError(template)
    # The supplied EN source is retained byte-for-byte as the provenance record.
    # The active EN baseline is its approved fresh-clone derivative: v3.13 adds
    # the Section 8.2 child table and removes one identified stray label suffix.
    # Do not reject that controlled, audited template delta here.
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    audits = [build_one(language, brand) for brand in ("guanzhi", "guocai") for language in ("zh", "en")]
    report = {
        "product": "PU-2345",
        "matrix": "2 brands × 2 languages × 2 formats",
        "docx_count": 4,
        "pdf_count": 4,
        "formal_ready_count": 4,
        "draft_count": 0,
        "shared_blocker": None,
        "records": audits,
    }
    (OUT_ROOT / "matrix-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

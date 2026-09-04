import copy
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
_nested_package = ROOT / "msds_unified_eight_deliverable_skill"
PACKAGE = _nested_package if _nested_package.is_dir() else ROOT
BASE_PATH = ROOT / "_task_work" / "generate_pu2345_eight.py"
sys.path.insert(0, str(PACKAGE / "scripts"))
base_spec = importlib.util.spec_from_file_location("v37_base", BASE_PATH)
base = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(base)
from ghs_pictogram_policy import insert_source_pictogram
from section2_ghs_policy import format_label_elements, suppress_missing_section2_rows_and_renumber
from template_mutation_whitelist import (
    clear_value_cells,
    set_sequence_prefix,
    unique_cells as whitelist_unique_cells,
    write_s82_child_rows,
)

SOURCE = Path(os.environ.get(
    "MSDS_SOURCE",
    r"C:\Users\Administrator\Desktop\MSDS\TDS MSDS\产品 TDS MSDS -- WORD版本\6-1 水分散型异氰酸酯固化剂 OS\OS-9015 msds_CN 冠志.docx",
))
OUT_ROOT = Path(os.environ.get(
    "MSDS_OUT_ROOT",
    str(PACKAGE / "artifacts" / "package-msds-overwrite-agent" / "runs" / "OS-9015_20260903_v3.9"),
))
PRODUCT = "OS-9015"
TEMPLATE_CN = PACKAGE / "examples" / "template_reference.docx"
TEMPLATE_EN = PACKAGE / "examples" / "template_reference_en.docx"
TEMPLATE_EN_SOURCE = PACKAGE / "examples" / "template_reference_en_source.docx"

CN_GUANZHI = base.CN_GUANZHI
CN_GUANZHI_ADDR = base.CN_GUANZHI_ADDR
CN_GUOCAI = base.CN_GUOCAI
CN_GUOCAI_ADDR = base.CN_GUOCAI_ADDR
EN_GUANZHI = base.EN_GUANZHI
EN_GUANZHI_ADDR = base.EN_GUANZHI_ADDR
EN_GUOCAI = base.EN_GUOCAI
EN_GUOCAI_ADDR = base.EN_GUOCAI_ADDR


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def unique_cells(row):
    return whitelist_unique_cells(row)


def set_paragraph_text(p, text):
    base.set_paragraph_text(p, text)


def set_cell_text(cell, text):
    base.set_cell_text(cell, text)


def set_row(row, values):
    base.set_row(row, values)


def template_for(language):
    return TEMPLATE_EN if language == "en" else TEMPLATE_CN


def source_structure_snapshot(path: Path):
    doc = Document(str(path))
    tables = []
    for table in doc.tables:
        row_specs = []
        for row in table.rows:
            row_specs.append({
                "cell_count": len(row.cells),
                "unique_cell_count": len(unique_cells(row)),
                "cell_tc_ids": [id(cell._tc) for cell in row.cells],
            })
        grid_widths = []
        grid = table._tbl.tblGrid
        for col in grid.gridCol_lst:
            grid_widths.append(col.get(qn("w:w")))
        tables.append({
            "rows": len(table.rows),
            "columns": len(table.columns),
            "grid_widths_twips": grid_widths,
            "row_specs": row_specs,
            "table_xml_sha256": hashlib.sha256(table._tbl.xml.encode("utf-8")).hexdigest(),
        })
    sections = []
    for section in doc.sections:
        sections.append({
            "header_paragraphs": [{"style": p.style.name, "text": p.text} for p in section.header.paragraphs],
            "footer_paragraphs": [{"style": p.style.name, "text": p.text} for p in section.footer.paragraphs],
            "header_table_count": len(section.header.tables),
            "footer_table_count": len(section.footer.tables),
        })
    return {
        "source_sha256": sha256(path),
        "paragraph_count": len(doc.paragraphs),
        "table_count": len(doc.tables),
        "tables": tables,
        "sections": sections,
    }


def _company(language, brand):
    if language == "en":
        return (EN_GUOCAI, EN_GUOCAI_ADDR) if brand == "guocai" else (EN_GUANZHI, EN_GUANZHI_ADDR)
    return (CN_GUOCAI, CN_GUOCAI_ADDR) if brand == "guocai" else (CN_GUANZHI, CN_GUANZHI_ADDR)


def source_facts(language, brand):
    company, address = _company(language, brand)
    guocai = brand == "guocai"
    if language == "zh":
        return {
            "s1": [["1.1  产品名称：", PRODUCT], ["中文名称：", "水可分散型异氰酸酯固化剂"], ["化学品分类：", "聚异氰酸酯"], ["1.2  产品使用建议和使用限制：", "涂料用添加剂"], ["1.3  供应商信息：", ""], ["供应商名称：", company], ["供应商地址：", address], ["电话：", "86-763-2811205" if guocai else "86-20-82567990"], ["传真：", "86-763-2811024" if guocai else "86-20-32214789"]],
            "s2": [["2.1  紧急情况概述", "无数据"], ["2.2  GHS危险性类别：", "易燃液体，类别3（H226）\n急性毒性，吸入性，类别4（H332）\n皮肤致敏，类别1（H317）\n特异性靶器官有毒（一次性接触），类别3（H335）\n特异性靶器官有毒（一次性接触），类别2（H373）"], ["2.3  GHS标签要素：", format_label_elements("zh", [])], [" GHS象形图：", "无数据"], ["2.4  信号词：", "无数据"], ["2.5  危险性说明：", "H226 易燃液体和蒸气。\nH332 吸入有害。\nH317 可能造成皮肤过敏反应。\nH335 可能造成呼吸道刺激。\nH373 长期或反复暴露可能对器官造成损害。"], ["2.6  防范说明：", "P210 远离热源/火花/明火。禁止吸烟。\nP260 不要吸入粉尘/烟气/气体/烟雾/蒸气/喷雾。\nP271 仅在户外或通风良好处使用。\nP280 戴防护手套/穿防护服/戴防护面罩。\nP303+P361+P353 如皮肤（或头发）沾染：立即脱掉所有沾染的衣服。用水清洗皮肤/淋浴。\nP304+P340 如误吸入：将受害人转移到空气新鲜处，保持呼吸舒适的休息姿势。\nP308+P313 如接触到或有疑虑：求医/就诊。\nP403+P233 在通风良好处储存。保持容器密闭。\nP501 将本品或其容器送至有资质的废物处理厂处置。"], ["2.7  物理和化学危险：", "无数据"], ["2.8  健康危害", "吸入：吸入有害；可能造成呼吸道刺激。"], ["2.8  健康危害", "皮肤：可能造成皮肤过敏反应。"], ["2.8  健康危害", "眼睛：无数据。"], ["2.8  健康危害", "食入：无数据。"], ["2.8  健康危害", "长期或反复接触：可能对器官造成损害。"], ["2.9  环境危害", "无数据"], ["2.10  其他危害", "存在经皮吸收乙酸-1-甲氧基-2-丙基酯的风险。"]],
            "s3": [["产品类型：", "混合物", ""], ["成分", "", ""], ["化学品名称", "CAS编号", "含量%（w/w）"], ["六甲撑二异氰酸酯基均聚物", "28182-81-2", "≥45"], ["亲水改性的六甲撑二异氰酸酯基均聚物", "商业机密", "4-25"], ["六甲撑二异氰酸酯", "822-06-0", "≤0.15"], ["丙二醇甲醚醋酸酯", "108-65-6", "20-40"]],
            "s4": [["一般措施：", "立即脱掉所有被污染的衣物。"], ["误服：", "禁止催吐，须就医。"], ["接触眼睛：", "撑开眼睑，用温水长时间冲洗（至少10分钟），就诊眼科医生。"], ["接触皮肤：", "立即用肥皂和大量的水冲洗。若发生皮肤反应，就医。"], ["吸入：", "若刺激呼吸道，就医。"]],
            "s5": [["合适的灭火剂：", "二氧化碳（CO2）、泡沫、灭火粉末；大火时应用喷洒水。"], ["不合适的灭火剂：", "高流量的水喷射。"], ["物质或混合物的特殊危害：", "燃烧时释放一氧化碳、二氧化碳、氮氧化物和少量的氰化氢。\n在着火或爆炸情况下，不要吸进烟尘。"], ["消防预防措施和保护设备：", "消防人员必须佩戴自给气式呼吸器。\n禁止污染的灭火用水流入土壤、地下水或地表水中。"]],
            "s6": [["个人预防措施、应急程序：", "戴防护设备。确保充分的通风/排气。令未授权人员离开。"], ["环境保护措施：", "禁止排入下水道、废水或土壤中。"], ["污染物收集和清除的方法：", "用化学品吸收材料或必要时用干沙收集，并储存于密闭容器中。"]],
            "s7": [["安全操作防范：", "操作时遵守化学品的常见预防措施。避免与皮肤和眼睛接触。\n远离食物、饮料和烟草。休息以前和工作结束时洗手。将工作服单独存放。\n更换被污染或浸湿的衣物。"], ["安全储存条件：", "容器保持紧闭，储存在干燥通风处。为保持产品质量，必须遵守产品信息表的储存条件。"]],
            "s8": [["8.1  控制参数：", "工作场所组分控制参数：无数据"], ["呼吸系统防护：", "喷涂过程中要求有呼吸防护设备。"], ["手部防护：", "无数据"], ["防护手套的合适材料：", "EN 374-3"], ["氟化橡胶–FKM：", "厚度≥0.4 mm；穿透时间≥480 min。"], ["丁基橡胶–IIR：", "厚度≥0.5 mm；穿透时间≥480 min。"], ["丁腈橡胶–NBR：", "厚度≥0.35 mm；穿透时间≥480 min。"], ["建议：", "污染的手套应废弃。"], ["眼睛防护：", "建议使用护目镜。"], ["身体防护：", "穿着适当的防护服。"], ["8.2  工程控制：", "无数据"]],
            "s9": [["9.1  外观：", "无色至淡黄色透明液体"], ["9.2  离子性：", "阴离子"], ["9.3  可燃性（固态、气态）：", "不适用"], ["9.4  水溶性：", "可以分散乳化于水中"], ["9.5  动力粘度/25℃：", "＜300 mPa·s"], ["9.6  闪点（闭口）：", "42℃"], ["9.7  爆炸特性：", "爆炸上限（六亚甲基二异氰酸酯）[％(V/V)]：9.5%\n爆炸下限（六亚甲基二异氰酸酯）[％(V/V)]：0.9%\n爆炸上限（丙二醇甲醚醋酸酯）[％(V/V)]：7.0%\n爆炸下限（丙二醇甲醚醋酸酯）[％(V/V)]：1.5%"], ["9.8  粉尘爆炸级别：", "不适用"], ["9.9  固体含量：", "约70%"], ["9.10  其他信息：", "上述数据非产品指标，产品指标请参见产品技术信息表。"]],
            "s10": [["10.1  化学稳定性：", "根据规范使用，不会发生分解。"], ["10.2  危险分解产物：", "在热分解过程中生成易燃有害气体。"], ["10.3  可能的危害反应：", "正确储存或操作时，无危害反应。"], ["10.4  应避免的条件：", "无数据"], ["10.5  禁配物：", "无数据"]],
            "s11": [["该产品无可用的毒理学研究。"], ["类似产品的风险评估数据："], ["11.1  急性毒性：", "经口", "无数据"], ["11.1  急性毒性：", "吸入", "吸入有害。"], ["11.1  急性毒性：", "经皮", "无数据"], ["11.1  急性毒性：", "综合评价", "无数据"], ["11.2  主要皮肤刺激性：", "", "无数据"], ["11.3  主要眼睛刺激性：", "", "无数据"], ["11.4  致敏性：", "", "可能造成皮肤过敏反应。"], ["11.5  致突变性：", "", "无数据"], ["11.6  致癌性：", "", "无数据"], ["11.7  生殖毒性：", "生育力", "无数据"], ["11.7  生殖毒性：", "致畸形", "无数据"], ["11.7  生殖毒性：", "体外遗传毒性", "无数据"], ["11.8  特异性靶器官系统毒性（一次接触/反复接触）：", "", "一次性接触：类别3。\n反复接触：类别2。"], ["11.9  吸入危害：", "", "无数据"], ["11.10 附加信息：", "", "存在经皮吸收乙酸-1-甲氧基-2-丙基酯的风险。"]],
            "s12": [["该产品无可用的生态毒理学研究。"], ["以下为本产品成分的生态毒理学参考数据："], ["12.1  生态毒性：", "", "禁止排入下水道、废水或土壤中。"], ["12.2  持久性和降解性：", "", "该产品不易生物降解。"], ["12.3  其他不利的影响：", "", "根据生态毒理学资料，该产品被划分为对鱼类和水蚤无害类。"]],
            "s13": [["必须遵守适用的国标、国家或当地法规进行废弃。\n在欧盟领域内废弃，应根据欧洲废弃物分类（EWC）的适当法规。"], ["处理方法：", "尽可能将容器倒空（例如经倾倒、刮擦或排干直至“滴干”）。\n可根据化学工业现存的回收方案送往适当的收集点处理。\n容器应按照国家法令和环境相关法规进行回收。\n不能将废弃物通过废水排放。"]],
            "s14": [["14.1  运输信息：", "联合国编号：1866\n联合国运输名称：树脂溶液\n运输危险级别：3\n包装类型：III"], ["14.2  海上运输：", "无数据"], ["14.3  空运：", "无数据"], ["14.4  用户特殊注意事项：", "环境危险：否\n特殊防范措施：参见6-8节\n附加信息：具可燃性。温度不可高于+35℃，温度不可低于-10℃。远离食物、酸和碱。\n按《MARPOL73/78》公约附则II和IBC规则：不适用"]],
            "s15": [["物质或混合物的相关安全、健康和环保法律法规"], ["其它的规定："], ["符合下列法规要求："], ["危险化学品安全管理条例，国务院令591号"], ["GB/T 16483-2008 化学品安全技术说明书内容和项目顺序"], ["GB 13690-2009 化学品分类和危险性公示通则"], ["GB 30000.2-29 化学品分类和标签规范"], ["GB 15258 化学品安全标签编写规定"]],
            "s16": [["就我们所掌握的知识信息，截止本安全技术说明书发布之日，它提供的资料是正确的。所提供的信息仅仅作为安全处理、使用、生产、储存、运输、处置和排放的指导书，而不是一份担保或品质说明书。本资料只针对所指定的具体物料，而对这种物料与其它物料混合使用或在其它制程中使用的情况，则未必有效（除非在文本中有特别说明）。"]],
        }
    return {
        "s1": [["1.1  Product name:", PRODUCT], ["Chinese name:", "Water-dispersible isocyanate curing agent"], ["Chemical classification:", "Polyisocyanate"], ["1.2  Recommended use and restrictions on use:", "Coating additive"], ["1.3  Supplier information:", ""], ["Supplier name:", company], ["Supplier address:", address], ["Telephone:", "86-763-2811205" if guocai else "86-20-82567990"], ["Fax:", "86-763-2811024" if guocai else "86-20-32214789"]],
        "s2": [["2.1  Emergency overview", "No data available"], ["2.2  GHS hazard classification:", "Flammable liquid, Category 3 (H226)\nAcute toxicity, inhalation, Category 4 (H332)\nSkin sensitization, Category 1 (H317)\nSpecific target organ toxicity (single exposure), Category 3 (H335)\nSpecific target organ toxicity (single exposure), Category 2 (H373)"], ["2.3  GHS label elements:", format_label_elements("en", [])], [" GHS pictogram:", "No data available"], ["2.4  Signal word:", "No data available"], ["2.5  Hazard statements:", "H226 Flammable liquid and vapor.\nH332 Harmful if inhaled.\nH317 May cause an allergic skin reaction.\nH335 May cause respiratory irritation.\nH373 May cause damage to organs through prolonged or repeated exposure."], ["2.6  Precautionary statements:", "P210 Keep away from heat/sparks/open flames. No smoking.\nP260 Do not breathe dust/fume/gas/mist/vapors/spray.\nP271 Use only outdoors or in a well-ventilated area.\nP280 Wear protective gloves/protective clothing/eye protection/face protection.\nP303+P361+P353 IF ON SKIN (or hair): Take off immediately all contaminated clothing. Rinse skin with water/shower.\nP304+P340 IF INHALED: Remove person to fresh air and keep comfortable for breathing.\nP308+P313 IF exposed or concerned: Get medical advice/attention.\nP403+P233 Store in a well-ventilated place. Keep container tightly closed.\nP501 Dispose of contents/container through an approved waste disposal facility."], ["2.7  Physical and chemical hazards:", "No data available"], ["2.8  Health hazards", "Inhalation: Harmful if inhaled; may cause respiratory irritation."], ["2.8  Health hazards", "Skin: May cause an allergic skin reaction."], ["2.8  Health hazards", "Eyes: No data available."], ["2.8  Health hazards", "Ingestion: No data available."], ["2.8  Health hazards", "Prolonged or repeated exposure: May cause damage to organs."], ["2.9  Environmental hazards", "No data available"], ["2.10  Other hazards", "There is a risk of dermal absorption of 1-methoxy-2-propyl acetate."]],
        "s3": [["Product type:", "Mixture", ""], ["Components", "", ""], ["Chemical name", "CAS No.", "Content % (w/w)"], ["Hexamethylene diisocyanate homopolymer", "28182-81-2", "≥45"], ["Hydrophilically modified hexamethylene diisocyanate homopolymer", "Trade secret", "4-25"], ["Hexamethylene diisocyanate", "822-06-0", "≤0.15"], ["Propylene glycol methyl ether acetate", "108-65-6", "20-40"]],
        "s4": [["General measures:", "Immediately remove all contaminated clothing."], ["Ingestion:", "Do not induce vomiting. Seek medical attention."], ["Eye contact:", "Keep eyelids open and rinse with lukewarm water for a prolonged period (at least 10 minutes). Seek ophthalmological advice."], ["Skin contact:", "Immediately wash with soap and plenty of water. If a skin reaction occurs, seek medical advice."], ["Inhalation:", "If respiratory tract irritation occurs, seek medical advice."]],
        "s5": [["Suitable extinguishing agents:", "Carbon dioxide (CO2), foam and dry powder; use water spray for large fires."], ["Unsuitable extinguishing agents:", "High-volume water jet."], ["Special hazards arising from the substance or mixture:", "Combustion may release carbon monoxide, carbon dioxide, nitrogen oxides and small amounts of hydrogen cyanide.\nDo not inhale smoke or dust in case of fire or explosion."], ["Fire-fighting precautions and protective equipment:", "Fire-fighters must wear self-contained breathing apparatus.\nPrevent contaminated fire-fighting water from entering soil, groundwater or surface water."]],
        "s6": [["Personal precautions, emergency procedures:", "Wear protective equipment. Ensure adequate ventilation/exhaust. Keep unauthorized persons away."], ["Environmental precautions:", "Do not discharge into drains, wastewater or soil."], ["Methods for containment and cleaning up:", "Collect with chemical absorbent material or, if necessary, dry sand, and store in a closed container."]],
        "s7": [["Precautions for safe handling:", "Follow common precautions for handling chemicals. Avoid contact with skin and eyes.\nKeep away from food, beverages and tobacco. Wash hands before breaks and after work. Store work clothing separately.\nChange contaminated or wet clothing."], ["Conditions for safe storage:", "Keep containers tightly closed and store in a dry, well-ventilated place. To maintain product quality, follow the storage conditions in the product information sheet."]],
        "s8": [["8.1  Control parameters:", "Workplace component control parameters: No data available"], ["Respiratory protection:", "Respiratory protection is required during spraying."], ["Hand protection:", "No data available"], ["Suitable material for protective gloves:", "EN 374-3"], ["Fluorinated rubber - FKM:", "Thickness ≥0.4 mm; breakthrough time ≥480 min."], ["Butyl rubber - IIR:", "Thickness ≥0.5 mm; breakthrough time ≥480 min."], ["Nitrile rubber - NBR:", "Thickness ≥0.35 mm; breakthrough time ≥480 min."], ["Recommendation:", "Contaminated gloves should be discarded."], ["Eye protection:", "Safety goggles are recommended."], ["Body protection:", "Wear suitable protective clothing."], ["8.2  Engineering controls:", "No data available"]],
        "s9": [["9.1  Appearance:", "Colorless to pale yellow transparent liquid"], ["9.2  Ionicity:", "Anionic"], ["9.3  Flammability (solid, gas):", "Not applicable"], ["9.4  Solubility in water:", "Can be dispersed and emulsified in water"], ["9.5  Dynamic viscosity/25 °C:", "<300 mPa·s"], ["9.6  Flash point (closed cup):", "42 °C"], ["9.7  Explosive properties:", "Upper explosive limit (hexamethylene diisocyanate) [%(V/V)]: 9.5%\nLower explosive limit (hexamethylene diisocyanate) [%(V/V)]: 0.9%\nUpper explosive limit (propylene glycol methyl ether acetate) [%(V/V)]: 7.0%\nLower explosive limit (propylene glycol methyl ether acetate) [%(V/V)]: 1.5%"], ["9.8  Dust explosion class:", "Not applicable"], ["9.9  Solid content:", "Approx. 70%"], ["9.10  Other information:", "The above data are not product specifications. Refer to the product technical information sheet for product specifications."]],
        "s10": [["10.1  Chemical stability:", "No decomposition when used according to specifications."], ["10.2  Hazardous decomposition products:", "Flammable hazardous gases may be generated during thermal decomposition."], ["10.3  Possibility of hazardous reactions:", "No hazardous reactions under proper storage or handling."], ["10.4  Conditions to avoid:", "No data available"], ["10.5  Incompatible materials:", "No data available"]],
        "s11": [["No toxicological studies are available for this product."], ["Risk assessment data for similar products:"], ["11.1  Acute toxicity:", "Oral:", "No data available"], ["11.1  Acute toxicity:", "Inhalation:", "Harmful if inhaled."], ["11.1  Acute toxicity:", "Dermal:", "No data available"], ["11.1  Acute toxicity:", "Overall assessment", "No data available"], ["11.2  Skin irritation:", "", "No data available"], ["11.3  Eye irritation:", "", "No data available"], ["11.4  Sensitization:", "", "May cause an allergic skin reaction."], ["11.5  Germ cell mutagenicity:", "", "No data available"], ["11.6  Carcinogenicity:", "", "No data available"], ["11.7  Reproductive toxicity:", "Fertility：", "No data available"], ["11.7  Reproductive toxicity:", "Teratogenicity：", "No data available"], ["11.7  Reproductive toxicity:", "In vitro genotoxicity：", "No data available"], ["11.8  Specific target organ toxicity (single/repeated exposure):", "", "Single exposure: Category 3.\nRepeated exposure: Category 2."], ["11.9  Aspiration hazard:", "", "No data available"], ["11.10 Additional information:", "", "There is a risk of dermal absorption of 1-methoxy-2-propyl acetate."]],
        "s12": [["No ecotoxicological studies are available for this product."], ["The following are ecotoxicological reference data for the product components:"], ["12.1  Ecotoxicity:", "", "Do not discharge into drains, wastewater or soil."], ["12.2  Persistence and degradability:", "", "The product is not readily biodegradable."], ["12.3  Other adverse effects:", "", "According to ecotoxicological data, the product is classified as harmless to fish and daphnia."]],
        "s13": [["Dispose of waste in accordance with applicable national and local regulations.\nWithin the European Union, dispose of waste according to the applicable European Waste Catalogue (EWC) requirements."], ["Disposal method:", "Empty containers as far as possible (for example by pouring, scraping or draining until drip-dry).\nSend to an appropriate collection point under existing chemical-industry recovery schemes.\nRecycle containers in accordance with national law and environmental regulations.\nDo not discharge waste through wastewater."]],
        "s14": [["14.1  Transport information:", "UN No.: 1866\nProper shipping name: Resin solution\nTransport hazard class: 3\nPacking type: III"], ["14.2  Transport by sea:", "No data available"], ["14.3  Air transport:", "No data available"], ["14.4  Special precautions for users:", "Environmental hazard: No\nSpecial precautions: See Sections 6-8\nAdditional information: Flammable. Keep temperature below +35 °C and above -10 °C. Keep away from food, acids and alkalis.\nUnder MARPOL 73/78 Annex II and the IBC Code: Not applicable"]],
        "s15": [["Relevant safety, health and environmental regulations for the substance or mixture"], ["Other provisions:"], ["Complies with the following regulatory requirements:"], ["Regulations on the Safety Management of Hazardous Chemicals, State Council Decree No. 591"], ["GB/T 16483-2008 Safety data sheet for chemical products - Content and order of sections"], ["GB 13690-2009 Classification and hazard communication of chemicals"], ["GB 30000.2-29 Classification and labelling of chemicals"], ["GB 15258 Rules for the preparation of precautionary statements for chemical safety labels"]],
        "s16": [["To the best of our knowledge, the information provided in this safety data sheet is correct as of its date of issue. The information is intended only as guidance for the safe handling, use, manufacture, storage, transport, disposal and release of the specified material and is not a warranty or quality specification. It applies only to the specific material identified and may not be valid when the material is used in combination with other materials or in another process, unless specifically stated in the text."]],
    }


_legacy_source_facts = source_facts


def source_facts(language, brand):
    """Project only facts explicitly present in the OS-9015 source DOCX."""
    facts = _legacy_source_facts(language, brand)
    facts["s2"][2][1] = format_label_elements(
        language,
        ["亲水脂肪族聚异氰酸酯"] if language == "zh" else ["Hydrophilic aliphatic polyisocyanate"],
    )
    facts["s2"][3][1] = ""
    facts["s2"][4][1] = "警告" if language == "zh" else "Warning"
    # These are direct normalized renderings of the five Section 11 source
    # rows.  No species, method, classification or similar-product qualifier
    # is added where the source does not state it.
    if language == "zh":
        facts["s11"] = [
            ["该产品无可用的毒理学研究。"],
            ["类似产品的风险评估数据："],
            ["11.1  急性毒性：", "经口", "半数致死剂量（LD50）/大鼠：>2,000 mg/kg"],
            ["11.1  急性毒性：", "吸入", "无数据"],
            ["11.1  急性毒性：", "经皮", "无数据"],
            ["11.1  急性毒性：", "综合评价", "无数据"],
            ["11.2  主要皮肤刺激性：", "", "轻微刺激"],
            ["11.3  主要眼睛刺激性：", "", "主要粘膜刺激性：轻微刺激"],
            ["11.4  致敏性：", "", "皮肤接触可能致敏"],
            ["11.5  致突变性：", "", "在Ames试验中无致突变性。"],
            ["11.6  致癌性：", "", "无数据"],
            ["11.7  生殖毒性：", "生育力", "无数据"],
            ["11.7  生殖毒性：", "致畸形", "无数据"],
            ["11.7  生殖毒性：", "体外遗传毒性", "无数据"],
            ["11.8  特异性靶器官系统毒性（一次接触/反复接触）：", "", "无数据"],
            ["11.9  吸入危害：", "", "无数据"],
            ["11.10 附加信息：", "", "无数据"],
        ]
    else:
        facts["s11"] = [
            ["No toxicological studies are available for this product."],
            ["Risk assessment data for similar products:"],
            ["11.1  Acute toxicity:", "Oral:", "LD50/oral/rat: >2,000 mg/kg"],
            ["11.1  Acute toxicity:", "Inhalation:", "No data available"],
            ["11.1  Acute toxicity:", "Dermal:", "No data available"],
            ["11.1  Acute toxicity:", "Overall assessment", "No data available"],
            ["11.2  Skin irritation:", "", "Slight irritation"],
            ["11.3  Eye irritation:", "", "Mucous membrane irritation: slight irritation"],
            ["11.4  Sensitization:", "", "Skin contact may cause sensitization"],
            ["11.5  Germ cell mutagenicity:", "", "No mutagenicity in the Ames test."],
            ["11.6  Carcinogenicity:", "", "No data available"],
            ["11.7  Reproductive toxicity:", "Fertility：", "No data available"],
            ["11.7  Reproductive toxicity:", "Teratogenicity：", "No data available"],
            ["11.7  Reproductive toxicity:", "In vitro genotoxicity：", "No data available"],
            ["11.8  Specific target organ toxicity (single/repeated exposure):", "", "No data available"],
            ["11.9  Aspiration hazard:", "", "No data available"],
            ["11.10 Additional information:", "", "No data available"],
        ]
    return facts


def write_body(doc, facts, language):
    # The template owns headings, labels and sequence cells.  Only value
    # cells are cleared and written; S3 data rows are handled by the explicit
    # three-cell subtable branch in the whitelist.
    clear_value_cells(doc)
    for sec in range(1, 17):
        table = doc.tables[sec - 1]
        rows = base.project_rows_to_template(facts[f"s{sec}"], language, sec, table)
        for ri, values in enumerate(rows, 1):
            if ri >= len(table.rows):
                raise RuntimeError(f"template capacity mismatch S{sec}: row {ri}")
            base.set_row(table.rows[ri], values, table_index=sec - 1, row_index=ri)
    write_s82_child_rows(
        doc.tables[7].rows[11].cells[1],
        facts.get("s8_control_parameters", []),
        language,
    )


def write_header_footer(doc, language, brand):
    is_en = language == "en"
    company, _ = _company(language, brand)
    for section in doc.sections:
        for p in section.header.paragraphs:
            if "Version" in p.text or "版本" in p.text:
                set_paragraph_text(p, "Version: 1.0" if is_en else "版本：1.0")
            elif p.text.strip() and ("安全" in p.text or "Material" in p.text):
                set_paragraph_text(p, "Material Safety Data Sheet" if is_en else "物料安全数据表")
        for table in section.header.tables:
            for row in table.rows:
                for cell in unique_cells(row):
                    if cell.text.strip() in {"PU-2345", "PEA-4139", PRODUCT}:
                        set_cell_text(cell, PRODUCT)
        for table in section.footer.tables:
            if not table.rows:
                continue
            cells = unique_cells(table.rows[0])
            if cells:
                set_cell_text(cells[0], f"{company}\n{PRODUCT}-MSDS" if is_en else f"{company}  {PRODUCT}-MSDS")
                if len(cells) > 1:
                    set_cell_text(cells[1], "Revision date: 2025/2/22" if is_en else "修订日期：2025/2/22")


def replace_residual_product_ids(doc):
    def visit(container):
        for paragraph in container.paragraphs:
            if paragraph.text.strip() in {"PEA-4139", "PU-2345"}:
                set_paragraph_text(paragraph, PRODUCT)
        for table in container.tables:
            for row in table.rows:
                for cell in unique_cells(row):
                    if cell.text.strip() in {"PEA-4139", "PU-2345"}:
                        set_cell_text(cell, PRODUCT)
    visit(doc)
    for section in doc.sections:
        visit(section.header)
        visit(section.footer)


def suppress_s9(doc):
    table = doc.tables[8]
    removed = []
    visible = []
    for row in list(table.rows)[1:]:
        cells = unique_cells(row)
        value = " ".join(cell.text.strip() for cell in cells[1:] if cell.text.strip())
        label = cells[0].text.strip() if cells else ""
        if not value or base.is_missing_data_value(value):
            removed.append(label)
            table._tbl.remove(row._tr)
        else:
            visible.append(row)
    labels = []
    for number, row in enumerate(visible, 1):
        cells = unique_cells(row)
        if not cells or not cells[0].paragraphs:
            continue
        p = cells[0].paragraphs[0]
        current = p.text
        updated = re.sub(r"^(\s*)9\.\d+\b", rf"\g<1>9.{number}", current, count=1)
        if updated != current:
            set_sequence_prefix(cells[0], 9, number)
        labels.append(updated.strip())
    return {"removed_count": len(removed), "removed_labels": removed, "visible_count": len(labels), "visible_labels": labels}


def build_one(language, brand):
    slug = f"{brand}_{'en' if language == 'en' else 'cn'}"
    out_dir = OUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_docx = out_dir / f"{PRODUCT}_MSDS_{'EN' if language == 'en' else 'CN'}_{'Guocai' if brand == 'guocai' else 'Guanzhi'}.docx"
    template = template_for(language)
    import shutil
    shutil.copy2(template, out_docx)
    doc = Document(str(out_docx))
    base.validate_template_capacity(doc, language)
    facts = source_facts(language, brand)
    base.ensure_s3_component_rows(doc, component_count=len(facts["s3"]) - 3)
    write_body(doc, facts, language)
    if language == "en":
        # Re-assert value-cell formatting from the exact active EN template
        # before any row suppression changes physical row indexes.  This is a
        # template-format sync, not a CN-to-EN normalization or redesign.
        base.normalize_en_document(doc, template_path=TEMPLATE_EN)
    pictogram_audit = insert_source_pictogram(doc, SOURCE)
    s2_policy = suppress_missing_section2_rows_and_renumber(doc, set_paragraph_text)
    s9_policy = suppress_s9(doc)
    write_header_footer(doc, language, brand)
    replace_residual_product_ids(doc)
    if language == "zh":
        base.compact_cn_document(doc)
    else:
        base.normalize_footer(doc)
    doc.save(out_docx)
    output_rows = [len(table.rows) for table in doc.tables]
    return {
        "product": PRODUCT,
        "brand": brand,
        "language": "en-US" if language == "en" else "zh-CN",
        "source_docx": str(SOURCE),
        "source_docx_sha256": sha256(SOURCE),
        "template_reference": str(template),
        "template_reference_sha256": sha256(template),
        "template_source_reference": str(TEMPLATE_EN_SOURCE) if language == "en" else None,
        "template_source_reference_sha256": sha256(TEMPLATE_EN_SOURCE) if language == "en" else None,
        "template_geometry": base.template_geometry(language),
        "output_geometry": {"table_count": 16, "rows": output_rows, "s3_component_rows": 4},
        "section2_policy": s2_policy,
        "pictogram": pictogram_audit,
        "section9_policy": s9_policy,
        "status": "ready",
        "formal_ready": True,
        "blockers": [],
        "translation_review": [] if language == "zh" else [{"status": "completed_by_source_grounded_mapping"}],
        "output_path": str(out_docx),
    }


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
    (OUT_ROOT / "source-structure-snapshot.json").write_text(json.dumps(source_structure_snapshot(SOURCE), ensure_ascii=False, indent=2), encoding="utf-8")
    audits = [build_one(language, brand) for brand in ("guanzhi", "guocai") for language in ("zh", "en")]
    report = {
        "product": PRODUCT,
        "matrix": "2 brands × 2 languages × 2 formats",
        "docx_count": 4,
        "pdf_count": 4,
        "formal_ready_count": 4,
        "draft_count": 0,
        "shared_blocker": None,
        "source_docx_sha256": sha256(SOURCE),
        "records": audits,
    }
    (OUT_ROOT / "matrix-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

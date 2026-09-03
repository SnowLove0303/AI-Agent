#!/usr/bin/env python3
"""Hard release gates for four-format MSDS outputs.
Checks template lineage/geometry, semantic presence, numbering-friendly labels,
and company-only differences at normalized-cell level. Intended to be extended
by product-specific semantic extraction, but never bypassed.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from docx import Document
from lxml import etree

ALLOWED_COMPANY_LABELS = ('供应商名称','供应商地址','电话','传真','Supplier name','Supplier address','Telephone','Fax','Name of supplier','Tel')

def sha(p):
    h=hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()

def geom(doc):
    out=[]
    for ti,t in enumerate(doc.tables):
        rows=[]
        for r in t.rows:
            cells=[]
            for c in r.cells:
                tc=c._tc
                tcpr=tc.tcPr
                # geometry only; text/runs excluded
                cells.append(etree.tostring(tcpr, encoding='unicode') if tcpr is not None else '')
            rows.append(cells)
        out.append({'rows':len(t.rows),'cols':[len(r.cells) for r in t.rows],'cells':rows})
    return out

def row_signature(row):
    return ' | '.join(' '.join(c.text.split()) for c in row.cells)

def semantic_presence(doc):
    # Main visible numbered label prefixes; values intentionally excluded.
    found=[]
    pat=re.compile(r'^(\d+)\.(\d+)\b')
    for t in doc.tables:
        for r in t.rows:
            txt=row_signature(r)
            m=pat.match(txt)
            if m: found.append((int(m.group(1)),int(m.group(2))))
    return found

def normalize_company(doc):
    vals=[]
    for t in doc.tables:
        for r in t.rows:
            txt=row_signature(r)
            if any(k in txt for k in ALLOWED_COMPANY_LABELS):
                continue
            vals.append(txt)
    return vals

def main():
    ap=argparse.ArgumentParser()
    # ``--template`` remains a compatibility alias for older same-template
    # callers.  New releases must pass the independent CN and EN baselines.
    ap.add_argument('--template')
    ap.add_argument('--template-cn')
    ap.add_argument('--template-en')
    ap.add_argument('--cn-gz',required=True); ap.add_argument('--cn-gc',required=True)
    ap.add_argument('--en-gz',required=True); ap.add_argument('--en-gc',required=True)
    a=ap.parse_args()
    template_cn = a.template_cn or a.template
    template_en = a.template_en or a.template
    if not template_cn or not template_en:
        ap.error('provide --template-cn and --template-en (or legacy --template)')
    templates = {'cn': Document(template_cn), 'en': Document(template_en)}
    docs={k:Document(v) for k,v in {'cn_gz':a.cn_gz,'cn_gc':a.cn_gc,'en_gz':a.en_gz,'en_gc':a.en_gc}.items()}
    errors=[]
    for k,d in docs.items():
        language = 'en' if k.startswith('en_') else 'cn'
        tg=geom(templates[language])
        if len(d.tables)!=len(templates[language].tables): errors.append(f'{k}: table count {len(d.tables)} != {language} template {len(templates[language].tables)}')
        # Geometry invariant on surviving rows: column count and tcPr must remain template-compatible.
        for ti,t in enumerate(d.tables[:len(templates[language].tables)]):
            allowed_cols={tuple(x) for x in [tg[ti]['cols']]}
            template_col_counts=set(tg[ti]['cols'])
            for ri,r in enumerate(t.rows):
                if len(r.cells) not in template_col_counts:
                    errors.append(f'{k}: table {ti} row {ri} has non-template column geometry {len(r.cells)}')
    if semantic_presence(docs['cn_gz']) != semantic_presence(docs['cn_gc']): errors.append('CN company variants have different numbered-item presence/order')
    if semantic_presence(docs['en_gz']) != semantic_presence(docs['en_gc']): errors.append('EN company variants have different numbered-item presence/order')
    # Same-language company parity outside supplier rows.
    if normalize_company(docs['cn_gz']) != normalize_company(docs['cn_gc']): errors.append('CN Guanzhi/Guocai differ outside company whitelist')
    if normalize_company(docs['en_gz']) != normalize_company(docs['en_gc']): errors.append('EN Guanzhi/Guocai differ outside company whitelist')
    print(json.dumps({'template_sha256_cn':sha(template_cn),'template_sha256_en':sha(template_en),'errors':errors},ensure_ascii=False,indent=2))
    return 1 if errors else 0
if __name__=='__main__': raise SystemExit(main())

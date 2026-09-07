from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
from tds_common import ROOT, convert_legacy
SCRIPTS=Path(__file__).parent
def run(name,*args):
    r=subprocess.run([sys.executable,str(SCRIPTS/name),*map(str,args)],text=True,encoding='utf-8',errors='replace');
    if r.returncode: raise SystemExit(r.returncode)
def main():
    ap=argparse.ArgumentParser(description='Independent TDS CN/EN x Guanzhi/Guocai eight-format builder'); sub=ap.add_subparsers(dest='cmd',required=True)
    b=sub.add_parser('baseline'); b.add_argument('--output',type=Path,default=ROOT/'snapshots'/'template_baselines.json')
    build=sub.add_parser('build'); build.add_argument('--source-cn',type=Path); build.add_argument('--source-en',type=Path); build.add_argument('--normalized-mapping',type=Path,help='approved 1.3.0 mapping produced after Agent normalization and translation judgment'); build.add_argument('--model',required=True); build.add_argument('--output-dir',type=Path,required=True)
    a=sub.add_parser('audit'); a.add_argument('--output-dir',type=Path,required=True); a.add_argument('--mapping',type=Path,required=True); a.add_argument('--report',type=Path,required=True)
    x=ap.parse_args()
    if x.cmd=='baseline': run('snapshot_tds_templates.py','--output',x.output); return
    if x.cmd=='build':
        if not x.source_cn and not x.source_en and not x.normalized_mapping: raise SystemExit('source-cn, source-en, or normalized-mapping required')
        audit=x.output_dir/'audit'; word_dir=x.output_dir/'WORD'; pdf_dir=x.output_dir/'PDF'; generation_dir=audit/'generation'; log_dir=audit/'execution_logs'
        audit.mkdir(parents=True,exist_ok=True); word_dir.mkdir(parents=True,exist_ok=True); pdf_dir.mkdir(parents=True,exist_ok=True); generation_dir.mkdir(parents=True,exist_ok=True); log_dir.mkdir(parents=True,exist_ok=True)
        if x.normalized_mapping:
            mapping=x.normalized_mapping
        else:
            work=ROOT/'_work'/'source-convert'; work.mkdir(parents=True,exist_ok=True); cn=convert_legacy(x.source_cn,work) if x.source_cn else None; en=convert_legacy(x.source_en,work) if x.source_en else None; facts=[]
            for p,lang in ((cn,'zh-CN'),(en,'en-US')):
                if p: f=audit/(p.stem+'_'+lang+'.json'); run('extract_tds_source.py',p,'--language',lang,'--output',f); facts.append((lang,f))
            cnf=next((p for l,p in facts if l=='zh-CN'),None); enf=next((p for l,p in facts if l=='en-US'),None); mapping=audit/'mapping.json'; map_args=[]; map_args += ['--cn',cnf] if cnf else []; map_args += ['--en',enf] if enf else []; map_args += ['--registry',ROOT/'mapping'/'template_field_registry.json','--output',mapping]; run('map_tds_fields.py',*map_args)
        run('overwrite_tds.py','--mapping',mapping,'--registry',ROOT/'mapping'/'template_field_registry.json','--output-dir',word_dir,'--log-dir',log_dir,'--generation-dir',generation_dir,'--artifact-root',x.output_dir,'--model',x.model); run('convert_docx_to_pdf.py','--input-dir',word_dir,'--output-dir',pdf_dir); run('audit_tds_eight.py','--output-dir',x.output_dir,'--registry',ROOT/'mapping'/'template_field_registry.json','--mapping',mapping,'--model',x.model,'--report',x.output_dir/'audit'/'release_report.json'); return
    run('audit_tds_eight.py','--output-dir',x.output_dir,'--registry',ROOT/'mapping'/'template_field_registry.json','--mapping',x.mapping,'--model',x.output_dir.name,'--report',x.report)
if __name__=='__main__': main()

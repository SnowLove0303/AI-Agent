#!/usr/bin/env python3
import re, sys, zipfile
from pathlib import Path

BANNED = [
    r'\bdanger chemicals?\b', r'\bpoison information\b', r'\becology toxicity\b',
    r'\bhand protect\b', r'\beye protect\b', r'\bno danger reaction\b',
    r'not satisfy classification standard', r'no data materials?'
]
MISSING = ['无数据','无数据资料','暂无数据','无可用数据','无适用资料']

def text_from_docx(p):
    with zipfile.ZipFile(p) as z:
        parts=[]
        for n in z.namelist():
            if n.startswith('word/') and n.endswith('.xml'):
                parts.append(z.read(n).decode('utf-8','ignore'))
        s=' '.join(parts)
        s=re.sub(r'<[^>]+>',' ',s)
        return re.sub(r'\s+',' ',s)

def run(p):
    """Audit one built file; return issue list. Import-safe core of main()."""
    p = Path(p)
    text=text_from_docx(p) if p.suffix.lower()=='.docx' else p.read_text(encoding='utf-8')
    issues=[]
    low=text.lower()
    for pat in BANNED:
        if re.search(pat, low): issues.append('BANNED_TRANSLATION: '+pat)
    for m in MISSING:
        if m in text: issues.append('VISIBLE_MISSING_MARKER: '+m)
    return issues


def main():
    p=Path(sys.argv[1])
    issues = run(p)
    if issues:
        print('\n'.join(issues)); return 2
    print('PASS: English terminology audit')
    return 0
if __name__=='__main__': raise SystemExit(main())

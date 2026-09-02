#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, zipfile, tempfile, sys
EXCLUDE=('__pycache__','.pytest_cache')
ALLOW_CHANGED={
    'SKILL.md', 'CHANGELOG.md', 'manifest.txt', 'scripts/sentence_boundary_policy.py',
    # v3.4 approved template-baseline replacement; v2.9 core remains hash-checked.
    'docs/template_baseline.md', 'examples/template_reference.docx',
    # v3.6.2 retains the approved Section 9 whole-row omission/renumbering clarification.
    'docs/section_mapping_rules.md',
    'tests/template_snapshot.json',
    # v3.4 release gates: controlled locked-label and whitespace audits.
    'scripts/audit_locked_labels.py', 'scripts/audit_whitespace.py',
}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root):
    return {str(p.relative_to(root)).replace('\\','/'):p for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in EXCLUDE)}

def zip_name(info):
    """Return a usable ZIP member name without corrupting UTF-8 names."""
    name = info.filename
    # Some legacy archives stored UTF-8 bytes while clearing the UTF-8 flag.
    if not (info.flag_bits & 0x800):
        raw = name.encode('cp437', errors='replace')
        for encoding in ('utf-8', 'gb18030'):
            try:
                candidate = raw.decode(encoding)
            except UnicodeDecodeError:
                continue
            if '\ufffd' not in candidate:
                return candidate
    return name

def unpack_zip(path, target):
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            name = zip_name(info)
            out = target / name
            if info.is_dir():
                out.mkdir(parents=True, exist_ok=True)
            else:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(z.read(info))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--v29-zip',required=True); ap.add_argument('--skill-root',required=True); a=ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        unpack_root = Path(td)
        unpack_zip(a.v29_zip, unpack_root)
        roots=[p for p in unpack_root.iterdir() if p.is_dir()]; base=roots[0]
        old,new=files(base),files(Path(a.skill_root)); errors=[]
        new_by_digest={}
        for rel,p in new.items(): new_by_digest.setdefault(digest(p), []).append((rel,p))
        for rel,p in old.items():
            if rel not in new:
                matches=new_by_digest.get(digest(p), [])
                if matches:
                    # Multiple paths are acceptable only when every candidate has
                    # the same exact digest (for preserved legacy filename aliases).
                    continue
                errors.append(f'MISSING {rel}'); continue
            if rel not in ALLOW_CHANGED and digest(p)!=digest(new[rel]): errors.append(f'CHANGED {rel}')
        # preservation copies for intentionally changed legacy core files
        required=['legacy_v2_9/SKILL_v2.9.md','legacy_v2_9/CHANGELOG_v2.9.md','legacy_v2_9/sentence_boundary_policy_v2.9.py','docs/v2_9_inheritance_contract.md']
        for rel in required:
            if not (Path(a.skill_root)/rel).exists(): errors.append(f'MISSING_COMPAT {rel}')
        if errors:
            print('\n'.join(errors)); return 1
        print(f'PASS v2.9 inheritance: {len(old)} legacy files checked; only approved wrapper/enhancement files differ.')
        return 0
if __name__=='__main__': sys.exit(main())

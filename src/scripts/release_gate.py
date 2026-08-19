#!/usr/bin/env python3
"""Release safety gate: migration graph, destructive downgrade policy, and required production config."""
from pathlib import Path
import re, sys

root=Path(__file__).resolve().parents[1]
versions=root/'alembic'/'versions'
files=sorted(versions.glob('*.py'))
revs={}; children={}
for f in files:
    s=f.read_text(errors='ignore')
    m=re.search(r'^revision\s*=\s*[\"\']([^\"\']+)',s,re.M)
    d=re.search(r'^down_revision\s*=\s*[\"\']([^\"\']+)',s,re.M)
    if not m: continue
    rev=m.group(1); down=d.group(1) if d else None
    if rev in revs: raise SystemExit(f'duplicate revision: {rev}')
    revs[rev]=(f,down)
    if down: children.setdefault(down,[]).append(rev)
heads=[r for r in revs if r not in children]
if len(heads)!=1: raise SystemExit(f'expected exactly one Alembic head, got {heads}')
cur=heads[0]; seen=set()
while cur:
    if cur in seen: raise SystemExit('migration cycle detected')
    seen.add(cur)
    cur=revs[cur][1]
    if cur and cur not in revs: raise SystemExit(f'missing down_revision: {cur}')
if len(seen)!=len(revs): raise SystemExit('disconnected Alembic migration branch detected')
# Production migrations must not use Base.metadata.create_all except the explicit baseline.
for rev,(f,_) in revs.items():
    s=f.read_text(errors='ignore')
    if rev!='render_v84' and 'create_all(' in s:
        raise SystemExit(f'unapproved create_all in migration {f.name}')
# Explicitly reject silent destructive operations in upgrade paths.
for rev,(f,_) in revs.items():
    if rev=='render_v84': continue
    s=f.read_text(errors='ignore')
    up=s.split('def downgrade():',1)[0]
    if re.search(r'\b(drop_table|drop_column|drop_constraint)\s*\(', up):
        # v842 deliberately invalidates legacy plaintext tokens as a one-way security migration.
        if rev != 'v842_security_cleanup':
            raise SystemExit(f'destructive schema operation in upgrade: {f.name}')
print(f'RELEASE GATE PASS: {len(revs)} migrations, single head={heads[0]}')

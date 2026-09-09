# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,json,re,collections,datetime
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
recs=[]
with open(os.path.join(R,'_logs','failures.jsonl'),encoding='utf-8') as fh:
    for l in fh:
        l=l.strip()
        if l:
            try:
                r=json.loads(l); r['_h']=re.sub(r'^https?://','',(r.get('url') or '')).split('/')[0].lower(); recs.append(r)
            except Exception: pass

print('=== v.redd.it 403 vs 200: is it the host or the asset?')
v=[r for r in recs if r['_h']=='v.redd.it']
for ph in sorted({r.get('phase') for r in v}):
    s=[r for r in v if r.get('phase')==ph]
    print('  phase %-10s n=%3d  %s'%(ph,len(s),dict(collections.Counter(r.get('status') for r in s).most_common())))
print()
print('  by url shape:')
def shape(u):
    if 'DASH' in u: return re.sub(r'DASH_\d+','DASH_N',u.split('/')[-1].split('?')[0])+('?fallback' if 'fallback' in u else '')
    return u.split('/')[-1][:20] or 'bare'
sh=collections.defaultdict(collections.Counter)
for r in v: sh[shape(r.get('url',''))][r.get('status')]+=1
for k,c in sorted(sh.items(),key=lambda kv:-sum(kv[1].values()))[:10]:
    print('    %-34s %s'%(k,dict(c.most_common())))
print()
print('  temporal clustering of 403 (per phase, ordered by ts):')
for ph in sorted({r.get('phase') for r in v}):
    s=sorted([r for r in v if r.get('phase')==ph],key=lambda r:r.get('ts') or '')
    seq=''.join('X' if r.get('status')==403 else ('o' if r.get('status') in (200,206) else '.') for r in s)
    print('    %-10s %s'%(ph,seq))
    # runs test: count runs of X
    runs=len([1 for i,ch in enumerate(seq) if ch=='X' and (i==0 or seq[i-1]!='X')])
    nx=seq.count('X')
    print('      403s=%d  runs_of_403=%d  (isolated 403s => asset-specific; long runs => throttling)'%(nx,runs))
print()
print('  same post_id probed in both phases? agreement:')
byid=collections.defaultdict(dict)
for r in v:
    byid[r.get('post_id')][r.get('phase')]=r.get('status')
both=[(k,d) for k,d in byid.items() if len(d)>1]
agree=sum(1 for k,d in both if len(set(1 if s==403 else 0 for s in d.values()))==1)
print('    ids probed in >1 phase: %d ; same 403-ness both times: %d ; flipped: %d'%(len(both),agree,len(both)-agree))
for k,d in both[:12]: print('      ',k,d)

print()
print('=== redgifs auth blindness')
g=[r for r in recs if r['_h']=='api.redgifs.com']
for ph in sorted({r.get('phase') for r in g}):
    s=[r for r in g if r.get('phase')==ph]
    print('  phase %-10s n=%3d  %s'%(ph,len(s),dict(collections.Counter(r.get('status') for r in s).most_common())))
print()
print('=== gfycat.com direct (status None = connection error)')
gc=[r for r in recs if r['_h']=='gfycat.com']
print(collections.Counter((r.get('error') or '')[:80] for r in gc).most_common(5))

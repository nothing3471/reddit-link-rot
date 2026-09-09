# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,json,csv,re,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
recs=[]
with open(os.path.join(R,'_logs','failures.jsonl'),encoding='utf-8') as fh:
    for l in fh:
        l=l.strip()
        if l:
            try: recs.append(json.loads(l))
            except Exception: pass
print('failures.jsonl records:',len(recs))
print('keys:',sorted({k for r in recs for k in r}))
print('phases:',collections.Counter(r.get('phase') for r in recs).most_common())
host=lambda u:(re.match(r'^https?://([^/]+)',u or '') or [None,'?'])[1] if re.match(r'^https?://([^/]+)',u or '') else '?'
for r in recs: r['_h']=re.sub(r'^https?://','',(r.get('url') or '')).split('/')[0].lower()
print()
print('=== status by host (all phases)')
tab=collections.defaultdict(collections.Counter)
for r in recs: tab[r['_h']][r.get('status')]+=1
for h,c in sorted(tab.items(),key=lambda kv:-sum(kv[1].values()))[:18]:
    print('%-34s n=%5d  %s'%(h,sum(c.values()),dict(c.most_common(8))))
print()
print('=== v.redd.it detail')
v=[r for r in recs if 'v.redd.it' in r['_h']]
print('n=',len(v),'status:',collections.Counter(r.get('status') for r in v).most_common())
print('verdicts:',collections.Counter(r.get('verdict') for r in v).most_common())
print('sample errors:',collections.Counter((r.get('error') or '')[:90] for r in v).most_common(6))
print()
print('=== i.redd.it detail')
i=[r for r in recs if r['_h']=='i.redd.it']
print('n=',len(i),'status:',collections.Counter(r.get('status') for r in i).most_common())
print()
print('=== preview/thumb hosts')
for hh in ('preview.redd.it','external-preview.redd.it','b.thumbs.redditmedia.com','a.thumbs.redditmedia.com'):
    s=[r for r in recs if r['_h']==hh]
    if s: print('%-30s n=%5d %s'%(hh,len(s),collections.Counter(r.get('status') for r in s).most_common(5)))
print()
print('=== last-record phase breakdown per stratum (latest run only)')
ph=collections.Counter(r.get('phase') for r in recs).most_common()
print(ph)

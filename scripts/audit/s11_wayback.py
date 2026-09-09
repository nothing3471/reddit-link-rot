# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
# -*- coding: utf-8 -*-
"""Wayback availability probe. Touches ONLY archive.org. Never imgur/redgifs/reddit."""
import os,sys,json,csv,re,time,random,urllib.request,urllib.error,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) reddit-archive-audit/1.0'
FORBIDDEN=re.compile(r'(imgur\.com|redgifs\.com|gfycat\.com|redd\.it|redditmedia\.com|reddit\.com)',re.I)

dead=list(csv.DictReader(open(os.path.join(R,'_logs','dead_list_candidates.csv'),encoding='utf-8',newline='')))
by=collections.defaultdict(list)
for x in dead: by[x['stratum']].append(x)
random.seed(41)
N=int(sys.argv[1]) if len(sys.argv)>1 else 60
rows=[r for s,v in by.items() for r in random.sample(v,min(N,len(v)))]
random.shuffle(rows)
print('probing %d urls across %d strata'%(len(rows),len(by)),flush=True)

def avail(u):
    q='https://archive.org/wayback/available?url='+urllib.parse.quote(u,safe='')
    assert not FORBIDDEN.search(q.split('?')[0]), 'refuse: forbidden host in request target'
    req=urllib.request.Request(q); req.add_header('User-Agent',UA)
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            j=json.loads(r.read(20000).decode('utf-8','replace'))
            s=(j.get('archived_snapshots') or {}).get('closest') or {}
            return ('HIT' if s.get('available') else 'MISS'), s.get('timestamp'), s.get('status'), s.get('url')
    except urllib.error.HTTPError as e: return 'HTTP%s'%e.code,None,None,None
    except Exception as e: return 'ERR:'+type(e).__name__,None,None,None

import urllib.parse
out=[];res=collections.Counter();t0=time.time()
fh=open(os.path.join(A,'wayback_results.jsonl'),'w',encoding='utf-8')
for i,r in enumerate(rows):
    v,ts,st,su=avail(r['url'])
    res[r['stratum']+'|'+v]+=1
    rec={'id':r['id'],'stratum':r['stratum'],'url':r['url'],'verdict':v,'ts':ts,'snap_status':st,'snap_url':su}
    fh.write(json.dumps(rec)+'\n'); fh.flush()
    if (i+1)%25==0: print('  %d/%d %.0fs'%(i+1,len(rows),time.time()-t0),flush=True)
    time.sleep(1.1)
fh.close()
print()
print('%-20s %6s %6s %6s %8s'%('stratum','HIT','MISS','other','hit%'))
for s in sorted(by):
    h=res[s+'|HIT']; m=res[s+'|MISS']; o=sum(v for k,v in res.items() if k.startswith(s+'|') and not k.endswith('|HIT') and not k.endswith('|MISS'))
    t=h+m+o
    print('%-20s %6d %6d %6d %7.0f%%'%(s,h,m,o,100.0*h/t if t else 0))
th=sum(v for k,v in res.items() if k.endswith('|HIT'))
print('%-20s %6d %6d %6d %7.0f%%'%('TOTAL',th,sum(v for k,v in res.items() if k.endswith('|MISS')),
      sum(res.values())-th-sum(v for k,v in res.items() if k.endswith('|MISS')),100.0*th/sum(res.values())))
print('other verdicts:',collections.Counter(k.split('|')[1] for k in res.elements()).most_common())

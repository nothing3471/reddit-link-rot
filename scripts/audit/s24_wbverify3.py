# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
# Third attempt at byte-verifying Wayback snapshots. Contacts ONLY web.archive.org.
# Uses https + normal replay (no id_), which is what a browser would request.
import os,sys,json,re,time,random,collections,urllib.request,urllib.error,ssl
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
recs=[json.loads(l) for l in open(os.path.join(A,'wayback_results.jsonl'),encoding='utf-8') if l.strip()]
hits=[r for r in recs if r['verdict']=='HIT' and r.get('snap_url')]
by=collections.defaultdict(list)
for r in hits: by[r['stratum']].append(r)
random.seed(9)
pick=[r for s,v in sorted(by.items()) for r in random.sample(v,min(4,len(v)))]
print('byte-verifying %d of %d hits (https, normal replay)'%(len(pick),len(hits)),flush=True)
MAGIC=[(b'\xff\xd8\xff','jpg'),(b'\x89PNG','png'),(b'GIF8','gif'),(b'RIFF','webp'),(b'\x1aE\xdf\xa3','webm')]
def sniff(b):
    for m,n in MAGIC:
        if b.startswith(m): return n
    if len(b)>=12 and b[4:8]==b'ftyp': return 'mp4'
    low=b[:800].lower()
    if b'<html' in low or b'<!doctype' in low: return 'html'
    return 'other:'+repr(b[:8])
ctx=ssl.create_default_context(); res=collections.Counter()
for r in pick:
    u=r['snap_url'].replace('http://web.archive.org','https://web.archive.org')
    if 'web.archive.org' not in u.split('/')[2]: continue
    k='?';n=None;ct=''
    try:
        req=urllib.request.Request(u)
        req.add_header('User-Agent',UA)
        req.add_header('Accept','text/html,image/*,*/*;q=0.8')
        with urllib.request.urlopen(req,timeout=60,context=ctx) as rr:
            b=rr.read(8192); ct=(rr.headers.get('Content-Type') or '')[:28]; n=rr.headers.get('Content-Length'); k=sniff(b)
    except urllib.error.HTTPError as e: k='HTTP%s'%e.code
    except Exception as e: k='ERR:'+type(e).__name__
    res[r['stratum']+'|'+('media' if k in ('jpg','png','gif','webp','mp4','webm') else k)]+=1
    print('  %-20s %-14s %-26s %9s  %s'%(r['stratum'],k[:14],ct,n,r['url'][:50]),flush=True)
    time.sleep(3.0)
print()
for s in sorted({k.split('|')[0] for k in res}):
    d={k.split('|')[1]:v for k,v in res.items() if k.startswith(s+'|')}
    print('  %-20s %s'%(s,d))
tot=sum(res.values()); m=sum(v for k,v in res.items() if k.split('|')[1]=='media')
print('  real media bytes returned: %d/%d'%(m,tot))

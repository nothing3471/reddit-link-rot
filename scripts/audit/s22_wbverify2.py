# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
# Byte-verify Wayback snapshots. Contacts ONLY web.archive.org. No Range header (WBM rejects it).
import os,sys,json,re,time,random,collections,urllib.request,urllib.error
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
os.makedirs(A, exist_ok=True)
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
recs=[json.loads(l) for l in open(os.path.join(A,'wayback_results.jsonl'),encoding='utf-8') if l.strip()]
hits=[r for r in recs if r['verdict']=='HIT' and r.get('snap_url')]
by=collections.defaultdict(list)
for r in hits: by[r['stratum']].append(r)
random.seed(5)
pick=[r for s,v in sorted(by.items()) for r in random.sample(v,min(8,len(v)))]
print('verifying %d snapshots (of %d hits) by byte-sniff'%(len(pick),len(hits)),flush=True)
MAGIC=[(b'\xff\xd8\xff','jpg'),(b'\x89PNG','png'),(b'GIF8','gif'),(b'RIFF','webp'),(b'\x1aE\xdf\xa3','webm')]
def sniff(b):
    for m,n in MAGIC:
        if b.startswith(m): return n
    if len(b)>=12 and b[4:8]==b'ftyp': return 'mp4'
    low=b[:600].lower()
    if b'<html' in low or b'<!doctype' in low: return 'html'
    return 'other'
res=collections.Counter()
for r in pick:
    u=re.sub(r'/web/(\d{14})/','/web/\\1id_/',r['snap_url'])
    if 'web.archive.org' not in u.split('/')[2]: continue
    k='?';n=None
    for attempt in (1,2):
        req=urllib.request.Request(u); req.add_header('User-Agent',UA); req.add_header('Accept','*/*')
        try:
            with urllib.request.urlopen(req,timeout=60) as rr:
                b=rr.read(8192); n=rr.headers.get('Content-Length'); k=sniff(b); break
        except urllib.error.HTTPError as e: k='HTTP%s'%e.code; break
        except Exception as e:
            k='ERR:'+type(e).__name__
            if attempt==1: time.sleep(5); continue
    res[r['stratum']+'|'+k]+=1
    print('  %-20s %-10s %10s  %s'%(r['stratum'],k,n,r['url'][:58]),flush=True)
    time.sleep(2.0)
print()
print('=== byte-verified snapshot content by stratum')
for s in sorted({k.split('|')[0] for k in res}):
    d={k.split('|')[1]:v for k,v in res.items() if k.startswith(s+'|')}
    real=sum(v for k,v in d.items() if k in ('jpg','png','gif','webp','mp4','webm'))
    print('  %-20s real-media %d/%d   %s'%(s,real,sum(d.values()),d))
tot=sum(res.values()); rm=sum(v for k,v in res.items() if k.split('|')[1] in ('jpg','png','gif','webp','mp4','webm'))
print('  TOTAL real media %d/%d = %.0f%%'%(rm,tot,100.0*rm/tot if tot else 0))

# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
# Fetch actual snapshot BYTES from web.archive.org and sniff. Only archive.org is contacted.
import os,sys,json,re,time,random,collections,urllib.request,urllib.error
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
os.makedirs(A, exist_ok=True)
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) reddit-archive-audit/1.0'
recs=[json.loads(l) for l in open(os.path.join(A,'wayback_results.jsonl'),encoding='utf-8') if l.strip()]
hits=[r for r in recs if r['verdict']=='HIT' and r.get('snap_url')]
by=collections.defaultdict(list)
for r in hits: by[r['stratum']].append(r)
random.seed(3)
pick=[r for s,v in by.items() for r in random.sample(v,min(6,len(v)))]
print('verifying %d snapshots by byte-sniff'%len(pick),flush=True)
MAGIC=[(b'\xff\xd8\xff','jpg'),(b'\x89PNG','png'),(b'GIF8','gif'),(b'RIFF','webp'),(b'\x1aE\xdf\xa3','webm')]
def sniff(b):
    for m,n in MAGIC:
        if b.startswith(m): return n
    if len(b)>=12 and b[4:8]==b'ftyp': return 'mp4'
    low=b[:400].lower()
    if b'<html' in low or b'<!doctype' in low: return 'html'
    return 'other'
res=collections.Counter(); rows=[]
for r in pick:
    u=re.sub(r'/web/(\d{14})/','/web/\\1id_/',r['snap_url'])
    if not u.startswith('http://web.archive.org') and not u.startswith('https://web.archive.org'):
        print('  skip non-archive url'); continue
    req=urllib.request.Request(u); req.add_header('User-Agent',UA); req.add_header('Range','bytes=0-4095')
    try:
        with urllib.request.urlopen(req,timeout=45) as rr:
            b=rr.read(4096); ct=(rr.headers.get('Content-Type') or '').lower()
            cr=rr.headers.get('Content-Range'); n=None
            if cr and '/' in cr:
                try: n=int(cr.rsplit('/',1)[-1])
                except ValueError: pass
            k=sniff(b)
    except urllib.error.HTTPError as e: k='HTTP%s'%e.code; ct='';n=None
    except Exception as e: k='ERR:'+type(e).__name__; ct='';n=None
    res[r['stratum']+'|'+k]+=1
    rows.append((r['stratum'],k,n,r['url'][:52]))
    print('  %-20s %-8s %9s  %s'%(r['stratum'],k,n,r['url'][:60]),flush=True)
    time.sleep(1.4)
print()
print('=== byte-verified snapshot content by stratum')
st=sorted({k.split('|')[0] for k in res})
for s in st:
    d={k.split('|')[1]:v for k,v in res.items() if k.startswith(s+'|')}
    real=sum(v for k,v in d.items() if k in ('jpg','png','gif','webp','mp4','webm'))
    print('  %-20s real-media %d/%d   %s'%(s,real,sum(d.values()),d))

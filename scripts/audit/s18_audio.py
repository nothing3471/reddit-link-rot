# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,re,json,struct,random,collections,sqlite3
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
def has_audio(path,cap=6*1024*1024):
    """Scan the first/last chunk of an mp4 for an 'soun' handler box."""
    try:
        sz=os.path.getsize(path)
        with open(path,'rb') as fh:
            a=fh.read(cap)
            if sz>cap:
                fh.seek(max(0,sz-cap)); a+=fh.read(cap)
    except OSError: return None
    if b'hdlr' not in a: return None
    # 'soun' appears as handler_type right after 'hdlr'+8 bytes
    for m in re.finditer(b'hdlr',a):
        ht=a[m.end()+8:m.end()+12]
        if ht==b'soun': return True
    return False

vids=[]
for dp,dn,fn in os.walk(os.path.join(R,'Video')):
    for f in fn:
        if f.lower().endswith(('.mp4','.m4v','.mov')): vids.append(os.path.join(dp,f))
print('mp4-family videos in Video bucket:',len(vids))
random.seed(7); s=random.sample(vids,min(400,len(vids)))
c=collections.Counter()
noaud=[]
for p in s:
    r=has_audio(p); c[r]+=1
    if r is False: noaud.append(p)
print('sample n=%d  has_audio: %s'%(len(s),dict(c)))
print('  -> silent (video-only) share: %.1f%%'%(100.0*c[False]/len(s)))
for p in noaud[:8]: print('     SILENT %8d B  %s'%(os.path.getsize(p),os.path.basename(p)[:88]))
print()
print('=== which source produced the silent ones? (v.redd.it posts vs other)')
con=sqlite3.connect(os.path.join(R,'Reddit Export','reddit_saved.db'))
pid=re.compile(r'_([a-z0-9]{4,10})_(\d{8})(?:_\d{2})?$',re.I)
def getid(p):
    m=pid.search(os.path.splitext(os.path.basename(p))[0]); return m.group(1).lower() if m else None
dom={}
for i,d,mu in con.execute("select id,domain,media_url from posts"): dom[i]=(d,mu)
cc=collections.Counter()
for p in noaud:
    i=getid(p); cc[(dom.get(i) or ('?',''))[0]]+=1
print('  silent-file domains:',cc.most_common(8))
ca=collections.Counter()
for p in s:
    i=getid(p); ca[(dom.get(i) or ('?',''))[0]]+=1
print('  sampled-file domains:',ca.most_common(8))
print()
print('=== v.redd.it media_url shapes in the DB (does it carry audio?)')
sh=collections.Counter()
for i,(d,mu) in dom.items():
    if d=='v.redd.it': sh[re.sub(r'DASH_\d+','DASH_N',(mu or '').split('/')[-1])]+=1
print(' ',sh.most_common(8))
print()
print('=== domain-field corruption (domain holding a permalink path)')
bad=[i for i,(d,mu) in dom.items() if d and d.startswith('/r/')]
print('  rows whose domain field is a subreddit path, not a host:',len(bad))

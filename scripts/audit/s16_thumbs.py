# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,csv,re,json,collections,struct
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
dead=list(csv.DictReader(open(os.path.join(R,'_logs','dead_list_candidates.csv'),encoding='utf-8',newline='')))
print('=== A. what the thumbnail URLs actually promise (parsed from the URL itself)')
dim=collections.Counter(); crop=collections.Counter(); host=collections.Counter()
nothumb=0
for x in dead:
    t=x['thumbnail'] or ''
    if not t.startswith('http'): nothumb+=1; continue
    host[re.sub(r'^https?://','',t).split('/')[0]]+=1
    w=re.search(r'width=(\d+)',t); h=re.search(r'height=(\d+)',t)
    dim[(w.group(1) if w else '?',h.group(1) if h else '?')]+=1
    crop['square_crop' if 'crop=1' in t else ('aspect' if w else 'no_size_param')]+=1
print('  rows with no usable thumbnail:',nothumb,'of',len(dead))
print('  thumb hosts:',host.most_common(6))
print('  crop style:',crop.most_common())
print('  top declared sizes:',dim.most_common(12))
tall=[d for d in dim if d[1].isdigit() and int(d[1])>0]
import statistics
hs=[int(d[1]) for d in dim for _ in range(dim[d]) if d[1].isdigit()]
if hs: print('  height: median=%d  p10=%d p90=%d  min=%d max=%d'%(statistics.median(hs),
      sorted(hs)[len(hs)//10],sorted(hs)[9*len(hs)//10],min(hs),max(hs)))
print()
print('=== B. preview_url is NOT 140px - what does it promise?')
pw=collections.Counter()
for x in dead:
    p=x['preview_url'] or ''
    if not p.startswith('http'): pw['none']+=1; continue
    m=re.search(r'width=(\d+)',p)
    pw[m.group(1) if m else 'no width param (full-size preview)']+=1
print(' ',pw.most_common(6))
print()
print('=== C. measured bytes for thumbnail vs preview fetches (from failures.jsonl)')
recs=[]
for l in open(os.path.join(R,'_logs','failures.jsonl'),encoding='utf-8'):
    l=l.strip()
    if l:
        try: recs.append(json.loads(l))
        except Exception: pass
for tag,pat in (('thumbnail','thumbs.redditmedia.com'),('preview','external-preview.redd.it')):
    b=[r['bytes'] for r in recs if r.get('url') and pat in r['url'] and isinstance(r.get('bytes'),int)]
    if b:
        b.sort()
        print('  %-10s n=%4d  median=%6d B  p10=%6d  p90=%7d  max=%7d'%(tag,len(b),b[len(b)//2],b[len(b)//10],b[9*len(b)//10],b[-1]))
print()
print('=== D. is the EXISTING archive already polluted with thumbnail-grade files?')
sizes=[]
for bkt in ('Images','Animated'):
    for dp,dn,fn in os.walk(os.path.join(R,bkt)):
        for f in fn:
            try: sizes.append((os.path.getsize(os.path.join(dp,f)),os.path.join(dp,f)))
            except OSError: pass
sizes.sort()
n=len(sizes)
print('  image/animated files: %d ; median %d B'%(n,sizes[n//2][0]))
for thr in (5000,10000,20000,50000):
    print('    < %6d B : %5d files (%.1f%%)'%(thr,sum(1 for s,_ in sizes if s<thr),100.0*sum(1 for s,_ in sizes if s<thr)/n))
print('  smallest 10:')
for s,p in sizes[:10]: print('     %7d  %s'%(s,os.path.basename(p)[:95]))

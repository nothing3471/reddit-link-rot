# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,json,sqlite3,re,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
os.makedirs(A, exist_ok=True)
con=sqlite3.connect(os.path.join(R,'Reddit Export','reddit_saved.db'))
cur=con.execute("select id,url,domain,media_url,gallery_urls,thumbnail,is_gallery,is_video,post_hint,removed_by,status,is_self from posts")
cols=[c[0] for c in cur.description]; byid={r[0]:dict(zip(cols,r)) for r in cur}
rest=set(json.load(open(os.path.join(A,'refetch_ids.json'))))
print('residual size:',len(rest))

MEDIA_HOST=re.compile(r'(i\.redd\.it|v\.redd\.it|i\.imgur\.com|imgur\.com|gfycat\.com|redgifs\.com|giphy\.com|reddituploads|streamable|\.gif$|\.jpg$|\.jpeg$|\.png$|\.mp4$|\.webm$|\.gifv$)',re.I)
LINKONLY=re.compile(r'(youtube\.com|youtu\.be|wikipedia\.org|netflix\.com|twitter\.com|x\.com|twitch\.tv|reddit\.com|nytimes|theguardian|variety\.com|bbc\.|cnn\.|washingtonpost|imdb\.com|amazon\.|spotify|soundcloud|github\.com|medium\.com)',re.I)
cls=collections.Counter(); examples=collections.defaultdict(list)
for i in rest:
    r=byid[i]; u=r['url'] or ''; dom=(r['domain'] or '').lower()
    mu=r['media_url'] or ''
    if dom in ('i.redd.it',): k='reddit_image'
    elif dom in ('v.redd.it',): k='reddit_video(DASH)'
    elif MEDIA_HOST.search(dom) or MEDIA_HOST.search(u): k='other_media_host'
    elif LINKONLY.search(dom): k='LINK_ONLY_not_media'
    else: k='unknown_host'
    cls[k]+=1
    if len(examples[k])<4: examples[k].append(dom+' | '+u[:70])
for k,n in cls.most_common():
    print('  %-22s %6d'%(k,n))
    for e in examples[k]: print('        ',e)
print()
print('=== does the residual double-count galleries?')
g=[i for i in rest if byid[i]['is_gallery']==1]
tot=0
for i in g:
    try: tot+=len(json.loads(byid[i]['gallery_urls'] or '[]'))
    except Exception: pass
print('  gallery posts in residual: %d ; total gallery asset urls behind them: %d (expansion +%d files)'%(len(g),tot,tot-len(g)))
allg=[i for i in byid if byid[i]['is_gallery']==1]
tot2=0
for i in allg:
    try: tot2+=len(json.loads(byid[i]['gallery_urls'] or '[]'))
    except Exception: pass
print('  DB-wide: %d gallery posts -> %d asset urls'%(len(allg),tot2))
print()
print('=== residual rows whose media_url is missing/unusable')
bad=[i for i in rest if not (byid[i]['media_url'] or '').startswith('http')]
print('  no http media_url:',len(bad),collections.Counter(byid[i]['domain'] for i in bad).most_common(8))
print()
print('=== reconciling 13,264 vs my 13,884  (delta 620)')
print('  residual minus LINK_ONLY  = ',len(rest)-cls['LINK_ONLY_not_media'])
print('  residual minus unknown    = ',len(rest)-cls['unknown_host'])
print('  residual minus (link+unk) = ',len(rest)-cls['LINK_ONLY_not_media']-cls['unknown_host'])
print('  residual minus no-media_url =',len(rest)-len(bad))

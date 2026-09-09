# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,json,csv,re,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
idx=json.load(open(os.path.join(R,'Scripts and Data','_media_index.json'),encoding='utf-8',errors='replace'))
print('index entries:',len(idx))
print('loc:',collections.Counter(e.get('loc') for e in idx).most_common())
roots=collections.Counter()
for e in idx:
    p=e['path']; roots[os.sep.join(p.split(os.sep)[:4])]+=1
print('roots:',roots.most_common(10))
alive=sum(1 for e in idx[:4000] if os.path.exists(e['path']))
print('sample 4000 paths still exist:',alive)

# asset id inside parentheses, e.g. "title (md9tk6jq9kbe1).jpeg"
paren=re.compile(r'\(([A-Za-z0-9_\-]{5,32})\)[^()]*$')
asset2path=collections.defaultdict(list)
for e in idx:
    fn=os.path.basename(e['path'])
    m=paren.search(os.path.splitext(fn)[0])
    if m: asset2path[m.group(1).lower()].append(e['path'])
print('distinct asset ids in index:',len(asset2path))

dead=list(csv.DictReader(open(os.path.join(R,'_logs','dead_list_candidates.csv'),encoding='utf-8',newline='')))
def assets(u):
    out=set()
    for m in re.finditer(r'(?:i\.imgur\.com|imgur\.com|i\.redd\.it|v\.redd\.it|gfycat\.com|i\.reddituploads\.com)/(?:a/|gallery/)?([A-Za-z0-9_\-]{4,40})',u or ''):
        out.add(m.group(1).lower().rsplit('.',1)[0])
    return out
hit=0; hitrows=[]
for x in dead:
    a=assets(x['url'])
    f=[p for k in a for p in asset2path.get(k,[])]
    if f: hit+=1; hitrows.append((x['id'],x['stratum'],x['url'],f[0]))
print()
print('=== dead-list posts whose media ASSET appears in the historical media index: %d / %d'%(hit,len(dead)))
for r in hitrows[:25]: print('   ',r[0],r[1],r[2][:70],'->',r[3][:110])
still=[r for r in hitrows if os.path.exists(r[3])]
print('   ... of which the file STILL EXISTS on disk today:',len(still))
for r in still[:20]: print('      EXISTS',r[0],r[3][:130])
json.dump(hitrows,open(os.path.join(A,'dead_asset_hits.json'),'w'))

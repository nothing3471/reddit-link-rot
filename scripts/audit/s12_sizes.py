# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,json,re,csv,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
os.makedirs(A, exist_ok=True)
idx=json.load(open(os.path.join(R,'Scripts and Data','_media_index.json'),encoding='utf-8',errors='replace'))
paren=re.compile(r'\(([A-Za-z0-9_\-]{5,32})\)[^()]*$')
want=set(json.load(open(os.path.join(A,'dead_asset_hits.json')))and[])
hits=json.load(open(os.path.join(A,'dead_asset_hits.json')))
wantpaths=set(h[3] for h in hits)
deadsizes=collections.Counter()
for e in idx:
    if e['path'] in wantpaths and e['size']: deadsizes[e['size']]+=1
print('dead-asset index entries with size:',sum(deadsizes.values()),'distinct sizes:',len(deadsizes))

bsz=collections.Counter(); nb=0
for b in ('Images','Video','Animated','Text'):
    for dp,dn,fn in os.walk(os.path.join(R,b)):
        for f in fn:
            try: bsz[os.path.getsize(os.path.join(dp,f))]+=1; nb+=1
            except OSError: pass
print('bucket files:',nb,'distinct sizes:',len(bsz))
common=set(deadsizes)&set(bsz)
print('exact size collisions between dead assets and bucket files:',len(common),
      '(files involved: %d bucket / %d dead)'%(sum(bsz[s] for s in common),sum(deadsizes[s] for s in common)))
print('  -> a rename-not-loss story would need thousands of these')
# also: do the bucket files match the index at all (sanity that index sizes are comparable)
allidx=collections.Counter(e['size'] for e in idx if e.get('size'))
ov=set(allidx)&set(bsz)
print('sanity: bucket sizes also present anywhere in the 62,984-entry index:',len(ov),
      '(%.0f%% of bucket distinct sizes)'%(100.0*len(ov)/len(bsz)))

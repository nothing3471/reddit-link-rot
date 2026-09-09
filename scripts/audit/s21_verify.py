# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,csv,json,random,collections,sqlite3,re,math
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
os.makedirs(A, exist_ok=True)
print('=== V1. re-derive 8,938 a different way: DB ids that appear in any bucket filename')
con=sqlite3.connect(os.path.join(R,'Reddit Export','reddit_saved.db'))
ids=set(r[0].lower() for r in con.execute("select id from posts"))
found=set(); nfiles=0; noid=0
for b in ('Images','Video','Animated','Text'):
    for dp,dn,fn in os.walk(os.path.join(R,b)):
        for f in fn:
            nfiles+=1
            stem=os.path.splitext(f)[0].lower()
            toks=re.split(r'[_\s\.\(\)\[\]]+',stem)
            hit=[t for t in toks if t in ids]
            if hit: found.add(hit[-1])
            else: noid+=1
print('  files walked: %d   distinct DB ids matched by token: %d   files with no DB id token: %d'%(nfiles,len(found),noid))
prev=set().union(*[set(json.load(open(os.path.join(A,'disk_ids.json')))[k]) for k in ('Images','Video','Animated','Text')])
print('  regex-method set: %d ; token-method set: %d ; agree on %d ; regex-only %d ; token-only %d'%(
      len(prev),len(found),len(prev&found),len(prev-found),len(found-prev)))

print()
print('=== V2. bootstrap the weighted full-quality estimate (no Wilson formula)')
dead=list(csv.DictReader(open(os.path.join(R,'_logs','dead_list_candidates.csv'),encoding='utf-8',newline='')))
N=collections.Counter(x['stratum'] for x in dead)
full={'gfycat':(6,100),'imgur_album':(0,100),'imgur_direct':(92,100),'imgur_gifv':(86,100),
      'other_deadhost':(9,98),'removed_external':(44,100),'removed_reddit_cdn':(66,100)}
random.seed(11); NT=sum(N.values()); ests=[]
for _ in range(20000):
    tot=0.0
    for s,(k,n) in full.items():
        draw=sum(1 for _ in range(n) if random.random()<k/n) if 0<k<n else k
        tot+=(draw/n)*N[s]
    ests.append(tot/NT)
ests.sort()
print('  bootstrap mean %.1f%%  95%% percentile CI [%.1f%% , %.1f%%]  -> %d to %d posts'%(
      100*sum(ests)/len(ests),100*ests[500],100*ests[19499],round(ests[500]*NT),round(ests[19499]*NT)))
print('  (unweighted sample proportion for comparison: %.1f%%)'%(100*sum(k for k,n in full.values())/sum(n for k,n in full.values())))

print()
print('=== V3. is the dead list stratum assignment self-consistent with the url?')
mis=collections.Counter()
for x in dead:
    u=x['url']; s=x['stratum']
    ok = (s=='imgur_gifv' and u.endswith('.gifv')) or \
         (s=='imgur_direct' and 'i.imgur.com' in u and not u.endswith('.gifv')) or \
         (s=='imgur_album' and re.search(r'imgur\.com/(a|gallery)/',u)) or \
         (s=='gfycat' and 'gfycat.com' in u) or \
         (s in ('removed_reddit_cdn','removed_external','other_deadhost'))
    if not ok: mis[s]+=1
print('  rows whose url contradicts their stratum:',dict(mis),'total',sum(mis.values()))
print()
print('=== V4. removed_reddit_cdn composition (the v.redd.it question)')
d=collections.Counter(x['domain'] for x in dead if x['stratum']=='removed_reddit_cdn')
print(' ',d.most_common(6))
print('  dead-list rows on v.redd.it overall:',sum(1 for x in dead if x['domain']=='v.redd.it'))
print('  dead-list rows on i.redd.it overall:',sum(1 for x in dead if x['domain']=='i.redd.it'))

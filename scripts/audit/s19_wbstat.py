# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,json,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
p=os.path.join(R,'_logs','_audit3','wayback_results.jsonl')
recs=[json.loads(l) for l in open(p,encoding='utf-8') if l.strip()]
print('records so far:',len(recs))
c=collections.Counter(r['verdict'] for r in recs)
print('verdicts:',c.most_common())
tab=collections.defaultdict(collections.Counter)
for r in recs: tab[r['stratum']][r['verdict']]+=1
print('%-20s %5s %5s %5s %7s'%('stratum','HIT','MISS','other','hit%'))
for s in sorted(tab):
    h=tab[s]['HIT']; m=tab[s]['MISS']; o=sum(tab[s].values())-h-m; t=h+m+o
    print('%-20s %5d %5d %5d %6.0f%%'%(s,h,m,o,100.0*h/t if t else 0))
hits=[r for r in recs if r['verdict']=='HIT']
print()
print('snapshot http status of hits:',collections.Counter(r['snap_status'] for r in hits).most_common())
print('snapshot year:',collections.Counter((r['ts'] or '????')[:4] for r in hits).most_common(10))
print('sample hits:')
for r in hits[:10]: print('   ',r['stratum'],r['url'][:60],'->',r['snap_url'])

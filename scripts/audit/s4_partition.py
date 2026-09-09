# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,sqlite3,json,csv,re,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
os.makedirs(A, exist_ok=True)
con=sqlite3.connect(os.path.join(R,'Reddit Export','reddit_saved.db'))
cur=con.execute("select id,status,url,domain,media_url,gallery_urls,thumbnail,is_self,is_gallery,is_video,removed_by,post_hint from posts")
cols=[c[0] for c in cur.description]
rows=[dict(zip(cols,r)) for r in cur]
print('db rows',len(rows),'distinct ids',len(set(r['id'] for r in rows)))

disk=set(json.load(open(os.path.join(A,'disk_ids.json')))['Images'])
d=json.load(open(os.path.join(A,'disk_ids.json')))
disk=set().union(*[set(d[k]) for k in ('Images','Video','Animated','Text')])
print('disk ids',len(disk))

dead=list(csv.DictReader(open(os.path.join(R,'_logs','dead_list_candidates.csv'),encoding='utf-8',newline='')))
print('dead list rows',len(dead),'distinct ids',len(set(x['id'] for x in dead)))
deadids=set(x['id'] for x in dead)

byid={r['id']:r for r in rows}
print()
print('=== A. dead-list integrity')
print('dead ids not present in db:',len(deadids-set(byid)))
print('dead ids ALSO ON DISK      :',len(deadids&disk))
print('dead stratum counts:',collections.Counter(x['stratum'] for x in dead).most_common())
print('dead has_fallback:',collections.Counter(x['has_fallback'] for x in dead).most_common())
print('dead rows with empty url:',sum(1 for x in dead if not x['url'].startswith('http')))
print()
print('=== B. residual / partition')
NON=set()
for r in rows:
    u=(r['url'] or '')
    dom=(r['domain'] or '')
    if r['is_self']==1 or dom.startswith('self.') or r['status']!='ok' or not u.startswith('http'):
        NON.add(r['id'])
print('non-media/unfetchable (self, status!=ok, no url):',len(NON))
rest=set(byid)-disk-deadids-NON
print('33716 - disk(%d) - dead(%d) - non(%d) [with overlaps removed] = %d'%(len(disk),len(deadids),len(NON),len(rest)))
print('overlaps: disk&dead=%d disk&NON=%d dead&NON=%d'%(len(disk&deadids),len(disk&NON),len(deadids&NON)))
json.dump(sorted(rest),open(os.path.join(A,'refetch_ids.json'),'w'))
print()
print('=== C. what is in the residual (candidate refetchable) set')
print('domains:',collections.Counter((byid[i]['domain'] or '') for i in rest).most_common(15))
print('is_gallery in residual:',sum(1 for i in rest if byid[i]['is_gallery']==1))
print('no media_url and no gallery_urls in residual:',sum(1 for i in rest if (not byid[i]['media_url'] or byid[i]['media_url']=='None') and (not byid[i]['gallery_urls'] or byid[i]['gallery_urls'] in ('None','[]'))))
print('removed_by set in residual:',collections.Counter(byid[i]['removed_by'] for i in rest).most_common())

# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,json,csv,re,sqlite3,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
dead=list(csv.DictReader(open(os.path.join(R,'_logs','dead_list_candidates.csv'),encoding='utf-8',newline='')))
deadids=set(x['id'] for x in dead)
d=json.load(open(os.path.join(A,'disk_ids.json')))
disk=set().union(*[set(d[k]) for k in ('Images','Video','Animated','Text')])

# 1. yt-dlp download archive
arch=set()
p=os.path.join(R,'Reddit Export','downloaded_archive.txt')
for l in open(p,encoding='utf-8',errors='replace'):
    t=l.split()
    if len(t)>=2: arch.add(t[-1].lower())
print('downloaded_archive tokens:',len(arch))
print('  dead ids in yt-dlp archive:',len(deadids&arch))
print('  disk ids in yt-dlp archive:',len(disk&arch))

# 2. media_index / media_hashed json
for f in ('_media_index.json','_media_hashed.json'):
    p=os.path.join(R,'Scripts and Data',f)
    if not os.path.exists(p): print(f,'MISSING'); continue
    try: j=json.load(open(p,encoding='utf-8',errors='replace'))
    except Exception as e: print(f,'unparsable',e); continue
    print(f,'type',type(j).__name__,'len',len(j))
    if isinstance(j,dict): k0=list(j)[:2]; print('   sample keys',k0,'->',str(j[k0[0]])[:200] if k0 else '')
    else: print('   sample',str(j[0])[:250] if j else '')

# 3. media_library.db
p=os.path.join(R,'Scripts and Data','media_library.db')
if os.path.exists(p):
    c=sqlite3.connect(p)
    tabs=[r[0] for r in c.execute("select name from sqlite_master where type='table'")]
    print('media_library tables:',tabs)
    for t in tabs:
        try:
            n=c.execute('select count(*) from "%s"'%t).fetchone()[0]
            cols=[x[1] for x in c.execute('PRAGMA table_info("%s")'%t)]
            print('  %-22s n=%-8d cols=%s'%(t,n,cols))
        except Exception as e: print('  ',t,e)

# 4. error_list*.txt (BDFR logs) -- did any dead post ever download OK
els=[f for f in os.listdir(os.path.join(R,'Scripts and Data')) if f.lower().startswith('error') or f.lower().startswith('d_reddit')]
print('log files:',els)

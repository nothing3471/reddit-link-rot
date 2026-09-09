# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,sqlite3,json
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
db=os.path.join(R,'Reddit Export','reddit_saved.db')
con=sqlite3.connect(db)
for t in ('posts','grabs'):
    print('==',t,con.execute("select count(*) from %s"%t).fetchone()[0])
    for d in con.execute("PRAGMA table_info(%s)"%t):
        print('   ',d[1],d[2])
print('--- sample posts')
cur=con.execute("select * from posts limit 2")
cols=[c[0] for c in cur.description]
for r in cur:
    print(json.dumps(dict(zip(cols,[str(x)[:140] for x in r])),indent=1)[:1600])
print('--- sample grabs')
cur=con.execute("select * from grabs limit 2")
cols=[c[0] for c in cur.description]
for r in cur:
    print(json.dumps(dict(zip(cols,[str(x)[:140] for x in r])),indent=1)[:1600])

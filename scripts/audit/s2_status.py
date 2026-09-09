# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,sqlite3,json,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
con=sqlite3.connect(os.path.join(R,'Reddit Export','reddit_saved.db'))
c=con.cursor()
print('status:',collections.Counter(r[0] for r in c.execute("select status from posts")).most_common())
print()
print('is_self=1:',c.execute("select count(*) from posts where is_self=1").fetchone()[0])
print('is_gallery=1:',c.execute("select count(*) from posts where is_gallery=1").fetchone()[0])
print('is_video=1:',c.execute("select count(*) from posts where is_video=1").fetchone()[0])
print('removed_by not null/None:',c.execute("select count(*) from posts where removed_by is not null and removed_by<>'None' and removed_by<>''").fetchone()[0])
print('removed_by values:',collections.Counter(r[0] for r in c.execute("select removed_by from posts")).most_common(12))
print()
print('media_url empty/None:',c.execute("select count(*) from posts where media_url is null or media_url='' or media_url='None'").fetchone()[0])
print('gallery_urls present:',c.execute("select count(*) from posts where gallery_urls is not null and gallery_urls<>'' and gallery_urls<>'None' and gallery_urls<>'[]'").fetchone()[0])
print('thumbnail usable:',c.execute("select count(*) from posts where thumbnail like 'http%'").fetchone()[0])
print('thumbnail values non-http:',collections.Counter(r[0] for r in c.execute("select thumbnail from posts where thumbnail not like 'http%' or thumbnail is null")).most_common(10))
print()
print('domains top40:')
for d,n in collections.Counter((r[0] or '') for r in c.execute("select domain from posts")).most_common(40):
    print('   %-32s %6d'%(d,n))

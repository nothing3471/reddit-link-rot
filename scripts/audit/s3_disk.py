# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,re,json,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
os.makedirs(os.path.join(R,'_logs','_audit3'), exist_ok=True)
# filename pattern: {sub}_{title}_{id}_{YYYYMMDD}[_NN].ext   OR  {id}_{title}.ext (older pools)
pat_new=re.compile(r'_([a-z0-9]{4,10})_(\d{8})(?:_\d{2})?$',re.I)
pat_old=re.compile(r'^([a-z0-9]{4,10})_',re.I)

pools={}
for name,sub in [('Images','Images'),('Video','Video'),('Animated','Animated'),('Text','Text'),
                 ('MediaTitled','Media Titled'),('MediaBySub','Media by Subreddit'),
                 ('ExportMedia',os.path.join('Reddit Export','media'))]:
    p=os.path.join(R,sub)
    files=[];ids=set()
    if os.path.isdir(p):
        for dp,dn,fn in os.walk(p):
            for f in fn:
                if f.lower() in ('desktop.ini',) or f.lower().endswith('.txt') and name!='Text': 
                    if name!='Text': continue
                files.append(os.path.join(dp,f))
                stem=os.path.splitext(f)[0]
                m=pat_new.search(stem)
                if m: ids.add(m.group(1).lower()); continue
                m=pat_old.match(stem)
                if m: ids.add(m.group(1).lower())
    pools[name]=(files,ids)
    print('%-14s files=%6d  distinct_ids=%6d'%(name,len(files),len(ids)))

buckets=set().union(*[pools[k][1] for k in ('Images','Video','Animated','Text')])
bfiles=sum(len(pools[k][0]) for k in ('Images','Video','Animated','Text'))
old=pools['MediaTitled'][1]|pools['MediaBySub'][1]
print()
print('four buckets: files=%d distinct_ids=%d'%(bfiles,len(buckets)))
print('old pools   : distinct_ids=%d'%len(old))
print('buckets & old overlap ids=%d ; old-only=%d ; buckets-only=%d'%(len(buckets&old),len(old-buckets),len(buckets-old)))
print('ALL pools distinct ids=%d'%len(buckets|old|pools['ExportMedia'][1]))
# s4, s8 and s21 read disk_ids.json as ground truth about what is on disk. An
# all-empty file is indistinguishable to them from "genuinely nothing archived",
# so refuse to write one rather than hand three downstream scripts a confident
# wrong answer. Zero here almost always means REDDIT_ARCHIVE points somewhere
# that is not an archive.
if not (buckets or old or pools['ExportMedia'][1]):
    print()
    print('Found no media anywhere under %s.'%R)
    print('Expected at least one of: Images, Video, Animated, Text,')
    print('Media Titled, Media by Subreddit, Reddit Export/media.')
    sys.exit('Not writing disk_ids.json - s4, s8 and s21 would read it as fact.')

json.dump({k:sorted(v[1]) for k,v in pools.items()},open(os.path.join(R,'_logs','_audit3','disk_ids.json'),'w'))
print('per-bucket counts:',{k:(len(pools[k][0]),len(pools[k][1])) for k in ('Images','Video','Animated','Text')})

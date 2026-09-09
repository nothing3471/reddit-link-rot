# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,json,collections,re
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
cand=['Reddit Export/media_urls.txt','Reddit Export/media_urls_v2.txt','Reddit Export/media_urls_video_only_pending.txt',
      'Reddit Export/missing_ids.txt','Reddit Export/downloaded_archive.txt','Reddit Export/_retry_images.txt',
      'Reddit Export/_unique_reddit_ids.txt','Reddit Export/_true_submission_ids.txt','Reddit Export/_test_archive.txt',
      'Reddit Export/_title_fetch_done_ids.txt','Scripts and Data/post_ids.txt','_logs/curation_seen.csv']
for c in cand:
    p=os.path.join(R,c.replace('/',os.sep))
    if not os.path.exists(p): print('%-52s MISSING'%c); continue
    n=0;first=None
    with open(p,encoding='utf-8',errors='replace') as fh:
        for i,l in enumerate(fh):
            if l.strip():
                n+=1
                if first is None: first=l.strip()[:120]
    print('%-52s lines=%6d  | %s'%(c,n,first))

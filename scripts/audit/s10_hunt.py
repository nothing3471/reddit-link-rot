# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,json,re,csv,collections,time
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
A=os.path.join(R,'_logs','_audit3')
os.makedirs(A, exist_ok=True)
_hits_path=os.path.join(A,'dead_asset_hits.json')
if not os.path.exists(_hits_path):
    print('Missing %s' % _hits_path)
    sys.exit('Run s9_assetmatch.py first - it is what writes that file.')
hits=json.load(open(_hits_path))
want=set()
paren=re.compile(r'\(([A-Za-z0-9_\-]{5,32})\)[^()]*$')
for pid,st,url,path in hits:
    m=paren.search(os.path.splitext(os.path.basename(path))[0])
    if m: want.add(m.group(1).lower())
print('distinct dead-post asset ids to hunt:',len(want))

roots=[os.path.expanduser('~')+r'\Desktop',os.path.expanduser('~')+r'\Downloads',os.path.expanduser('~')+r'\Documents',
       os.path.expanduser('~')+r'\Pictures',os.path.expanduser('~')+r'\Videos',r'D:\\',r'E:\\']
# This walks your whole profile and two entire drives. That is fine on the
# machine it was written for and is not fine as the default behaviour of a
# script somebody cloned five minutes ago, so it asks first.
if '--scan' not in sys.argv:
    print()
    print('This would walk every file under:')
    for r in roots: print('   ', r)
    print()
    print('That is your whole user profile and two entire drives. It reads only')
    print('filenames, writes nothing outside _logs/_audit3, and can take a long')
    print('time on a large disk.')
    print()
    print('Re-run with --scan to go ahead, or edit `roots` above first.')
    sys.exit(0)

found={}; scanned=0; t0=time.time()
skip=re.compile(r'\\(node_modules|\.git|AppData|Windows|Program Files|\$Recycle)',re.I)
for root in roots:
    if not os.path.isdir(root): print('  (no root %s)'%root); continue
    for dp,dn,fn in os.walk(root):
        if skip.search(dp): dn[:]=[]; continue
        for f in fn:
            scanned+=1
            stem=os.path.splitext(f)[0]
            m=paren.search(stem)
            if m and m.group(1).lower() in want:
                found.setdefault(m.group(1).lower(),os.path.join(dp,f))
    print('  after %-32s scanned=%d found=%d  %.0fs'%(root,scanned,len(found),time.time()-t0))
print()
print('TOTAL files scanned:',scanned)
print('dead-post assets found live on disk:',len(found),'/',len(want))
for k,v in list(found.items())[:25]: print('   ',k,'->',v[:140])
json.dump(found,open(os.path.join(A,'found_assets.json'),'w'))

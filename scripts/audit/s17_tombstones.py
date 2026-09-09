# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,hashlib,collections,json,re
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
MAGIC=[(b'\xff\xd8\xff','jpg'),(b'\x89PNG','png'),(b'GIF8','gif'),(b'RIFF','webp'),
       (b'\x1aE\xdf\xa3','webm'),(b'ID3','mp3'),(b'OggS','ogg'),(b'%PDF','pdf'),(b'<!DO','html'),(b'<htm','html'),(b'<?xm','xml')]
def sniff(b):
    for m,n in MAGIC:
        if b.startswith(m): return n
    if len(b)>=12 and b[4:8]==b'ftyp': return 'mp4'
    return 'UNKNOWN'
rows=[];small=[]
for bkt in ('Images','Video','Animated'):
    for dp,dn,fn in os.walk(os.path.join(R,bkt)):
        for f in fn:
            p=os.path.join(dp,f)
            try: sz=os.path.getsize(p)
            except OSError: continue
            if sz<30000:
                with open(p,'rb') as fh: head=fh.read(64)
                h=hashlib.md5(open(p,'rb').read()).hexdigest() if sz<200000 else ''
                small.append((sz,sniff(head),h,f,bkt))
print('files <30 KB in Images/Video/Animated:',len(small))
print()
print('=== identical-content clusters among small files (md5)')
byh=collections.Counter(s[2] for s in small)
dupes=[(h,n) for h,n in byh.most_common(12) if n>1]
tot_dupe=0
for h,n in dupes:
    ex=[s for s in small if s[2]==h][0]
    tot_dupe+=n
    print('  %3d copies  %7d B  %-6s  e.g. %s'%(n,ex[0],ex[1],ex[3][:80]))
print('  total files in repeated-content clusters:',tot_dupe)
print()
print('=== what is the 503-byte png?')
z=[s for s in small if s[0]==503]
if z:
    p=None
    for dp,dn,fn in os.walk(os.path.join(R,'Images')):
        for f in fn:
            if f==z[0][3]: p=os.path.join(dp,f);break
        if p:break
    if p:
        d=open(p,'rb').read()
        print('  bytes:',len(d),'sniff:',sniff(d))
        # PNG IHDR: width/height at offset 16..24
        if d[:4]==b'\x89PNG':
            import struct
            w,hh=struct.unpack('>II',d[16:24])
            print('  PNG dimensions: %dx%d'%(w,hh))
        print('  copies of this exact file in archive:',byh[z[0][2]])
print()
print('=== sniffed-type distribution of small files')
print(collections.Counter(s[1] for s in small).most_common())
print()
print('=== non-media (UNKNOWN/html) files at ANY size - full scan')
bad=[]
for bkt in ('Images','Video','Animated'):
    for dp,dn,fn in os.walk(os.path.join(R,bkt)):
        for f in fn:
            p=os.path.join(dp,f)
            try:
                with open(p,'rb') as fh: head=fh.read(32)
            except OSError: continue
            if sniff(head) in ('UNKNOWN','html','xml'): bad.append((os.path.getsize(p),sniff(head),f,bkt))
print('  non-media files:',len(bad))
print(collections.Counter(b[1] for b in bad).most_common())
for b in bad[:15]: print('    %8d %-8s %s'%(b[0],b[1],b[2][:90]))
json.dump([[b[0],b[1],b[2],b[3]] for b in bad],open(os.path.join(R,'_logs','_audit3','nonmedia.json'),'w'))

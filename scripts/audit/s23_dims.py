# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,struct,collections,statistics,random
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
def dims(p):
    try:
        with open(p,'rb') as f:
            h=f.read(32)
            if h[:8]==b'\x89PNG\r\n\x1a\n':
                w,hh=struct.unpack('>II',h[16:24]); return w,hh
            if h[:3]==b'\xff\xd8\xff':
                f.seek(2)
                while True:
                    b=f.read(1)
                    if not b: return None
                    if b!=b'\xff': continue
                    m=f.read(1)
                    while m==b'\xff': m=f.read(1)
                    if not m: return None
                    if m[0] in (0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF):
                        f.read(3); hh,w=struct.unpack('>HH',f.read(4)); return w,hh
                    ln=struct.unpack('>H',f.read(2))[0]; f.seek(ln-2,1)
            if h[:4]==b'GIF8':
                w,hh=struct.unpack('<HH',h[6:10]); return w,hh
            if h[:4]==b'RIFF' and h[8:12]==b'WEBP':
                if h[12:16]==b'VP8X':
                    d=h[24:30]; return (d[0]|d[1]<<8|d[2]<<16)+1,(d[3]|d[4]<<8|d[5]<<16)+1
                return None
    except Exception: return None
    return None
files=[]
for b in ('Images','Animated'):
    for dp,dn,fn in os.walk(os.path.join(R,b)):
        for f in fn: files.append(os.path.join(dp,f))
print('image files:',len(files))
ws=[];small=[]
for p in files:
    d=dims(p)
    if d:
        ws.append(max(d))
        if max(d)<=200: small.append((d,os.path.getsize(p),os.path.basename(p)))
ws.sort()
if not ws:
    sys.exit('No image dimensions could be read from %d file(s). Nothing to measure.' % len(files))
print('long-edge px measured for %d/%d'%(len(ws),len(files)))
print('  min=%d p05=%d p25=%d median=%d p75=%d p95=%d max=%d'%(ws[0],ws[len(ws)//20],ws[len(ws)//4],ws[len(ws)//2],ws[3*len(ws)//4],ws[19*len(ws)//20],ws[-1]))
for thr in (140,200,320,480,640):
    print('  long edge <= %4d px : %5d files (%.1f%%)'%(thr,sum(1 for w in ws if w<=thr),100.0*sum(1 for w in ws if w<=thr)/len(ws)))
print()
print('=== files already in the archive at thumbnail scale (<=200px long edge): %d'%len(small))
for d,sz,n in small[:20]: print('   %4dx%-4d %7d B  %s'%(d[0],d[1],sz,n[:88]))

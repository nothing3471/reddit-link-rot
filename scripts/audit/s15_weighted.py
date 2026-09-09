# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,csv,math,collections
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
dead=list(csv.DictReader(open(os.path.join(R,'_logs','dead_list_candidates.csv'),encoding='utf-8',newline='')))
N=collections.Counter(x['stratum'] for x in dead)
# sample-v3: (alive, dead) and recovery method breakdown, straight from sample_v3_result.txt
S={ # stratum: (n_probed, {method:count}, n_dead)
 'gfycat':(100,{'preview':51,'redgifs':6,'thumbnail':40},3),
 'imgur_album':(100,{'preview':2,'thumbnail':79},19),
 'imgur_direct':(100,{'original':92,'thumbnail':5},3),
 'imgur_gifv':(100,{'gifv_mp4':86,'preview':5,'thumbnail':5},4),
 'other_deadhost':(98,{'original':9,'thumbnail':69},20),
 'removed_external':(100,{'gifv_mp4':28,'original':16},56),
 'removed_reddit_cdn':(100,{'original':66,'preview':1},33)}
CAT={'original':'full','gifv_mp4':'full','redgifs':'full','preview':'preview','thumbnail':'thumb'}
def wilson(k,n,z=1.96):
    if n<=0: return (0.0,1.0)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0.,c-h),min(1.,c+h))
def fpc(n,Np): return math.sqrt(max(0.0,(Np-n)/(Np-1))) if Np>1 else 0.0

cats=['full','preview','thumb','dead']
print('%-20s %5s %4s | %-38s'%('stratum','N','n','full / preview / thumb / dead  (sample counts)'))
agg={c:[0.0,0.0,0.0] for c in cats}   # point, lo_posts, hi_posts
unw={c:0 for c in cats}; ntot=0
for s in sorted(N):
    n,meth,nd=S[s]; n=min(n,N[s])
    k={c:0 for c in cats}
    for m,v in meth.items(): k[CAT[m]]+=v
    k['dead']=nd
    tot=sum(k.values())
    print('%-20s %5d %4d | %3d / %3d / %3d / %3d'%(s,N[s],n,k['full'],k['preview'],k['thumb'],k['dead']))
    for c in cats:
        lo,hi=wilson(k[c],tot); f=fpc(tot,N[s]); mid=(lo+hi)/2; hw=(hi-lo)/2*f
        agg[c][0]+=k[c]/tot*N[s]; agg[c][1]+=max(0,mid-hw)*N[s]; agg[c][2]+=min(1,mid+hw)*N[s]
        unw[c]+=k[c]
    ntot+=tot
NT=sum(N.values())
print()
print('%-12s %-26s %-26s'%('outcome','UNWEIGHTED (what was reported)','POPULATION-WEIGHTED (correct)'))
for c in cats:
    print('%-12s %5.1f%%  (%d/%d)%-10s %5.1f%%   [%4.1f%%-%4.1f%%]  =%5d posts  [%d-%d]'%(
        c,100*unw[c]/ntot,unw[c],ntot,'',100*agg[c][0]/NT,100*agg[c][1]/NT,100*agg[c][2]/NT,
        round(agg[c][0]),round(agg[c][1]),round(agg[c][2])))
print()
print('sum of weighted point estimates: %d of %d'%(round(sum(agg[c][0] for c in cats)),NT))

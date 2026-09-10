# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
import os,sys,csv,math,collections,json
sys.stdout.reconfigure(encoding='utf-8')
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
dead=list(csv.DictReader(open(os.path.join(R,'_logs','dead_list_candidates.csv'),encoding='utf-8',newline='')))
N=collections.Counter(x['stratum'] for x in dead)

# sample-v3 (latest) results, transcribed from sample_v3_result.txt
v3={'gfycat':(97,100),'imgur_album':(81,100),'imgur_direct':(97,100),'imgur_gifv':(96,100),
    'other_deadhost':(78,98),'removed_external':(44,100),'removed_reddit_cdn':(67,100)}
# full-quality (original/gifv_mp4/redgifs) vs preview vs thumbnail, from 'recovered via'
via={'gfycat':{'preview':51,'redgifs':6,'thumbnail':40},
     'imgur_album':{'preview':2,'thumbnail':79},
     'imgur_direct':{'original':92,'thumbnail':5},
     'imgur_gifv':{'gifv_mp4':86,'preview':5,'thumbnail':5},
     'other_deadhost':{'original':9,'thumbnail':69},
     'removed_external':{'gifv_mp4':28,'original':16},
     'removed_reddit_cdn':{'original':66,'preview':1}}
FULL={'original','gifv_mp4','redgifs'}

def wilson(k,n,z=1.96):
    if n==0: return (0.0,1.0)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0.0,c-h),min(1.0,c+h))
def fpc(n,Npop): return math.sqrt((Npop-n)/(Npop-1)) if Npop>1 and n<Npop else 0.0

print('%-20s %6s %5s %8s %-18s %-18s'%('stratum','N_pop','n','full-q','95%CI full-quality','±posts at N_pop'))
tot_lo=tot_hi=tot_pt=0
for s in sorted(N):
    n=v3[s][1]; k=sum(v for kk,v in via[s].items() if kk in FULL)
    lo,hi=wilson(k,n); f=fpc(n,N[s])
    # apply finite-population correction to the half-width
    mid=(lo+hi)/2; hw=(hi-lo)/2*f
    lo2,hi2=max(0,mid-hw),min(1,mid+hw)
    print('%-20s %6d %5d %7.0f%% [%5.1f%% , %5.1f%%]  %6d - %6d'%(s,N[s],n,100*k/n,100*lo2,100*hi2,round(lo2*N[s]),round(hi2*N[s])))
    tot_lo+=lo2*N[s]; tot_hi+=hi2*N[s]; tot_pt+=k/n*N[s]
print('%-20s %6d %5d %7.0f%% [%5.1f%% , %5.1f%%]  %6d - %6d'%('TOTAL(strat.)',sum(N.values()),700,
      100*tot_pt/sum(N.values()),100*tot_lo/sum(N.values()),100*tot_hi/sum(N.values()),round(tot_lo),round(tot_hi)))
print()
print('=== thin strata: sample fraction and whether n=100 is a big slice of N')
for s in sorted(N,key=lambda x:N[x]):
    print('  %-20s N=%5d  n=100  sampling fraction %5.1f%%  fpc=%.3f'%(s,N[s],100.0/N[s]*100,fpc(100,N[s])))
print()
print('=== run-to-run instability (sample vs sample-v3, same 698 rows, same seed)')
s1={'gfycat':97,'imgur_album':100,'imgur_direct':99,'imgur_gifv':100,'other_deadhost':78,'removed_external':49,'removed_reddit_cdn':73}
for s in sorted(N):
    a,b=s1[s],v3[s][0]
    print('  %-20s alive: %3d -> %3d   delta %+d'%(s,a,b,b-a))

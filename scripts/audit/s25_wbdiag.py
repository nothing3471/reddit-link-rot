import sys,ssl,socket,urllib.request,urllib.error,time
sys.stdout.reconfigure(encoding='utf-8')
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
tests=[('archive.org availability API','https://archive.org/wayback/available?url=example.com'),
       ('web.archive.org root','https://web.archive.org/'),
       ('web.archive.org replay (html)','https://web.archive.org/web/2023/https://example.com/'),
       ('web.archive.org replay (image)','https://web.archive.org/web/20230509074804/https://i.imgur.com/4qqYSa0.jpg')]
for name,u in tests:
    try:
        print('  DNS %-32s -> %s'%(u.split('/')[2],socket.gethostbyname(u.split('/')[2])))
    except Exception as e:
        print('  DNS %-32s -> FAIL %s'%(u.split('/')[2],e))
    req=urllib.request.Request(u); req.add_header('User-Agent',UA)
    t=time.time()
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            b=r.read(600)
            print('  OK  %-32s HTTP %s  %s  %d bytes read  %.1fs'%(name,r.status,(r.headers.get('Content-Type') or '')[:24],len(b),time.time()-t))
    except urllib.error.HTTPError as e: print('  --  %-32s HTTP %s  %.1fs'%(name,e.code,time.time()-t))
    except Exception as e: print('  XX  %-32s %s: %s  %.1fs'%(name,type(e).__name__,str(e)[:70],time.time()-t))
    time.sleep(2)

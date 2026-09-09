# Archive paths come from the REDDIT_ARCHIVE environment variable.
# Set it to your own archive root before running.
# -*- coding: utf-8 -*-
import os, sys, json, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R=os.environ.get('REDDIT_ARCHIVE') or sys.exit('REDDIT_ARCHIVE is not set. Point it at your archive root and re-run - see the README.')
L=os.path.join(R,'_logs')
s = json.load(open(os.path.join(L, "download_status.json"), encoding="utf-8"))
recs = [json.loads(x) for x in open(os.path.join(L, "download_log.jsonl"),
        encoding="utf-8", errors="replace") if x.strip()]
cur = [r for r in recs if (r.get("ts") or "") >= s["started"]]
print("elapsed=%ss  records=%d  files_this_run=%s  rate=%s/min"
      % (s["elapsed_s"], len(cur), s["files_this_run"], s["files_per_min"]))
print("verdicts:", dict(collections.Counter(r.get("verdict") for r in cur)))
print("statuses:", dict(collections.Counter(r.get("status") for r in cur)))
print("hosts   :", dict(collections.Counter(r.get("host") for r in cur).most_common(6)))
print("gfycat records since restart (must be 0):",
      sum(1 for r in cur if "gfycat" in (r.get("host") or "")))
print("\nsample:")
for r in cur[:5]:
    print("   st=%-5s %-26s %s" % (r.get("status"), (r.get("host") or "")[:26],
                                   (r.get("error") or "")[:46]))
print("\nlast 3:")
for r in cur[-3:]:
    print("   %s st=%-5s %-24s %s" % (r["ts"][11:19], r.get("status"),
          (r.get("host") or "")[:24], (r.get("error") or r.get("bucket") or "")[:40]))

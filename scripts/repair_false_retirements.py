# -*- coding: utf-8 -*-
"""
Un-retire posts that were marked permanently 'dead' by the pre-fix
failure_log.py bug (the `verdict or classify(...)` override).

The code bug is already fixed in both layers:
  * failure_log.py   - _OMITTED sentinel, so an explicit None is honoured
  * download_archive.py - explicit verdict ladder; 403 -> "retry", and only
                          the last candidate of a non-gallery post may retire

But the fix is not retroactive. load_done() re-reads download_log.jsonl on every
run and retires any post that has a 'dead' record, so the bad verdicts written
before the fix still suppress those posts forever.

Target: records with verdict='dead' on the direct-HTTP path whose status the
CURRENT code could never retire on - i.e. anything that is not 404/410 and not
a 2xx-with-no-media. In practice that is a burst of 403 bot-blocks.

Rewrites those records' verdict to 'retry' and stamps them with `corrected`,
so the audit trail survives. Backs up first. Read-only unless --apply.

Usage:
    python repair_false_retirements.py            # dry run, changes nothing
    python repair_false_retirements.py --apply    # back up, then rewrite
"""
import json, os, shutil, sys
from collections import defaultdict

ARCHIVE = os.environ.get("REDDIT_ARCHIVE") or sys.exit(
    "REDDIT_ARCHIVE is not set. Point it at your archive root and re-run "
    "- see the README.")
LOG    = os.path.join(ARCHIVE, "_logs", "download_log.jsonl")
MARKER = "false-retirement-prefix-failure_log"
APPLY  = "--apply" in sys.argv


def is_false_retirement(r):
    """True if the current code could not have written this 'dead'."""
    if r.get("phase") != "download" or r.get("verdict") != "dead":
        return False
    if r.get("via") == "yt-dlp":      # yt-dlp path has its own transient list
        return False
    st = r.get("status")
    if st in (404, 410):              # genuine absence
        return False
    if st is not None and 200 <= st < 300:
        return False                  # HTML shell / imgur tombstone
    return True


def main():
    if not os.path.exists(LOG):
        sys.exit("not found: %s" % LOG)

    lines = open(LOG, encoding="utf-8", errors="replace").read().splitlines()
    recs, hits = [], []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            recs.append((i, None)); continue
        try:
            r = json.loads(s)
        except Exception:
            recs.append((i, None)); continue
        recs.append((i, r))
        if is_false_retirement(r):
            hits.append((i, r))

    posts = sorted({r.get("post_id") for _, r in hits})
    print("log records      : %d" % sum(1 for _, r in recs if r))
    print("false retirements: %d records / %d distinct posts" % (len(hits), len(posts)))
    if not hits:
        print("nothing to do."); return

    by_status = defaultdict(int)
    for _, r in hits:
        by_status[r.get("status")] += 1
    print("by status        : %s" % dict(by_status))
    print("window           : %s .. %s" % (min(r.get("ts", "") for _, r in hits)[:19],
                                           max(r.get("ts", "") for _, r in hits)[:19]))

    # Would any of these immediately re-retire on the attempt cap? load_done()
    # collapses attempts inside min_gap_s into one occasion and caps at 4.
    retry_ts = defaultdict(list)
    for _, r in recs:
        if r and r.get("phase") == "download" and r.get("verdict") == "retry":
            pid = (r.get("post_id") or "").lower()
            if pid in {p.lower() for p in posts}:
                retry_ts[pid].append(r.get("ts", ""))
    risky = {p: len(v) for p, v in retry_ts.items() if len(v) >= 4}
    print("posts already at/over the 4-attempt cap: %d %s"
          % (len(risky), risky if risky else ""))

    if not APPLY:
        print("\nDRY RUN - nothing written. Re-run with --apply to fix.")
        for _, r in hits[:10]:
            print("   %s st=%s %s" % (r.get("ts", "")[:19], r.get("status"),
                                      str(r.get("url"))[:70]))
        return

    bak = LOG + ".bak-before-retirement-repair"
    if not os.path.exists(bak):
        shutil.copy2(LOG, bak)
        print("\nbackup: %s" % bak)
    else:
        print("\nbackup already exists, not overwriting: %s" % bak)

    idx = {i for i, _ in hits}
    out = []
    for i, line in enumerate(lines):
        if i in idx:
            r = json.loads(line)
            r["verdict"] = "retry"
            r["corrected"] = MARKER
            out.append(json.dumps(r, ensure_ascii=False))
        else:
            out.append(line)

    tmp = LOG + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
        fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, LOG)                      # atomic
    print("rewrote %d records -> verdict='retry'" % len(hits))

    # verify
    again = [r for r in (json.loads(l) for l in
                         open(LOG, encoding="utf-8", errors="replace").read().splitlines() if l.strip())
             if is_false_retirement(r)]
    print("re-scan false retirements: %d  ->  %s"
          % (len(again), "PASS" if not again else "*** FAIL ***"))
    print("corrected markers present: %d"
          % sum(1 for l in open(LOG, encoding="utf-8", errors="replace") if MARKER in l))


if __name__ == "__main__":
    main()

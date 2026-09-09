# -*- coding: utf-8 -*-
"""
Measure gfycat recovery properly, by sampling the posts the downloader skipped.

WHY THIS EXISTS
    The 6% gfycat prior was never validated. The production run attempted only
    123 of 1,174 gfycat posts - the rule in DEAD_HOST_RE drops gfycat URLs
    because the domain's DNS is gone, so a post survives only when it has some
    other usable candidate. That leaves:

        6.4%  posts with a file on disk   <- a FLOOR, depressed by the skip
       61.0%  success among those tried   <- a CEILING, and badly selection-
                                             biased: those posts were kept
                                             precisely because they had a
                                             working alternative candidate

    The real value lies somewhere between and cannot be recovered from the
    existing logs. Only a random sample of the NEVER-ATTEMPTED posts can settle
    it.

METHOD
    Sample n posts uniformly at random (fixed seed, so the draw is reproducible
    and cannot be re-rolled until it flatters the result) from the skipped set,
    ask the Internet Archive availability API whether a snapshot exists, and
    optionally fetch the snapshot bytes to confirm it is an image rather than an
    HTML shell.

    That byte check is not optional in spirit. The audit's first probe run was
    invalidated precisely because it scored HTTP 200 HTML shells as live media.
    Availability != media. If --verify cannot run, the result is an availability
    rate, and must be reported as such.

    Only archive.org is contacted. gfycat itself is never requested - there is
    nothing at the other end and a DNS timeout costs ~18s.

USAGE
    python sample_gfycat_recovery.py                 # plan only, no network
    python sample_gfycat_recovery.py --probe         # + availability API
    python sample_gfycat_recovery.py --probe --verify  # + byte-sniff snapshots

    --n 150     sample size (default 150 -> about +/-7 points at 95%)
    --seed 20260903
"""
import argparse, csv, json, math, os, random, re, sqlite3, sys, time
from urllib.parse import quote

ARCHIVE = os.environ.get("REDDIT_ARCHIVE") or sys.exit(
    "REDDIT_ARCHIVE is not set. Point it at your archive root and re-run "
    "- see the README.")
DB      = os.path.join(ARCHIVE, "Reddit Export", "reddit_saved.db")
LOG     = os.path.join(ARCHIVE, "_logs", "download_log.jsonl")
# Results go to the archive, not next to this script. Writing them into a git
# checkout is how a sample of your own saved posts ends up in a commit.
OUT     = os.path.join(ARCHIVE, "_logs", "gfycat_sample_results.csv")

AVAIL   = "https://archive.org/wayback/available?url=%s"
PACE_S  = 1.5          # be a good citizen; archive.org is a donated resource
MAGIC   = {b"\xff\xd8\xff": "jpg", b"\x89PNG": "png", b"GIF8": "gif",
           b"RIFF": "webp", b"\x00\x00\x00": "mp4"}


def wilson(k, n, N=None, z=1.96):
    """Wilson interval, with finite-population correction when N is given."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    if N and N > n:
        z *= math.sqrt((N - n) / (N - 1))
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round(max(0.0, (c - m) / d) * 100, 1), round(min(1.0, (c + m) / d) * 100, 1))


def load_population():
    """gfycat posts that the run never attempted."""
    if not os.path.exists(DB):
        sys.exit("database not found: %s" % DB)
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    rows = con.execute("SELECT lower(id), coalesce(media_url,''), coalesce(url,''), "
                       "coalesce(title,''), coalesce(subreddit,'') FROM posts").fetchall()
    gfy = [r for r in rows if "gfycat.com" in (r[1] + " " + r[2]).lower()]

    attempted = set()
    if os.path.exists(LOG):
        for line in open(LOG, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line:
                try:
                    attempted.add((json.loads(line).get("post_id") or "").lower())
                except Exception:
                    pass
    else:
        # Without the log every gfycat post looks never-attempted, and the
        # sample silently comes from the wrong population - the whole point of
        # this script is the never-attempted subset. Say so rather than print a
        # plausible plan.
        print("WARNING: %s not found." % LOG)
        print("         Treating all %d gfycat posts as never-attempted." % len(gfy))
        print("         That is NOT the population the README's Finding 9 describes,")
        print("         and any rate measured from it is not comparable to the 6%% prior.")
        print()

    skipped = [r for r in gfy if r[0] not in attempted]
    return gfy, skipped


def probe(url, verify, timeout=20):
    """-> (available, media_confirmed, snapshot_url, note)"""
    import urllib.request
    req = urllib.request.Request(AVAIL % quote(url, safe=""),
                                 headers={"User-Agent": "gfycat-recovery-sample/1.0"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())
    except Exception as e:
        return (None, None, "", "availability-api: %s" % type(e).__name__)
    snap = (d.get("archived_snapshots") or {}).get("closest") or {}
    if not snap.get("available"):
        return (False, False, "", "no snapshot")
    su = snap.get("url", "")
    if not verify:
        return (True, None, su, "not byte-verified")
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(su, headers={"User-Agent": "gfycat-recovery-sample/1.0"}),
            timeout=timeout)
        head = r.read(64)
    except Exception as e:
        # web.archive.org was host-blocked on the original network; say so
        # plainly rather than scoring it as a miss.
        return (True, None, su, "replay unreachable: %s" % type(e).__name__)
    kind = next((v for k, v in MAGIC.items() if head.startswith(k)), None)
    if kind is None and head.lstrip()[:1] in (b"<",):
        return (True, False, su, "HTML shell, not media")
    return (True, bool(kind), su, kind or "unrecognised bytes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20260903)
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()

    gfy, skipped = load_population()
    print("gfycat posts in DB      : %d" % len(gfy))
    print("never attempted (target): %d" % len(skipped))
    if not skipped:
        print("nothing to sample."); return

    n = min(a.n, len(skipped))
    random.Random(a.seed).shuffle(skipped)
    sample = skipped[:n]
    lo, hi = wilson(int(0.3 * n), n, len(skipped))
    print("sample size             : %d  (seed %d)" % (n, a.seed))
    print("precision at p=0.30     : +/-%.1f points (Wilson, FPC N=%d)"
          % ((hi - lo) / 2, len(skipped)))

    if not a.probe:
        print("\nPLAN ONLY - no network calls made. Add --probe to run it.")
        print("Estimated wall time at %.1fs pacing: %.0f min" % (PACE_S, n * PACE_S / 60))
        for pid, mu, u, title, sub in sample[:5]:
            print("   %s  r/%-18s %s" % (pid, sub[:18], (mu or u)[:58]))
        return

    if not a.verify:
        print("\nNOTE: without --verify this measures AVAILABILITY, not recovered media.")

    res, avail, media = [], 0, 0
    for i, (pid, mu, u, title, sub) in enumerate(sample, 1):
        target = mu or u
        av, md, su, note = probe(target, a.verify)
        avail += 1 if av else 0
        media += 1 if md else 0
        res.append(dict(post_id=pid, subreddit=sub, url=target, available=av,
                        media_confirmed=md, snapshot=su, note=note))
        if i % 10 == 0 or i == n:
            print("  %d/%d  available=%d media=%d" % (i, n, avail, media), flush=True)
        time.sleep(PACE_S)

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)

    N = len(skipped)
    al, ah = wilson(avail, n, N)
    print("\n--- RESULT (population: %d never-attempted gfycat posts) ---" % N)
    print("availability : %d/%d = %.1f%%  (95%% CI %.1f-%.1f)" % (avail, n, 100*avail/n, al, ah))
    if a.verify:
        ml, mh = wilson(media, n, N)
        print("media confirmed: %d/%d = %.1f%%  (95%% CI %.1f-%.1f)" % (media, n, 100*media/n, ml, mh))
        print("=> gfycat recovery estimate: %.1f%% (%.1f-%.1f), vs 6%% prior" % (100*media/n, ml, mh))
        print("   projected recoverable posts: %d (%d-%d)"
              % (round(N*media/n), round(N*ml/100), round(N*mh/100)))
    else:
        print("=> AVAILABILITY only. Re-run with --verify before quoting a recovery rate.")
    unreachable = sum(1 for r in res if "unreachable" in (r["note"] or ""))
    if unreachable:
        print("\n%d/%d replay fetches failed - if that is most of them you have hit the same"
              % (unreachable, n))
        print("host block the audit documented. Re-run from a different network.")
    print("\nwrote %s" % OUT)


if __name__ == "__main__":
    main()

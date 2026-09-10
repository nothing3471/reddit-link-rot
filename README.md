# Most of your "dead" Reddit saves aren't dead: measured recovery rates for 10,326 rotted links

I archived 33,716 saved Reddit posts. 10,326 of them pointed at media that no
longer loads. The obvious question is how much of that is actually gone, and I
couldn't find a published answer — the link-rot literature measures *web pages*,
not media, and never breaks results out by host.

So I measured it — and then I ran the recovery and scored the measurement against
what actually came back. Short version: **at least 70% of the "permanently dead"
media is recoverable at full quality**, and recovery varies from 92% to 0%
depending entirely on which host the link points at.

I say "at least" deliberately. Where the forecast could be checked against real
outcomes, it turned out to be **too pessimistic, not too optimistic** — see
Finding 8. Treat 70% as a floor.

---

## TL;DR

- Recovery is **69.9%** at full quality (95% CI 66.5–73.2), not the 43% I first calculated. The difference is entirely an estimator bug — see below. It's the biggest single correction to the numbers, and Finding 8 then tests whether even it was conservative.
- The forecast was then **run for real and scored**: on the 6,493-post subset where it could be checked, predicted 84.9% vs **actual 98.2%**. The probe-based priors were systematically *too pessimistic*, because a single-URL probe understates a downloader with a fallback chain.
- Recovery rate by host ranges from **92% (imgur direct) to 0% (imgur albums)**. A single blended number is close to useless for planning.
- The Wayback Machine had **68%** of these dead media URLs available — and it's strongest exactly where live refetch is weakest.
- **imgur albums invert completely: 0% live, 86% on Wayback.**
- **Tombstones** — byte-identical placeholder images filed as real media — were 0.5% of my live archive (54 of 11,387 files) and 3.6% of the lost-file set (244 of 6,737). Exact fingerprint below.
- Net result: the archive went from **8,938 to 27,188 posts with media** — 80.6% of all 33,716 saved posts.
- `v.redd.it` and `i.redd.it` require *opposite* download tools. Getting this wrong silently produces thousands of soundless videos.
- The most alarming finding isn't link rot at all: **65% of my "dead" posts were media I had already downloaded and then lost locally.**

---

## Where the data comes from

A Reddit GDPR export (`saved_posts.csv`), hydrated with post metadata to 33,716
rows, plus a SQLite catalog of what actually made it to disk. The partition:

```
33,716  total saved rows
 8,938  have files on disk (11,387 media files)
10,326  dead list — media URL no longer serves media
 1,366  self-posts / no URL / status ≠ ok
13,884  residual, refetchable
```

Those don't sum cleanly because the categories overlap — 715 of the 1,366 also
have files and 83 are also on the dead list, so only 568 are unique to that
bucket. `33,716 − 8,938 − 10,326 − 568 = 13,884`.

Of the 13,884 residual, **1,090 (7.9%) aren't downloadable media at all** —
YouTube links (466), gallery permalinks, Wikipedia, news articles. The real
media-refetch job is 12,794 posts.

## Finding 1: the estimator, not the sample size

I probed a stratified sample of 698 dead-list posts and got 43.4% full-quality
recovery. That number is wrong, and the reason is worth internalising because
it's an easy mistake to repeat.

**Sampling fractions ranged from 3.2% to 100%.** The two largest strata are also
the best performers and the least sampled: `imgur_direct` (N=3,044, 92%) and
`imgur_gifv` (N=3,169, 86%) together are 60% of the dead list but were sampled at
about 3%. The worst performers — `gfycat` at 6%, `imgur_album` at 0% — are small
strata that were sampled heavily.

Averaging the sample flat therefore lets the small, terrible strata drag the
estimate down by 26 percentage points.

| Outcome | Unweighted | **Population-weighted** | 95% CI |
|---|---|---|---|
| Full quality | 43.4% | **69.9%** | 66.5–73.2% |
| Preview only | 8.5% | 7.0% | 5.1–12.2% |
| Thumbnail only | 28.4% | **10.5%** | 7.7–16.3% |
| Dead | 19.8% | **12.5%** | 8.8–19.0% |

Full-quality CI is a 20,000-draw bootstrap; the others are Wilson with a
finite-population correction.

In posts: roughly **7,200 of the 10,326 are recoverable at full quality**, about
2,800 more than the flat average implied.

## Finding 2: recovery by host

This is the table I wanted and couldn't find anywhere.

| Stratum | N | n | Full quality | 95% CI | Usable? |
|---|---|---|---|---|---|
| `imgur_direct` | 3,044 | 100 | 92% | 85–96% | yes — carries the conclusion |
| `imgur_gifv` | 3,169 | 100 | 86% | 78–91% | yes |
| `removed_reddit_cdn` | 2,172 | 100 | 66% | 57–74% | usable, ±190 posts |
| `gfycat` | 1,055 | 100 | 6% | 3.0–12.2% | **too wide to plan against** |
| `removed_external` | 427 | 100 | 44% | 36–53% | **too wide to plan against** |
| `imgur_album` | 361 | 100 | 0% | 0.3–3.4% | direction certain: 0/100 |
| `other_deadhost` | 98 | 98 | 9% | — | census, zero sampling error |

The strata sum to exactly 10,326.

Three honest caveats. `gfycat` spans 32–129 posts at the CI bounds — a 4× spread,
useless for sizing a job. `other_deadhost` is a census, not a sample: the probe
capped at the population, so it's exactly 9 of 98 with no sampling error. And the
`imgur_album` interval is reproduced as my tooling emitted it — note that its
lower bound sits *above* the 0/100 point estimate, which shouldn't happen; a
standard Wilson interval on 0/100 is [0, 3.7%]. The direction is certain either
way (0 of 100), but don't read that particular interval as authoritative.

`.gifv` → `.mp4` substitution works: 86 of 100. imgur albums fail completely at
full quality: 0 of 100.

## Finding 3: the Wayback inversion

I ran 352 dead-list URLs against the Internet Archive availability API.

| Stratum | Wayback available | Live full-quality |
|---|---|---|
| `imgur_album` | **86%** | **0%** |
| `imgur_direct` | 80% | 92% |
| `imgur_gifv` | 76% | 86% |
| `other_deadhost` | **76%** | **9%** |
| `removed_reddit_cdn` | 56% | 66% |
| `removed_external` | 54% | 44% |
| `gfycat` | **55%** | **6%** |
| **overall** | **68%** (241/352) | |

**Wayback is strongest exactly where live refetch is weakest.** The three
inverted strata — `imgur_album`, `other_deadhost`, `gfycat` — are ~1,514 posts
that currently have no full-quality path at all.

For context — and be careful with this comparison, because the usual framing of
it is wrong. The widely quoted figure is that the Wayback Machine rescues about
**15%** of pages, but that is 15% of *all sampled pages*, not of the dead ones.
The apples-to-apples number is that Wayback holds a copy of roughly **38% of dead
URLs**. So my 68% on dead *media* URLs is about a **1.8× gap, not the 4.5× the
"15%" framing implies**.

It's still a real difference, and I read it as evidence that media and pages rot
differently — media may simply be better preserved. But it's a more modest claim
than it first looks, and the caveat below matters more than the gap does.

**This route is unverified and I want to be blunt about that.** Every attempt to
fetch actual snapshot bytes failed: `web.archive.org` reset the connection at
18.5s on every single request including the site root, while `archive.org`
answered in 0.2s — a host-level block on my network, not a rate limit and not my
code. So I can confirm a snapshot *exists*, not that it contains an image rather
than an HTML shell. For `imgur_album` the snapshot is very likely the album
*page*, which is still useful (it would let you enumerate the individual image
URLs the album stratum can't otherwise reach) but is not itself an image.

Don't cost this route until someone byte-verifies it from an unblocked network.

**Update, 2026-09-09.** Re-probed from the same machine and the same network:
`web.archive.org` answers in 0.19s with HTTP 429, and `archive.org` in 0.21s with
200. That is a rate limit — the thing the paragraph above says it was not — and it
is nothing like an 18.5s transport-layer reset. Whatever was happening during the
original run is not happening now, and I have not re-run the snapshot fetches, so
the route remains unverified in the same direction as before. If you are planning
around any of this, probe it yourself first. `scripts/audit/s25_wbdiag.py` is that
probe and needs no archive to run.

## Finding 4: tombstones

54 byte-identical **503-byte, 161×81 PNGs** — imgur's "image removed" graphic —
were sitting in my `Images\` folder under 54 different post titles, indexed as
real media. A separate manifest of 6,737 posts contained 244 more.

If you archive imgur at any scale you have these. The fingerprint:

```
size:  503 bytes exactly
dims:  161 × 81
type:  PNG
hash:  byte-identical across all instances
```

Filter on exact byte size first — it's the cheapest test and it's nearly
sufficient on its own.

Some reassurance from the same scan: only 364 of 11,387 files were under 30 KB,
and no image was ≤140px. The archive wasn't broadly polluted — but "8,938 posts
have files" is 8,877 once you subtract tombstones and 7 other non-media
files (3 HTML pages saved as `.gif`, 2 duplicate blobs, 2 misc).

## Finding 5: the two Reddit hosts need opposite tools

This one costs you real data if you get it wrong.

- **`v.redd.it` must go through yt-dlp.** The `media_url` in the export is a `DASH_720.mp4?source=fallback` — a video-*only* DASH representation. Audio is a separate track. A plain GET returns a silent video, by construction. That would have been 6,480 soundless files. Measured against my existing archive: 39 of 334 sampled v.redd.it mp4s (11.7%) have no audio track, so whatever built the archive was muxing correctly about 88% of the time.
- **`i.redd.it` must NOT go through yt-dlp** — permanent 403 from my network. Direct HTTP with `Referer` and `User-Agent` works.

Same site, two hosts, opposite tools.

**Also: route on the URL, not on the `domain` column.** 587 database rows (1.7%)
carry a subreddit permalink (`/r/.../comments/...`) in the `domain` field
rather than a hostname. Anything that stratifies or routes on that
column misroutes all of them — in my case fetching HTML pages instead of videos.

(My working notes give **651** for what appears to be the same defect counted
against the CSV rather than the database. I've quoted the database figure;
anyone reproducing this should say which source they counted.)

## Finding 6: a 403 on v.redd.it is real

I suspected the `v.redd.it` 403s were rate-limiting artifacts rather than genuine
deletions. They aren't, on three lines of evidence:

1. **Perfect reproducibility.** The same 86 URLs, probed twice in randomised order, agreed on 403-ness **86/86, zero flips**. Throttling doesn't reproduce per-URL across runs.
2. **No temporal clustering.** 35 403s formed 20 separate runs in an 86-request sequence; random arrangement predicts ~21. Throttling produces long consecutive runs.
3. **Not a host block.** 59% of `v.redd.it` requests returned 200/206 in the same run, and both URL shapes showed mixed results.

For contrast, a *real* host-level block on the same network (`web.archive.org`,
above) looks completely different: uniform, transport-layer, 18.5s on every
request, no HTTP response at all. That contrast case no longer reproduces — see
the update under Finding 3 — so read it as a description of what a transport-layer
block looks like rather than as something you can go and observe today.

Treat 403 on `v.redd.it` as "this video is gone."

## Finding 7: the call is coming from inside the house

The finding that actually changed how I think about archiving.

Of the 10,326 "permanently dead" posts, **6,737 (65%) had their media asset
recorded in a pre-consolidation index of 62,984 files. Every one of those files
is now gone.**

I went looking: 195,354 files scanned across three drives and every user folder.
**0 of 6,658 distinct assets found.**

They weren't renamed into the current buckets either. Control test: 86% of my
buckets' distinct file sizes appear somewhere in that 62,984-entry index, so the
buckets did come from that pool and size-matching is a valid detector — yet the
6,658 dead assets produce only 54 size collisions, which is coincidence-level.

The likely mechanism: those files were named by *media asset ID*
(a title followed by the bare asset ID, `some title (aBcDeF1).jpeg`) with no post-ID mapping, so a
reorganisation step couldn't place them, and the source folders were deleted
afterward.

And it wasn't one folder. Reading the recovered-path column directly, the 6,737
lost files split **3,788 from the export's `media\` folder and 2,949 (43.8%) from
a second, separate media pool on another drive**. Two independent storage
locations lost their contents to the same naming problem, which makes a
one-off accident much less likely than a systematic one.

**Two-thirds of what I was calling link rot was my own bookkeeping.** If you
archive at scale, your reorganisation scripts are a bigger threat to your data
than the internet is. Keep a durable ID mapping, and never delete a source
folder in the same operation that reorganises it.

---

## Finding 8: the forecast was validated — and it was too pessimistic

Findings 1–2 are a *forecast*, made from a probe sample before the recovery run
executed. That run has since completed, so the forecast can be scored against
what actually landed on disk. This is the part I'd most want a reader to check.

Validation set: the 6,493 non-tombstone posts whose local copies were lost, each
carrying a per-row prior from the probe. Ground truth is the filesystem.

| Stratum | N | Predicted | Predicted CI | **Actual** | Actual 95% CI | In CI? |
|---|---|---|---|---|---|---|
| `imgur_direct` | 2,798 | 92% | 85–96% | **96.3%** | 95.5–96.9 | no (high) |
| `imgur_gifv` | 2,722 | 86% | 78–91% | **99.9%** | 99.7–100 | no (high) |
| `removed_reddit_cdn` | 774 | 66% | 57–74% | **100.0%** | 99.5–100 | no (high) |
| `removed_external` | 191 | 44% | 36–53% | **100.0%** | 98.0–100 | no (high) |
| `imgur_album` | 8 | 0% | 0–3% | **0.0%** | 0–32.4 | yes |
| **Total** | **6,493** | **84.9%** | | **98.2%** | 97.9–98.5 | — |

**Predicted 5,510 recoveries; actual 6,376. The forecast was low by 866 posts.**
Four of five strata landed above their upper CI bound — a one-directional miss,
which points at a systematic cause rather than noise.

**The cause is the measurement instrument, not the internet.** The priors were
measured by a liveness probe that tested essentially one URL per post. The
production downloader tries an ordered candidate chain — `media_url` first, then
the post URL if it looks like media, then the probe's own seed as last resort —
rewrites `.gifv` to `.mp4` automatically, routes `v.redd.it` through yt-dlp, and
falls back to direct DASH if yt-dlp fails. More shots on goal per post.

That gap is the most transferable result here: **single-URL probe estimates
systematically understate what a real downloader with a fallback chain
achieves.** If you are sizing a recovery job from probe data, treat the probe
number as a floor, not an estimate.

**Scope — read before quoting the 98.2%.** This validation covers the *easy*
part of the dead list. The two worst strata are absent from it entirely:
`gfycat` (1,055 posts, 6% prior) and `other_deadhost` (98 posts, 9% prior) have
zero rows in this set, and `imgur_album` contributes only 8. So 98.2% is the
recovery rate for the tractable majority, **not** for the dead list as a whole,
and the archive-wide 69.9% figure in Finding 1 remains unvalidated at the low
end. Someone should run the same comparison against a set that includes the
dead hosts before treating the headline number as confirmed.

Two guards against the obvious objection that these files were simply already
present: **zero** of the 6,493 appeared in the pre-run on-disk snapshot, and all
6,376 recoveries carry a successful download record from during the run. Nothing
is explained by pre-existing files.

One bookkeeping note, since the two figures differ by two. 6,378 posts have a
successful download record but only 6,376 have a full-quality file. The other
two landed in the thumbnails bucket rather than a media bucket, so they are
counted as *not* recovered. Where the log and the filesystem disagree, the
figures above follow the filesystem, which is the stricter of the two.

For context on scale, the archive went from **8,938 to 27,188 posts with media**
— 80.6% of all 33,716 saved posts.

## Finding 9: the gfycat number is not measured — and a coincidence nearly hid that

I tried to close the gap Finding 8 left open. I couldn't, and the reason is worth
more than the number would have been.

There are **1,174 gfycat posts** in the database — note that this is every gfycat post, not the 1,055 that landed on the dead list and carry the 6% prior in Finding 2. Different denominators, deliberately. Their current state:

| | Posts | |
|---|---|---|
| Have a file on disk now | 75 | 6.4% |
| Attempted during the run | 123 | 10.5% |
| **Never attempted at all** | **1,051** | **89.5%** |
| Retired as dead | 0 | 0% |

gfycat shut down in 2023 and its DNS is gone, so a lookup fails before any HTTP
status exists. Every such post can only be scored "retry" and then burns four
attempts paying a full resolver timeout each. Measured cost: a cluster of 44
gfycat URLs cut throughput from ~290 to ~50 records per 10 minutes. So the
downloader drops gfycat URLs by rule — the post survives only if it has a
different usable candidate.

**Now the trap.** The prior for gfycat was 6%. The observed on-disk rate is
**6.4%**. That looks like clean confirmation, and it is nothing of the kind. The
prior claims *6% of gfycat posts are recoverable*; the observation says *we
attempted 10% of them*. Those are unrelated statements that happen to produce
almost the same number. Had I not checked attempt counts, I would have reported
a validated prior and been badly wrong.

What the data actually supports is a pair of bounds, and they are far apart:

- **6.4% is a floor**, depressed by the skip rule — 89.5% were never tried.
- **61% is a ceiling.** Of the 123 posts actually attempted, 75 succeeded. But those 123 are exactly the posts the rule *kept* because they had a working `external-preview.redd.it` or `api.redgifs.com` candidate — selected for being recoverable. That is severe selection bias, in the optimistic direction.

The true value is somewhere in `[6.4%, 61%]` and this dataset cannot narrow it.
Notably, 61%-on-attempted is ten times the 6% prior, which is the same direction
and rough magnitude as every miss in Finding 8 — so the honest guess is that the
gfycat prior is also far too pessimistic. A guess is not a measurement.

**What would settle it:** a random sample of the 1,051 never-attempted posts,
routed through the Wayback Machine rather than the live host. The audit measured
**55% Wayback availability** for gfycat, which is the only known path for this
stratum. About **150 posts** gives ±7 points at 95% confidence with the
finite-population correction — a small job. `scripts/sample_gfycat_recovery.py`
in the repo below sets it up and is dry-run by default.

Until someone runs that, **the archive-wide 69.9% headline should be quoted as
resting on validated majority strata plus one stratum of ~1,000 posts whose
recovery rate is genuinely unknown.**

## Limitations

- **The Wayback route is unverified.** Availability ≠ media. See Finding 3.
- **`gfycat` and `removed_external` CIs are too wide to plan against.** Don't size a job on them.
- **No content hashes in the pre-consolidation index.** It recorded path and size only, so the Finding 7 matching is by asset ID and byte size — strong, but not proof of byte-identity.
- **Thumbnail characterisation is inferred, not measured.** Only 40 of 6,586 usable thumbnail URLs actually carry a `width=140` parameter; the rest are bare legacy `*.thumbs.redditmedia.com` URLs. Byte sizes support the claim (median 5,385 B, p90 8.2 KB) but the evidence is file size, not pixels.
- **`preview_url` is not a degraded tier.** I initially lumped it in with thumbnails. Only 1,666 rows (16%) have one, none carry a width parameter, and they measure median 26 KB / p90 51 KB / max 1 MB. At the top end that's effectively the original.
- **Single archive, single network, one point in time.** Everything here is one user's saved history probed from one IP in 2026. The imgur strata in particular are measuring the aftermath of imgur's purge of anonymous and NSFW content; someone sampling before that would get different numbers.

## Code and data

- `data/VALIDATION_predicted_vs_actual.csv` — the Finding 8 scoring table: per stratum, predicted rate, prediction CI, actual rate, actual CI. It counts download records, so its total is 6,378 rather than the 6,376 quoted above; `data/README.md` explains the two-post difference
- `scripts/audit/` — the 26 scripts that produced the audit, including the Wayback availability probes and the tombstone detector
- `scripts/sample_gfycat_recovery.py` — the Finding 9 sampler, if you want to close that gap yourself
- `scripts/repair_false_retirements.py` — the only script here that changes your data rather than reading it. It un-retires posts that were marked dead by a prefix-matching bug in the failure log. It needs `--apply` to write anything; without it, it prints what it would do
- MIT for code, CC BY 4.0 for data

### What the audit scripts are, and what they are not

They are the method, not a tool. They ran once, against my archive, to produce the
numbers above, and they are here so those numbers can be checked instead of taken on
trust.

Most of them will not run for you as they stand, and it is worth being exact about
why. They read six files this repo does not contain and cannot generate:

| File | Produced by |
|---|---|
| `Reddit Export/reddit_saved.db` | my downloader, seeded from a Reddit GDPR export |
| `_logs/dead_list_candidates.csv` | the downloader's dead-link pass |
| `_logs/failures.jsonl` | its failure log |
| `_logs/download_log.jsonl` | its per-post attempt log |
| `_logs/download_status.json` | its run state |
| `Scripts and Data/_media_index.json` | the media indexer |
| `Scripts and Data/media_library.db` | the media indexer (`s8` only) |
| `Reddit Export/downloaded_archive.txt` | the downloader's completion log (`s5`, `s8`) |

That downloader is not published. It is wired into my own accounts and paths, and
untangling it is a bigger job than this release. Treat the audit scripts as
reference implementations of each measurement — `s1_schema.py` prints the exact
database schema the other 25 assume, which is the quickest way to see whether your
own archive could be shaped to fit.

They are also not fully independent, despite the flat numbering:

| Writes | Read by |
|---|---|
| `s3_disk.py` → `disk_ids.json` | `s4`, `s8`, `s21` |
| `s9_assetmatch.py` → `dead_asset_hits.json` | `s10`, `s12` |
| `s4_partition.py` → `refetch_ids.json` | `s13` |
| `s11_wayback.py` → `wayback_results.jsonl` | `s19`, `s20`, `s22`, `s24` |

That last one is the longest chain in the repo and it is also the slowest: `s11`
probes the Internet Archive over the network, so the four scripts behind Finding 3
cannot be run until it has finished.

One more thing you should know before quoting any of these numbers. The per-stratum
sample outcomes in `s14_ci.py`, `s15_weighted.py` and `s21_verify.py` are **literal
dicts typed into the source**, transcribed from a probe run (`sample_v3_result.txt`)
that is not in this repo. Those scripts compute the weighting, the Wilson intervals
and the bootstrap from those constants and the population counts — the arithmetic is
reproducible and auditable, the underlying probe is not. The constants are right
there in the source if you want to check my arithmetic against them.

### Running them

Python 3.8 or newer, standard library only. Nothing to install.

```powershell
$env:REDDIT_ARCHIVE = "D:\Reddit Archive"       # PowerShell
set REDDIT_ARCHIVE=D:\Reddit Archive            # cmd
export REDDIT_ARCHIVE="/mnt/d/Reddit Archive"   # bash

python scripts/audit/s1_schema.py
```

Every script that reads the archive says so and stops if the variable is not set.
Two behave differently and it is worth knowing which: `s25_wbdiag.py` is a pure
network diagnostic that never touches your archive, so it runs regardless and
immediately makes live requests to archive.org. And `s10_hunt.py` walks your whole
user profile and your D: and E: drives looking for files by name — it prints the
list and refuses to start until you pass `--scan`.

`scripts/sample_gfycat_recovery.py` is the one worth your time if you have an
archive of your own. It needs only the database and the download log, it is dry-run
until you pass `--probe`, and it writes results into `$REDDIT_ARCHIVE/_logs/` rather
than into this checkout. If the download log is missing it says so loudly, because
without it the sample is drawn from the wrong population and the number means
nothing.

My own paths were stripped out of these before release, and the first pass at that
left `%REDDIT_ARCHIVE%` behind as a literal string. Python does not expand `%VAR%` —
that is cmd.exe syntax. All 25 affected scripts either died on an unopenable path or,
in `s10_hunt.py`'s case, walked nothing and reported zero files scanned as though
that were an answer. They read the variable properly now.

**No media is redistributed and no saved-post content is published** — the release
is aggregate measurements and tooling only. The scripts run against your *own*
Reddit export with your *own* credentials; nothing here calls an API on your
behalf or needs an account of mine.

If you run the gfycat sampler and get a real number for that stratum, I'd genuinely
like to see it — it's the one hole left in this.

---

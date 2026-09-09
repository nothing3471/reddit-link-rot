# Data

Two files, both aggregate. No post titles, no URLs, no filenames, nothing from the
underlying saved-post content.

## `VALIDATION_predicted_vs_actual.csv`

The Finding 8 scoring table: for each stratum, what the probe-based forecast
predicted, what the recovery run actually returned, and whether each figure falls
inside the other's confidence interval.

| Column | Meaning |
|---|---|
| `stratum` | host class the dead link belonged to |
| `n_posts` | posts in that stratum within the 6,493-post checkable subset |
| `predicted_pct` | forecast recovery rate, from the probe sample |
| `predicted_ci_low` / `_high` | 95% interval on that forecast |
| `actual_recovered` | posts the run actually recovered |
| `actual_pct` | observed rate |
| `actual_ci_low` / `_high` | 95% Wilson interval on the observed rate |
| `predicted_inside_actual_ci` | did the forecast land inside the observed interval |
| `actual_inside_predicted_ci` | and the reverse |

### The one thing to know before you use it

**This file counts download records. The README's headline counts files on disk.**

They differ by two posts. 6,378 posts have a successful download record from the
run; 6,376 of those have a full-quality file present afterwards. The README quotes
6,376 because the filesystem is the stricter test and the stricter number is the
honest one to lead with. This CSV carries 6,378, and the per-stratum column sums to
exactly that, so the two views stay internally consistent rather than being mixed.

Neither is wrong. If you re-derive the total from this file you will get 6,378, and
now you know why it is two higher than the number in the write-up.

`imgur_album` has n=8 here, against 361 in the Finding 2 population table. Finding 2
covers the whole dead list; this file covers only the subset the forecast could be
scored against. Its confidence interval also reads `0.0–32.4` on a 0/8 result, which
is wide because eight is a small number, not because anything recovered.

## `LICENSE-DATA.txt`

CC BY 4.0. The code in this repository is MIT; the data is not the same licence.

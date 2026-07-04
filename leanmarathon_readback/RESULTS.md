# LeanMarathon readback — canonical results

Regenerated 2026-07-04 from the result JSONs in this directory (the previous RESULTS.md was a
pre-rerun residue documenting the N=30 pilot; see `Stats history` below). All inferential
statistics below were independently recomputed on 2026-07-03 (`compute_stats.py`, seeded bootstrap
`default_rng(0)`, deterministic) and reproduce exactly the values reported in the TwoLoci paper.

## Paired named vs anon (bootstrap 95% CI, Wilcoxon signed-rank)

| arm | n (paired) | named | anon | Δ | 95% CI | p |
|---|---|---|---|---|---|---|
| statement (LeanMarathon) | 286 | 7.98 | 6.02 | +1.96 | [+1.41, +2.51] | 1.1e-10 |
| method (LeanMarathon) | 297 | 9.81 | 9.04 | +0.77 | [+0.48, +1.08] | 6.8e-07 |
| statement (oseledets) | 137 | 8.75 | 6.24 | +2.51 | [+1.80, +3.24] | 3.3e-09 |

Statement split (LeanMarathon, n=286): 58% structure-carried (Δ≤0), 6% intermediate (0<Δ≤2),
37% name-dependent (Δ>2) — percentages rounded independently. Oseledets: 56% / 36%.

n accounting: 302 blueprint nodes total; per-condition scored 299–301 (judge nulls); pairs =
intersection on unique (repo, gold) keys → 286 statement / 297 method; oseledets 137 paired of
141 matched pairs.

## Validity / application

| check | n | values | Δ | 95% CI | p |
|---|---|---|---|---|---|
| negative control (method) | 60 | correct 9.64 / wrong 0.44 | +9.20 | [+8.57, +9.71] | 2e-12 |
| drift detector (statement) | 56 | clean 8.79 / corrupt 1.56 | +7.22 | [+5.90, +8.39] | 4.6e-10 |

Negative control: 97% of nodes correct > wrong. Drift: 43/56 = 77% detected at the drop≥3 threshold.

## Method ablation ladder (n=80 per condition)

named 9.97 → anon 9.40 → aggr 7.73 → skel 7.21.

## Seeded random rerun (n=150, `lm_rerun.py`)

method: named 9.73 / anon 9.15 / anon_strict 7.69 / sig(no-body) 3.99.
statement: named 8.81 / anon_strict 3.43 (n=148 scored of 150).

## Predictors (`lm_predictors.py`; requires the external corpus clones under `MATHAI/external/`)

Δ(named−anon) vs # maskable identifiers: Spearman ρ=+0.077 (p=0.19), n=299 matched nodes.
Δ vs signature length: ρ=+0.026 (p=0.65). Name-dependence is not explained by either measure.

## Stats history

The RESULTS.md that previously lived here reported pilot/pre-rerun values (N=30 pilot; negctrl
9.44/0.16 n=40; drift 9.17/0.62 n=38; oseledets 8.93/6.60 n=60) matching stale hardcoded labels
in early script headers, not the current JSONs. The canonical values above come from the
full-corpus re-run of 2026-06-21 (JSONs in this directory) and were verified against them on
2026-07-03/04.

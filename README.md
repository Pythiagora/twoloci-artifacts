# TwoLoci — artifacts

Experimental artifacts for the paper **"Two Loci of Method Recoverability"**.

The paper studies **method recoverability** in formal mathematics: given a Lean 4
development with its human-facing identifiers stripped (anonymized), how much of
the underlying *method* — the proof idea, not just the statement — can a reader
still recover from the bare Lean term? The probes isolate two loci: the
**statement** (what is proved) and the **method** (how). Each experiment scores an
LLM reader (and, for cross-checks, a second judge) on paired *named* vs.
*anonymized* conditions and reports the recoverability gap.

This repository is the reproducibility bundle: the probe/analysis code plus every
result JSON the paper's numbers are computed from.

## Layout

Three self-contained experiment directories:

- **`leanmarathon_readback/`** — statement- and method-readback over LeanMarathon
  blueprint nodes (ErdosGraham, Erdos1196, Prim) and the oseledets corpus. Paired
  named-vs-anon scoring, negative control, drift detector, method-ablation ladder,
  seeded rerun, and predictor analysis. `RESULTS.md` is the canonical results table
  (regenerated 2026-07-04); `compute_stats.py` recomputes every inferential
  statistic (seeded bootstrap CIs + Wilcoxon) straight from the JSONs.
- **`multiproof_experiment/`** — within-theorem *method discrimination*: multiple
  distinct proofs of the same theorem (e.g. Infinitude of Primes, Fermat's Little
  Theorem, the Basel problem), anonymized, then read back and cross-judged
  (DeepSeek reader + judge, with an Opus dual-judge agreement check in
  `dualjudge_agreement.py`). `RESULTS.md` summarizes the confusion matrices.
- **`exch_experiment/`** — the de Finetti / exchangeability development probed at
  three granularities (aggregate / signature / locus), scored with the same
  dual-judge protocol. `exch_dualjudge_RESULTS.md` and `RESULTS_matrices.md` hold
  the results.

`.log` files are the original run logs kept alongside each experiment as a record.

## Reproduction

The scripts hardcode paths under `~/Code/AITP`. The path constants live at the top
of `leanmarathon_readback/lm_common.py`, `leanmarathon_readback/compute_stats.py`,
`multiproof_experiment/dualjudge_agreement.py`, and
`multiproof_experiment/mp_prep.py`. To reproduce, either **place this checkout at
`~/Code/AITP`** (so the three experiment dirs sit where the scripts expect them) or
**edit those path constants** to point at wherever you put it.

**Recomputing the statistics (no API, no corpus needed).** All headline numbers
are recomputed from the saved JSONs alone:

```
cd leanmarathon_readback && uv run compute_stats.py
```

Scripts carry inline [PEP 723](https://peps.python.org/pep-0723/) dependency
metadata, so `uv run` resolves scipy/numpy automatically.
`multiproof_experiment/dualjudge_agreement.py` likewise recomputes the
judge-agreement correlations from saved JSONs.

**Re-running the probes (needs the external corpora + an API key).** The
generation/judging scripts call the DeepSeek API and read `DEEPSEEK_API_KEY` from
the environment. They also require local clones of the external Lean corpora under
`MATHAI/external/` at the exact commits pinned in [`CHECKSUMS.md`](CHECKSUMS.md).
In particular:

- `leanmarathon_readback/lm_predictors.py` reads the LeanMarathon blueprint nodes
  from the clones; without them `lm_common.load(...)` matches nothing and the
  script reports `matched 0 nodes`.
- `multiproof_experiment/mp_prep.py` regenerates the `mp_*.json` forms from the
  DifferentProofs corpus, which is **no longer available** (see below) — so this
  step cannot be re-run from source; the `mp_*.json` it produced are shipped here
  as data.

## Provenance note — DifferentProofs

The `multiproof_experiment` results are built on the **DifferentProofs** corpus
(`github.com/seewoo5/DifferentProofs`), which was public at collection time
(2026-05 / 2026-06) but has since become **unavailable (404)** and carried **no
license** at any point we observed it.

Because there is no license and no reachable upstream, this mirror does **not**
redistribute the DifferentProofs source tree. However, the corpus's proof scripts
are embedded — as anonymized and raw `script` fields — inside the
`multiproof_experiment/mp_*.json` files, because they *are* the paper's
experimental data and the corpus is otherwise irrecoverable. A full archived
snapshot of the clone at the exact commit used (SHA256 in
[`CHECKSUMS.md`](CHECKSUMS.md)) is retained by the author and available on
request.

If you are a rights-holder for DifferentProofs and want the embedded excerpts
removed, that **takedown request will be honored** — please contact the author.

## License

Experiment code (the `.py` scripts) is released under the MIT License
(see [`LICENSE`](LICENSE)). Third-party corpus excerpts embedded in the data files
(`mp_*.json`, and any JSON carrying upstream Lean source) remain under their own
terms; see [`CHECKSUMS.md`](CHECKSUMS.md) for each corpus's license status.

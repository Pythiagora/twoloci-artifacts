# External corpora — provenance & checksums

The experiments in this repository draw on seven external Lean 4 corpora. None of
their source trees are redistributed here; the experiment scripts expect local
clones under `~/Code/AITP/MATHAI/external/<name>/` (see `README.md` →
Reproduction). This file pins the exact upstream commit each result was computed
against, together with the license each corpus carried at collection time
(2026-05 / 2026-06).

| Corpus | Clone URL | Commit | License |
|---|---|---|---|
| DifferentProofs | https://github.com/seewoo5/DifferentProofs | `1f3ce5daf4a0d2c4e937bede838a2010ae83b6de` | none — no LICENSE/COPYING file; **repo unavailable (404) since ~2026-06/07** |
| Erdos1196 | https://github.com/YuanheZ/Erdos1196 | `1e960723d96f1375f1b959b6fab656042d90513b` | none — no LICENSE/COPYING file |
| ErdosGraham | https://github.com/YuanheZ/ErdosGraham | `c084fe629b057870b2ef8eb0a1f16c3e05eead53` | none — no LICENSE/COPYING file |
| exchangeability | https://github.com/cameronfreer/exchangeability | `e0532e59ceff23edab44dda9ab0655debbc9cc22` | Apache-2.0 (LICENSE present) |
| lean4-oseledets | https://github.com/marcmorningstar/lean4-oseledets | `640b21bd779ea018e1f1fba783b5dbd119c3345e` | Apache-2.0 (LICENSE present) |
| LeanMarathon | https://github.com/YuanheZ/LeanMarathon | `9ace81e67b556684050f46535fb6b84c9b7fea46` | none — no LICENSE/COPYING file |
| Prim | https://github.com/YuanheZ/Prim | `a303f6bd23bb8f29a833d1d70327528359180995` | none — no LICENSE/COPYING file |

License findings are from a direct scan of each clone (top-level and one level
deep) for `LICENSE` / `COPYING` files; "none" means no such file and no license
declaration in the README. Corpora marked Apache-2.0 ship the standard Apache
License 2.0 text.

## DifferentProofs snapshot

Because the DifferentProofs upstream is no longer reachable and carries no
license, its source tree is **not** included in this mirror. A full archived
snapshot of the clone at commit `1f3ce5d` (the state used for the paper) is
retained privately by the author and is available on request. Its proof scripts
also survive as embedded experimental data inside
`multiproof_experiment/mp_*.json` (see the provenance note in `README.md`).

- Archive: `DifferentProofs_1f3ce5d_2026-06-19.tar.gz` (`tar czf` of the full
  clone directory at commit `1f3ce5daf4a0d2c4e937bede838a2010ae83b6de`,
  including its `.git`)
- SHA256: `100b5835f012c2f8574f405790234351affc4880b25b26b79cb39b30e7ecdffb`

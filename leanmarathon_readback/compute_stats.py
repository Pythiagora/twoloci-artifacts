# /// script
# requires-python = ">=3.11"
# dependencies = ["scipy>=1.11","numpy>=1.26"]
# ///
# Real statistical tests for the readback results (council asked for variance/significance/CIs).
# Paired named-vs-anon (statement/method/oseledets) + negctrl + drift: paired mean Δ, 95% bootstrap CI,
# Wilcoxon signed-rank p. No fabrication — straight from the saved per-item scores.
import json, numpy as np
from pathlib import Path
from scipy.stats import wilcoxon
D=Path.home()/"Code/AITP/leanmarathon_readback"
rng=np.random.default_rng(0)
def boot(diffs,n=10000):
    diffs=np.array(diffs); idx=rng.integers(0,len(diffs),(n,len(diffs)))
    means=diffs[idx].mean(1); return np.percentile(means,2.5),np.percentile(means,97.5)
def paired(path,a="named",b="anon",keyf=lambda r:r["repo"]+r["gold"]):
    res=json.load(open(D/path))
    A={keyf(r):r["mean"] for r in res if r["cond"]==a and r["mean"] is not None}
    B={keyf(r):r["mean"] for r in res if r["cond"]==b and r["mean"] is not None}
    ks=[k for k in A if k in B]; d=[A[k]-B[k] for k in ks]
    return d,[A[k] for k in ks],[B[k] for k in ks]
def report(name,d,va,vb,la="named",lb="anon"):
    lo,hi=boot(d)
    try: w=wilcoxon(va,vb).pvalue
    except Exception: w=float('nan')
    print(f"{name:34} n={len(d):3} {la} {np.mean(va):.2f} / {lb} {np.mean(vb):.2f} | "
          f"Δ={np.mean(d):+.2f} [95% CI {lo:+.2f},{hi:+.2f}] Wilcoxon p={w:.2g}")

print("=== paired named vs anon ===")
for nm,fn in [("statement (LeanMarathon n=302)","lm_readback_statement_results.json"),
              ("method (LeanMarathon n=302)","lm_readback_method_results.json")]:
    d,va,vb=paired(fn); report(nm,d,va,vb)
d,va,vb=paired("lm_oseledets_results.json",keyf=lambda r:r["gold"]); report("statement (oseledets n=60)",d,va,vb)

print("\n=== validity / application (pre-paired per item) ===")
ng=json.load(open(D/"lm_negctrl_results.json"))
cw=[(r["correct"],r["wrong"]) for r in ng if r.get("correct") is not None and r.get("wrong") is not None]
report("negative control (method n=40)",[a-b for a,b in cw],[a for a,b in cw],[b for a,b in cw],"correct","wrong")
dr=json.load(open(D/"lm_drift_results.json"))
cc=[(r["clean"],r["corrupt"]) for r in dr if r.get("clean") is not None and r.get("corrupt") is not None]
report("drift detector (statement n=38)",[a-b for a,b in cc],[a for a,b in cc],[b for a,b in cc],"clean","corrupt")

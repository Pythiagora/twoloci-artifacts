# /// script
# requires-python = ">=3.11"
# dependencies = ["scipy>=1.11"]
# ///
# #3 PREDICTORS of name-dependence (no API). Per statement node: Δ = named_mean - anon_mean (from the
# full-run results), vs features: signature length, # maskable identifiers (anon F-count). Hypothesis:
# more maskable identifiers -> more name-carried (higher Δ). Turns the bimodality into a predictive claim.
import json, re, statistics as st
from scipy.stats import spearmanr, pearsonr
from lm_common import load, anon

res=json.load(open("lm_readback_statement_results.json"))
named={r["repo"]+r["gold"]:r["mean"] for r in res if r["cond"]=="named"}
anonm={r["repo"]+r["gold"]:r["mean"] for r in res if r["cond"]=="anon"}
nodes=load("statement")
rows=[]
for n in nodes:
    key=n["repo"]+(n["statement"] or "")[:120]
    if named.get(key) is None or anonm.get(key) is None: continue
    delta=named[key]-anonm[key]
    nmask=len(set(re.findall(r'\bF\d+', anon(n["lean_sig"]))))
    rows.append({"delta":delta,"nmask":nmask,"siglen":len(n["lean_sig"]),"anon":anonm[key]})
print(f"matched {len(rows)} nodes")
D=[r["delta"] for r in rows]; NM=[r["nmask"] for r in rows]; SL=[r["siglen"] for r in rows]
def rep(x,name,y="Δ(named-anon)"):
    rs,ps=spearmanr(x,D); rp,pp=pearsonr(x,D)
    print(f"{name:>26} vs {y}: Spearman ρ={rs:+.3f} (p={ps:.2g}) | Pearson r={rp:+.3f}")
rep(NM,"# maskable identifiers"); rep(SL,"signature length")
# split: low vs high maskable-identifier count
NM_med=st.median(NM)
lo=[r["delta"] for r in rows if r["nmask"]<=NM_med]; hi=[r["delta"] for r in rows if r["nmask"]>NM_med]
print(f"\nΔ by maskable-identifier count: low(≤{NM_med:.0f}) mean={st.mean(lo):+.2f}  | high(>{NM_med:.0f}) mean={st.mean(hi):+.2f}")
print(f"anon-recovery: low-mask mean={st.mean([r['anon'] for r in rows if r['nmask']<=NM_med]):.2f} | "
      f"high-mask mean={st.mean([r['anon'] for r in rows if r['nmask']>NM_med]):.2f}")

# /// script
# requires-python = ">=3.11"
# dependencies = ["scipy>=1.11"]
# ///
# Quantify DeepSeek <-> Opus judge agreement on the confusion structure (the §4.4 claim).
# DeepSeek matrices: loaded from saved raw K=5 judge scores (cell means).
# Opus matrices: the in-session Opus judging, transcribed here and saved to JSON for the record.
# We correlate the OFF-DIAGONAL cells (the confusion structure; diagonals are ~10 for both and
# would trivially inflate any all-cell correlation).
import json, os, statistics as st
from scipy.stats import spearmanr, pearsonr

EXCH = os.path.expanduser("~/Code/AITP/exch_experiment")
MP = os.path.expanduser("~/Code/AITP/multiproof_experiment")

def means_from_raw(path, meths):
    raw = json.load(open(path))
    return {(i, j): (st.mean(raw[f"{i}__{j}"]) if raw.get(f"{i}__{j}") else 0.0)
            for i in meths for j in meths}

# ---- de Finetti (full anonymized development) ----
dF = ["Martingale", "L2", "Koopman"]
ds_dF = means_from_raw(f"{EXCH}/exch_full_judge_raw.json", dF)
# Opus in-session judging of the SAME saved informalizations (rows=reader, cols=gold):
opus_dF = {
    ("Martingale","Martingale"):10,("Martingale","L2"):0,("Martingale","Koopman"):0,
    ("L2","Martingale"):2,("L2","L2"):10,("L2","Koopman"):3,
    ("Koopman","Martingale"):1,("Koopman","L2"):4,("Koopman","Koopman"):9,
}

# ---- primes (anon) ----
pr = ["Euclid","Euler","Goldbach","Saidak","Wunderlich"]
ds_pr = means_from_raw(f"{MP}/mp_InfinitudeOfPrimes_anon_judge_raw.json", pr)
opus_pr = {
    ("Euclid","Euclid"):10,("Euclid","Euler"):0,("Euclid","Goldbach"):0,("Euclid","Saidak"):1,("Euclid","Wunderlich"):0,
    ("Euler","Euclid"):0,("Euler","Euler"):10,("Euler","Goldbach"):0,("Euler","Saidak"):0,("Euler","Wunderlich"):0,
    ("Goldbach","Euclid"):2,("Goldbach","Euler"):0,("Goldbach","Goldbach"):10,("Goldbach","Saidak"):6,("Goldbach","Wunderlich"):5,
    ("Saidak","Euclid"):3,("Saidak","Euler"):0,("Saidak","Goldbach"):5,("Saidak","Saidak"):10,("Saidak","Wunderlich"):4,
    ("Wunderlich","Euclid"):1,("Wunderlich","Euler"):0,("Wunderlich","Goldbach"):6,("Wunderlich","Saidak"):6,("Wunderlich","Wunderlich"):10,
}

def offdiag(meths, m):
    return [m[(i,j)] for i in meths for j in meths if i != j]

def report(name, meths, ds, opus):
    do, oo = offdiag(meths, ds), offdiag(meths, opus)
    rs, ps = spearmanr(do, oo); rp, pp = pearsonr(do, oo)
    print(f"\n[{name}] off-diagonal cells n={len(do)}")
    print(f"  DeepSeek diag={st.mean([ds[(x,x)] for x in meths]):.2f} off={st.mean(do):.2f} margin={st.mean([ds[(x,x)] for x in meths])-st.mean(do):.2f}")
    print(f"  Opus     diag={st.mean([opus[(x,x)] for x in meths]):.2f} off={st.mean(oo):.2f} margin={st.mean([opus[(x,x)] for x in meths])-st.mean(oo):.2f}")
    print(f"  Spearman ρ={rs:.3f} (p={ps:.3g}) | Pearson r={rp:.3f} (p={pp:.3g})")
    return do, oo

dDo, dOo = report("de Finetti full", dF, ds_dF, opus_dF)
pDo, pOo = report("primes anon", pr, ds_pr, opus_pr)

# pooled across both theorems
allds, allopus = dDo + pDo, dOo + pOo
rs, ps = spearmanr(allds, allopus); rp, pp = pearsonr(allds, allopus)
print(f"\n[POOLED off-diagonal] n={len(allds)}  Spearman ρ={rs:.3f} (p={ps:.3g}) | Pearson r={rp:.3f} (p={pp:.3g})")

# save Opus matrices for the record
json.dump({f"{i}__{j}": opus_dF[(i,j)] for i in dF for j in dF},
          open(f"{EXCH}/exch_full_opus_matrix.json","w"), indent=1)
json.dump({f"{i}__{j}": opus_pr[(i,j)] for i in pr for j in pr},
          open(f"{MP}/mp_InfinitudeOfPrimes_anon_opus_matrix.json","w"), indent=1)
print("\nsaved Opus matrices -> exch_full_opus_matrix.json, mp_InfinitudeOfPrimes_anon_opus_matrix.json")

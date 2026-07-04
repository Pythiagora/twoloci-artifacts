# /// script
# requires-python = ">=3.11"
# ///
# Prepare per-theorem discrimination forms from seewoo5/DifferentProofs.
# Usage: uv run mp_prep.py <TheoremDirName>   e.g. FermatLittleTheorem
# Output: mp_<THM>.json (raw, with names) + mp_<THM>_anon.json (anonymized).
# Each entry: {method, gold (blueprint prose), script (intra-repo import closure), stmt, nmask}
import re, json, os, sys

REPO = os.path.expanduser("~/Code/AITP/MATHAI/external/DifferentProofs")
THM = sys.argv[1]
PDIR = f"{REPO}/DifferentProofs/{THM}"
BP = f"{REPO}/DifferentProofsBlueprint/Chapters/{THM}.lean"
EXCLUDE = {"Defs", "Basic"}   # shared statement + helpers, not methods

def read(f): return open(f).read()

def closure(stem, seen):
    f = f"{PDIR}/{stem}.lean"
    if stem in seen or not os.path.exists(f): return []
    seen.add(stem)
    src = read(f)
    files = []
    for d in re.findall(rf"import DifferentProofs\.{THM}\.(\w+)", src):
        files += closure(d, seen)
    files.append((stem, src))
    return files

def strip_boiler(src):
    keep = []
    for l in src.split("\n"):
        s = l.strip()
        if s == "module" or s.startswith(("public import", "import ", "@[expose]")):
            continue
        keep.append(l)
    src = "\n".join(keep)
    src = re.sub(r"/-.*?-/", "", src, flags=re.DOTALL)
    src = "\n".join(l for l in src.split("\n") if not l.strip().startswith("--"))
    return re.sub(r"\n{3,}", "\n\n", src).strip()

# ---- golds + statement from the Verso blueprint chapter ----
bp = read(BP)
idname = dict(re.findall(r':::(?:theorem|lemma_|definition)\s+"([^"]+)"[^\n]*\(lean\s*:=\s*"([^"]+)"\)', bp, flags=re.DOTALL))
proofs = {m.group(1): m.group(2) for m in re.finditer(r':::proof\s+"([^"]+)"\s*(.*?):::', bp, flags=re.DOTALL)}
def clean(p):
    p = re.sub(r'\{uses\s+"[^"]+"\}\[\]', "", p)
    p = p.replace("$`", "").replace("`", "").replace("\\pmod", "mod").replace("\\", "")
    return re.sub(r"\s+", " ", p).strip()
def gold_for(stem):
    cand = [(bid, name) for bid, name in idname.items()
            if name.lower().endswith(stem.lower()) and bid in proofs and ("theorem" in re.search(rf':::(\w+)\s+"{re.escape(bid)}"', bp).group(1))]
    if cand:
        return clean(proofs[cand[0][0]])
    # fallback: any block whose name endswith stem
    for bid, name in idname.items():
        if name.lower().endswith(stem.lower()) and bid in proofs:
            return clean(proofs[bid])
    return None
mdef = re.search(rf':::definition\s+"[^"]+"[^\n]*\(lean\s*:=\s*"{THM}"\)\s*(.*?):::', bp, flags=re.DOTALL)
stmt = clean(mdef.group(1)) if mdef else THM

# ---- anonymization (mask method-revealing identifiers; keep Lean syntax/tactics + generic types) ----
KEEP = set("""theorem lemma def example variable variables open namespace section end by have let show fun match with at using from in do return if then else where mutual
exact apply refine intro intros rintro obtain rcases cases constructor induction rcases use exists existsi refine' specialize
simp simp_all simp_rw rw rewrite calc ring ring_nf linarith nlinarith norm_num norm_cast omega positivity gcongr aesop tauto decide
field_simp convert congr ext funext subst this trivial rfl sorry set push_cast exact_mod_cast filter_upwards by_contra contrapose
And Or Iff Exists Not True False Type Prop Sort Nonempty noncomputable instance abbrev structure inductive class scoped Classical Fact
Nat Int Rat Real Complex Finset Set ZMod Polynomial zero succ one two pow mul add sub div mod""".split())
def keepf(t):
    if t in KEEP: return True
    if len(t) <= 2: return True
    if re.fullmatch(r"h[A-Za-z0-9_]{0,3}", t): return True
    if re.fullmatch(r"[0-9].*", t): return True
    return False
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*'?")
def anonymize(src):
    rmap = {}; cnt = [0]
    def rep(mt):
        t = mt.group(0); head = t.split(".")[0]
        if keepf(t) or keepf(head): return t
        if t not in rmap: cnt[0] += 1; rmap[t] = f"F{cnt[0]}"
        return rmap[t]
    return IDENT.sub(rep, src), cnt[0]

methods = sorted(s[:-5] for s in os.listdir(PDIR) if s.endswith(".lean") and s[:-5] not in EXCLUDE)
raw, anon = [], []
for stem in methods:
    src = "\n\n".join(strip_boiler(s) for _, s in closure(stem, set()))
    gold = gold_for(stem)
    raw.append({"method": stem, "gold": gold, "script": src, "stmt": stmt})
    a, n = anonymize(src)
    anon.append({"method": stem, "gold": gold, "script": a, "stmt": stmt, "nmask": n})
json.dump(raw,  open(f"mp_{THM}.json", "w"), ensure_ascii=False, indent=1)
json.dump(anon, open(f"mp_{THM}_anon.json", "w"), ensure_ascii=False, indent=1)
print(f"STMT: {stmt[:100]}")
for r, a in zip(raw, anon):
    print(f"{r['method']:>16}: {len(r['script']):>6}c raw / {len(a['script']):>6}c anon ({a['nmask']} masqués) | gold={'OK('+str(len(r['gold']))+'c)' if r['gold'] else 'MISSING'}")

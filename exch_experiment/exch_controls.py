# /// script
# requires-python = ">=3.11"
# ///
# de Finetti control battery (aggr / sig / locus) on the FULL developments, to repeat on the
# UNCANONICAL anchor what mp_controls/mp_locus did on DifferentProofs — esp. SIG: if removing
# proof bodies collapses discrimination on a non-famous theorem, it's not priors.
# Reproduces anon_full's file gathering (Theorem{ViaM} + ViaX/**), then aggr/sig/locus + DeepSeek golds.
import re, json, glob, os, sys

REPO = os.path.expanduser("~/Code/AITP/MATHAI/external/exchangeability")
BASE = f"{REPO}/Exchangeability/DeFinetti"
golds = {o["method"]: o["gold"] for o in json.load(open("exch_forms.json"))}
DIRS = {"Martingale": "ViaMartingale", "L2": "ViaL2", "Koopman": "ViaKoopman"}

def raw_fulldev(m, d):
    files = [f"{BASE}/Theorem Via{m}.lean".replace(" ", "")] + sorted(glob.glob(f"{BASE}/{d}/**/*.lean", recursive=True))
    src = "\n".join(open(f).read() for f in files if os.path.exists(f))
    src = re.sub(r"/-.*?-/", "", src, flags=re.DOTALL)
    src = "\n".join(l for l in src.split("\n")
                    if not l.strip().startswith(("--", "module", "import", "public import", "@[expose]")))
    src = re.sub(r"via(Martingale|L2|Koopman)", "ViaX", src)
    return re.sub(r"\n{3,}", "\n\n", src).strip()

KEEP = set("""theorem lemma def example variable variables open namespace section end by have let show fun match with at using from in do return if then else where mutual
exact apply refine intro intros rintro obtain rcases cases constructor induction use exists refine specialize calc
simp simp_all simp_rw rw rewrite ring ring_nf linarith nlinarith lia norm_num norm_cast omega positivity gcongr aesop tauto decide
field_simp convert congr ext funext subst this trivial rfl sorry set push_cast exact_mod_cast by_contra contrapose wlog unfold filter_upwards
fun forall exists And Or Iff Not True False Type Prop Sort HIDDEN""".split())
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*'?")
def aggr(src):
    rmap = {}; c = [0]
    def rep(mt):
        t = mt.group(0); h = t.split(".")[0]
        if t in KEEP or h in KEEP: return t
        if t not in rmap: c[0] += 1; rmap[t] = f"F{c[0]}"
        return rmap[t]
    return IDENT.sub(rep, src)

def chunks(src):
    return re.split(r"(?m)(?=^(?:noncomputable\s+def|theorem|lemma|def|example|instance)\b)", src)

def strip_bodies(src):  # signatures only
    out = []
    for p in chunks(src):
        h = re.match(r"^\s*(noncomputable\s+def|theorem|lemma|def|example|instance)\b", p)
        if h and not h.group(1).endswith("def"):
            m = re.search(r":=", p)
            out.append((p[:m.start()].rstrip() + " := by sorry\n") if m else p)
        else:
            out.append(p)
    return "\n".join(out)

def locus(src):  # opacify stated objects (def bodies + all lemma/theorem TYPES), keep tactic bodies
    out = []
    for p in chunks(src):
        h = re.match(r"^\s*(noncomputable\s+def|theorem|lemma|def|example|instance)\b", p)
        if not h: out.append(p); continue
        if h.group(1).endswith("def"):
            m = re.search(r":=", p)
            if m: out.append(p[:m.start()].rstrip() + " := HIDDEN\n")
            else:
                mm = re.search(r"\n\s*\|", p); out.append((p[:mm.start()] if mm else p).rstrip() + " := HIDDEN\n")
        else:
            mt = re.search(r":\s*(.*?):=", p, re.DOTALL)
            nm = re.match(r"^\s*(?:theorem|lemma|example)\s+(\S+)", p)
            if mt and nm: out.append(f"{h.group(1)} {nm.group(1)} : HIDDEN {p[mt.end()-2:]}")
            else: out.append(p)
    return "\n".join(out)

conds = {"aggr": lambda s: aggr(s), "sig": lambda s: aggr(strip_bodies(s)), "locus": lambda s: aggr(locus(s))}
raws = {m: raw_fulldev(m, d) for m, d in DIRS.items()}
for cond, fn in conds.items():
    out = [{"method": m, "gold": golds[m], "script": fn(raws[m])} for m in DIRS]
    json.dump(out, open(f"exch_{cond}.json", "w"), ensure_ascii=False, indent=1)
    print(f"{cond:>6}: " + " | ".join(f"{o['method']} {len(o['script'])}c" for o in out))

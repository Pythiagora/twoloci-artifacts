# /// script
# requires-python = ">=3.11"
# ///
# Falsification controls for the discrimination result. From raw mp_<THM>.json produce:
#   mp_<THM>_aggr.json : AGGRESSIVE anonymization — mask EVERYTHING except pure Lean
#                        syntax/tactic keywords (drops the ZMod/Nat/Real/Polynomial leak;
#                        even single-letter locals masked, consistently). Tests "kept names leaked".
#   mp_<THM>_sig.json  : SIGNATURE-ONLY — proof bodies (`:= by ...`) replaced by `:= by sorry`,
#                        then aggressively anonymized. Tests "is it the proof BODY or just priors?".
# Usage: uv run mp_controls.py <THM>
import re, json, sys

THM = sys.argv[1]
raw = json.load(open(f"mp_{THM}.json"))

# minimal whitelist: ONLY structural/tactic tokens. No types, no lemma names, no numbers-as-names.
KEEP = set("""theorem lemma def example variable variables open namespace section end by have let show fun match with at using from in do return if then else where mutual
exact apply refine intro intros rintro obtain rcases cases constructor induction use exists refine specialize calc
simp simp_all simp_rw rw rewrite ring ring_nf linarith nlinarith norm_num norm_cast omega positivity gcongr aesop tauto decide
field_simp convert congr ext funext subst this trivial rfl sorry set push_cast exact_mod_cast by_contra contrapose
fun forall exists And Or Iff Not True False Type Prop Sort""".split())

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*'?")
def aggr(src):
    rmap = {}; cnt = [0]
    def rep(mt):
        t = mt.group(0); head = t.split(".")[0]
        if t in KEEP or head in KEEP: return t
        if t not in rmap: cnt[0] += 1; rmap[t] = f"F{cnt[0]}"
        return rmap[t]
    return IDENT.sub(rep, src), cnt[0]

def strip_bodies(src):
    # replace each "... := by <body>" up to the next top-level decl with ":= by sorry"
    # split into declaration chunks on top-level keywords
    parts = re.split(r"(?m)(?=^(?:theorem|lemma|def|example|instance)\b)", src)
    out = []
    for p in parts:
        # cut the proof term/tactic body: first ":=" (handles ":= by" and ":= term")
        m = re.search(r":=", p)
        if m and re.match(r"(?s)^\s*(theorem|lemma|example|instance)\b", p):
            out.append(p[:m.start()].rstrip() + " := by sorry\n")
        else:
            out.append(p)  # defs/notation kept (they ARE signatures/structure)
    return "\n".join(out)

aggr_out, sig_out = [], []
for o in raw:
    a, na = aggr(o["script"])
    aggr_out.append({**o, "script": a, "nmask": na})
    s, ns = aggr(strip_bodies(o["script"]))
    sig_out.append({**o, "script": s, "nmask": ns})
json.dump(aggr_out, open(f"mp_{THM}_aggr.json", "w"), ensure_ascii=False, indent=1)
json.dump(sig_out, open(f"mp_{THM}_sig.json", "w"), ensure_ascii=False, indent=1)
for o, a, s in zip(raw, aggr_out, sig_out):
    print(f"{o['method']:>14}: raw {len(o['script']):>6}c -> aggr {len(a['script']):>6}c / sig {len(s['script']):>5}c")

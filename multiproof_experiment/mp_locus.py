# /// script
# requires-python = ">=3.11"
# ///
# LOCUS-(a) isolation: hide the STATED mathematical objects (def bodies + auxiliary lemma
# TYPES) so the method can only be read from the TACTIC structure of the main proof.
# Keeps: the main theorem's full statement+body, and every tactic proof body; opacifies the
# *content* of definitions and the *claims* of helper lemmas (-> HIDDEN), then aggressive-masks.
# Tests whether tactic structure alone carries the method (vs the stated objects).
# Usage: uv run mp_locus.py <THM> <prop1> [prop2...]
import re, json, sys

THM = sys.argv[1]
PROPS = sys.argv[2:] or [THM]
raw = json.load(open(f"mp_{THM}.json"))

KEEP = set("""theorem lemma def example variable variables open namespace section end by have let show fun match with at using from in do return if then else where mutual
exact apply refine intro intros rintro obtain rcases cases constructor induction use exists refine specialize calc
simp simp_all simp_rw rw rewrite ring ring_nf linarith nlinarith lia norm_num norm_cast omega positivity gcongr aesop tauto decide
field_simp convert congr ext funext subst this trivial rfl sorry set push_cast exact_mod_cast by_contra contrapose wlog unfold
fun forall exists And Or Iff Not True False Type Prop Sort HIDDEN""".split())
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*'?")
def aggr(src):
    rmap = {}; cnt = [0]
    def rep(mt):
        t = mt.group(0); head = t.split(".")[0]
        if t in KEEP or head in KEEP: return t
        if t not in rmap: cnt[0] += 1; rmap[t] = f"F{cnt[0]}"
        return rmap[t]
    return IDENT.sub(rep, src), cnt[0]

def opacify(src):
    parts = re.split(r"(?m)(?=^(?:noncomputable\s+def|theorem|lemma|def|example|instance)\b)", src)
    out = []
    for p in parts:
        h = re.match(r"^\s*(noncomputable\s+def|theorem|lemma|def|example|instance)\b", p)
        if not h:
            out.append(p); continue
        kind = h.group(1)
        if kind.endswith("def"):
            m = re.search(r":=", p)
            if m:
                out.append(p[:m.start()].rstrip() + " := HIDDEN\n")
            else:  # pattern-matching def: drop the match arms
                mm = re.search(r"\n\s*\|", p)
                out.append((p[:mm.start()] if mm else p).rstrip() + " := HIDDEN\n")
        else:
            mt = re.search(r":\s*(.*?):=", p, re.DOTALL)          # type between top ':' and ':='
            typ = mt.group(1).strip() if mt else ""
            is_main = any(re.search(rf"(^|[^A-Za-z0-9_]){re.escape(pn)}([^A-Za-z0-9_]|$)", typ) for pn in PROPS) and len(typ.split()) <= 3
            name_m = re.match(r"^\s*(?:theorem|lemma|example)\s+(\S+)", p)
            if is_main or not mt or not name_m:
                out.append(p)                                      # keep main (statement+body) / unparseable
            else:
                out.append(f"{kind} {name_m.group(1)} : HIDDEN {p[mt.end()-2:]}")  # hide claim, keep proof
    return "\n".join(out)

locus = []
for o in raw:
    op = opacify(o["script"])
    a, n = aggr(op)
    locus.append({**o, "script": a, "nmask": n})
json.dump(locus, open(f"mp_{THM}_locus.json", "w"), ensure_ascii=False, indent=1)
for o, l in zip(raw, locus):
    nh = l["script"].count("HIDDEN")
    print(f"{o['method']:>14}: raw {len(o['script']):>6}c -> locus {len(l['script']):>6}c  ({nh} HIDDEN)")

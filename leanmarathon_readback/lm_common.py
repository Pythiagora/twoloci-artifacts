import re
from pathlib import Path
EXT = Path.home()/"Code/AITP/MATHAI/external"
REPOS = ["ErdosGraham", "Erdos1196", "Prim"]

def parse_nodes(repo):
    f = EXT/repo/"LeanMarathon"/"Main.lean"
    if not f.exists(): return []
    txt = f.read_text(); out = []
    for b in re.split(r"(?=@\[blueprint)", txt):
        if not b.startswith("@[blueprint"): continue
        env = (re.search(r'latexEnv\s*:=\s*"([^"]+)"', b) or [None,None])[1]
        ms = re.search(r'statement\s*:=\s*/--(.*?)-/', b, re.DOTALL)
        mp = re.search(r'proof\s*:=\s*/--(.*?)-/', b, re.DOTALL)
        md = re.search(r'(?m)^(?:local\s+)?(theorem|lemma|def|abbrev|structure|inductive|class|instance)\b', b)
        if not md: continue
        lean = b[md.start():].strip(); parts = re.split(r':=', lean, 1)
        out.append({"repo": repo, "env": env,
                    "statement": ms.group(1).strip() if ms else None,
                    "latex_proof": mp.group(1).strip() if mp else None,
                    "lean_sig": parts[0].strip(),
                    "lean_proof": parts[1].strip() if len(parts) > 1 else ""})
    return out

KEEP = set("""theorem lemma def abbrev structure inductive class instance local section end variable
forall exists fun Prop Type Sort Nat Int Rat Real Complex Filter Set Finset atTop nhds And Or Not Iff True False
by intro exact apply refine rw simp ring linarith nlinarith omega norm_num positivity gcongr calc have obtain
rcases cases constructor induction exact_mod_cast push_cast field_simp use""".split())
_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*'?")
def anon(src):
    rmap={}; c=[0]
    def rep(m):
        t=m.group(0); h=t.split(".")[0]
        if t in KEEP or h in KEEP or len(t)<=2: return t
        if t not in rmap: c[0]+=1; rmap[t]=f"F{c[0]}"
        return rmap[t]
    return _ID.sub(rep, src)

def anon_strict(src):
    # stricter than anon: strip /- -/ and -- comments, mask numeric literals, then mask identifiers.
    s=re.sub(r"/-.*?-/","",src,flags=re.DOTALL)
    s="\n".join(l.split("--")[0] if "--" in l else l for l in s.split("\n"))
    s=re.sub(r"\b\d+(?:\.\d+)?\b","N",s)
    return anon(s)

def rsample(items, n, seed=0):
    import random
    if n>=len(items): return items
    r=random.Random(seed); idx=sorted(r.sample(range(len(items)), n)); return [items[i] for i in idx]

def load(mode):
    nodes=[n for r in REPOS for n in parse_nodes(r)]
    if mode=="method":
        return [n for n in nodes if n["env"] in ("lemma","theorem") and n["latex_proof"] and len(n["lean_proof"])>25]
    return [n for n in nodes if n["env"] in ("lemma","theorem") and n["statement"] and len(n["lean_sig"])>15]

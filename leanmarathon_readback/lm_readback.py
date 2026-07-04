# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
# Readback probe on LeanMarathon blueprints (Erdős). Built-in gold: each @[blueprint] node pairs a
# Lean declaration with a LaTeX `statement` (+ often `proof`).
#   statement mode: anon Lean TYPE -> informal claim, judged vs gold LaTeX statement
#   method mode:    anon Lean PROOF -> informal method, judged vs gold LaTeX proof
#   conditions: named (raw) vs anon (identifiers masked) -> structure-carried vs name-carried readback
# Reader + judge = DeepSeek-V4-Pro. Usage:
#   uv run lm_readback.py dry
#   uv run lm_readback.py run statement [N]
#   uv run lm_readback.py run method [N]
import re, os, sys, json, asyncio, statistics as st
from pathlib import Path

EXT = Path.home()/"Code/AITP/MATHAI/external"
REPOS = ["ErdosGraham", "Erdos1196", "Prim"]

def parse_nodes(repo):
    f = EXT/repo/"LeanMarathon"/"Main.lean"
    if not f.exists(): return []
    txt = f.read_text()
    out = []
    for b in re.split(r"(?=@\[blueprint)", txt):
        if not b.startswith("@[blueprint"): continue
        env = (re.search(r'latexEnv\s*:=\s*"([^"]+)"', b) or [None,None])[1]
        ms = re.search(r'statement\s*:=\s*/--(.*?)-/', b, re.DOTALL)
        mp = re.search(r'proof\s*:=\s*/--(.*?)-/', b, re.DOTALL)
        md = re.search(r'(?m)^(?:local\s+)?(theorem|lemma|def|abbrev|structure|inductive|class|instance)\b', b)
        if not md: continue
        lean = b[md.start():].strip()
        parts = re.split(r':=', lean, 1)
        sig = parts[0].strip()
        proof = parts[1].strip() if len(parts) > 1 else ""
        out.append({"repo": repo, "env": env,
                    "statement": ms.group(1).strip() if ms else None,
                    "latex_proof": mp.group(1).strip() if mp else None,
                    "lean_sig": sig, "lean_proof": proof})
    return out

KEEP = set("""theorem lemma def abbrev structure inductive class instance local section end variable
forall exists fun Prop Type Sort Nat Int Rat Real Complex Filter Set Finset atTop nhds And Or Not Iff True False
by intro exact apply refine rw simp simdp ring linarith nlinarith omega norm_num positivity gcongr calc have obtain
rcases cases constructor induction exact_mod_cast push_cast field_simp use""".split())
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*'?")
def anon(src):
    rmap={}; c=[0]
    def rep(m):
        t=m.group(0); h=t.split(".")[0]
        if t in KEEP or h in KEEP or len(t)<=2: return t
        if t not in rmap: c[0]+=1; rmap[t]=f"F{c[0]}"
        return rmap[t]
    return IDENT.sub(rep, src)

def load(mode):
    nodes=[n for r in REPOS for n in parse_nodes(r)]
    if mode=="method":
        keep=[n for n in nodes if n["env"] in ("lemma","theorem") and n["latex_proof"] and len(n["lean_proof"])>25]
    else:
        keep=[n for n in nodes if n["env"] in ("lemma","theorem") and n["statement"] and len(n["lean_sig"])>15]
    return nodes, keep

if sys.argv[1:] and sys.argv[1]=="dry":
    for mode in ("statement","method"):
        _,k=load(mode); print(f"{mode}: {len(k)} nodes")
    sys.exit(0)

import httpx
KEY=os.environ["DEEPSEEK_API_KEY"]; URL="https://api.deepseek.com/chat/completions"; M="deepseek-v4-pro"
MODE=sys.argv[2] if len(sys.argv)>2 else "statement"
_,keep=load(MODE); keep.sort(key=lambda n:(n["repo"], n["statement"] or n["lean_sig"]))
N=int(sys.argv[3]) if len(sys.argv)>3 else len(keep)
sample=keep if N>=len(keep) else [keep[i] for i in range(0,len(keep),max(1,len(keep)//N))][:N]
K=int(os.environ.get("K","2")); SEM=asyncio.Semaphore(int(os.environ.get("CONC","24")))

PROMPTS={
 "statement":(("Voici la SIGNATURE d'un énoncé formel Lean 4. Énonce en clair, en 1–2 phrases, CE QUE "
               "cet énoncé affirme mathématiquement, sans paraphraser la syntaxe.\n\n```lean\n{s}\n```"),
              ("Énoncé informel du lecteur :\n«{cand}»\n\nÉnoncé de RÉFÉRENCE :\n«{ref}»\n\nLe lecteur a-t-il "
               "récupéré LE MÊME contenu mathématique ? 0=différent/faux, 10=même claim. JSON: {{\"score\":<0-10>}}")),
 "method":(("Voici une PREUVE formelle Lean 4 (anonymisée possible). Décris en clair, en 2–4 phrases, la "
            "MÉTHODE / l'idée de preuve employée, sans paraphraser le code.\n\n```lean\n{s}\n```"),
           ("Méthode de preuve décrite par le lecteur :\n«{cand}»\n\nPreuve de RÉFÉRENCE :\n«{ref}»\n\nLe lecteur "
            "a-t-il récupéré LA MÊME méthode ? 0=technique différente, 10=même méthode. JSON: {{\"score\":<0-10>}}")),
}
RP,JP=PROMPTS[MODE]
def parse(t):
    for x in re.findall(r'\{[^{}]*score[^{}]*\}',t):
        try: return int(round(float(json.loads(x)["score"])))
        except: pass
    return None

async def call(c,msgs,mt,temp):
    async with SEM:
        for _ in range(4):
            try:
                r=await asyncio.wait_for(c.post(URL,headers={"Authorization":f"Bearer {KEY}"},
                    json={"model":M,"messages":msgs,"max_tokens":mt,"temperature":temp}),900)
                if r.status_code==200: return r.json()["choices"][0]["message"].get("content") or ""
            except Exception: await asyncio.sleep(5)
        return ""

async def main():
    field = "lean_sig" if MODE=="statement" else "lean_proof"
    gold  = "statement" if MODE=="statement" else "latex_proof"
    async with httpx.AsyncClient(timeout=httpx.Timeout(900.0)) as c:
        async def one(n,cond):
            src = n[field] if cond=="named" else anon(n[field])
            inf = await call(c,[{"role":"user","content":RP.format(s=src)}],4000,0.2)
            sc = await asyncio.gather(*[call(c,[{"role":"user","content":JP.format(cand=inf,ref=n[gold])}],4000,0.7) for _ in range(K)])
            scores=[x for x in (parse(t) for t in sc) if x is not None]
            return {"repo":n["repo"],"cond":cond,"mean":(st.mean(scores) if scores else None),"gold":(n[gold] or "")[:120]}
        res=await asyncio.gather(*[one(n,cond) for n in sample for cond in ("named","anon")])
    json.dump(res, open(f"lm_readback_{MODE}_results.json","w"), ensure_ascii=False, indent=1)
    print(f"### MODE={MODE}  n={len(sample)} nodes  K={K}")
    for cond in ("named","anon"):
        ms=[r["mean"] for r in res if r["cond"]==cond and r["mean"] is not None]
        print(f"{cond:>6}: n={len(ms)} mean={st.mean(ms):.2f} (sd {st.pstdev(ms):.2f})")
    nd={r["repo"]+r["gold"]:r["mean"] for r in res if r["cond"]=="named"}
    ad={r["repo"]+r["gold"]:r["mean"] for r in res if r["cond"]=="anon"}
    deltas=[nd[k]-ad[k] for k in nd if nd.get(k) is not None and ad.get(k) is not None]
    print(f"Δ(named-anon) mean={st.mean(deltas):+.2f} | struct(Δ≤0)={sum(1 for d in deltas if d<=0)} "
          f"mild(0<Δ≤2)={sum(1 for d in deltas if 0<d<=2)} name-dep(Δ>2)={sum(1 for d in deltas if d>2)} of {len(deltas)}")

asyncio.run(main())

# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
# #5 method-readback ABLATION at scale (the two-loci battery on the proof stratum, n>>17).
# Conditions on the Lean PROOF given to the reader, judged vs gold LaTeX proof:
#   named : raw proof
#   anon  : custom identifiers masked (types/tactics kept)            [= structure + embedded math]
#   aggr  : identifiers AND types masked (only Lean syntax/tactics)   [does type-vocab leak?]
#   skel  : aggr + lemma-argument lists [..] blanked                  [pure tactic control-flow]
# Recovery surviving 'skel' => method is in the control-flow; collapsing => it needs embedded terms.
# Usage: uv run lm_method_ablation.py [N]
import os, sys, json, re, asyncio, statistics as st
import httpx
from lm_common import load, anon
KEY=os.environ["DEEPSEEK_API_KEY"]; URL="https://api.deepseek.com/chat/completions"; M="deepseek-v4-pro"
N=int(sys.argv[1]) if len(sys.argv)>1 else 80; K=2; SEM=asyncio.Semaphore(24)

KEEP_AGGR=set("""theorem lemma by intro intros rintro exact apply refine rw rewrite simp simp_all ring ring_nf
linarith nlinarith omega norm_num norm_cast positivity gcongr calc have obtain rcases cases constructor induction
exact_mod_cast push_cast field_simp use refine' specialize subst convert congr ext funext fun forall exists""".split())
_ID=re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*'?")
def aggr(src):
    rmap={}; c=[0]
    def rep(m):
        t=m.group(0); h=t.split(".")[0]
        if t in KEEP_AGGR or h in KEEP_AGGR: return t
        if t not in rmap: c[0]+=1; rmap[t]=f"F{c[0]}"
        return rmap[t]
    return _ID.sub(rep,src)
def skel(src): return re.sub(r"\[[^\]]*\]","[..]", aggr(src))
TRANSFORM={"named":lambda s:s,"anon":anon,"aggr":aggr,"skel":skel}

keep=load("method"); keep.sort(key=lambda n:(n["repo"], n["latex_proof"] or ""))
sample=keep if N>=len(keep) else [keep[i] for i in range(0,len(keep),max(1,len(keep)//N))][:N]
RP=("Voici une PREUVE formelle Lean 4. Décris en clair, 2–4 phrases, la MÉTHODE / l'idée de preuve "
    "employée, sans paraphraser le code.\n\n```lean\n{s}\n```")
JP=("Méthode décrite par le lecteur :\n«{cand}»\n\nPreuve de RÉFÉRENCE :\n«{ref}»\n\nMÊME méthode ? "
    "0=technique différente, 10=même méthode. JSON: {{\"score\":<0-10>}}")
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
    async with httpx.AsyncClient(timeout=httpx.Timeout(900.0)) as c:
        async def one(n,cond):
            inf=await call(c,[{"role":"user","content":RP.format(s=TRANSFORM[cond](n["lean_proof"]))}],4000,0.2)
            sc=await asyncio.gather(*[call(c,[{"role":"user","content":JP.format(cand=inf,ref=n["latex_proof"])}],4000,0.7) for _ in range(K)])
            v=[x for x in (parse(t) for t in sc) if x is not None]
            return {"cond":cond,"mean":(st.mean(v) if v else None)}
        res=await asyncio.gather(*[one(n,cond) for n in sample for cond in TRANSFORM])
    json.dump(res,open("lm_method_ablation_results.json","w"),indent=1)
    print(f"### METHOD-READBACK ABLATION  n={len(sample)}  K={K}")
    for cond in TRANSFORM:
        ms=[r["mean"] for r in res if r["cond"]==cond and r["mean"] is not None]
        print(f"{cond:>6}: n={len(ms)} mean recovery={st.mean(ms):.2f} (sd {st.pstdev(ms):.2f})")
asyncio.run(main())

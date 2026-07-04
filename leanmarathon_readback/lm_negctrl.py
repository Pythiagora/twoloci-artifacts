# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
# #1 NEGATIVE CONTROL for method-readback. The 9.04 anon score could be judge leniency.
# Test: reader informalizes the ANON proof, then judge scores it against the CORRECT gold AND a
# WRONG gold (another node's proof). If correct >> wrong, the judge discriminates -> signal is real.
# If correct ~ wrong, it's leniency. Usage: uv run lm_negctrl.py [N]
import os, sys, json, asyncio, random, statistics as st
import httpx
from lm_common import load, anon, rsample
KEY=os.environ["DEEPSEEK_API_KEY"]; URL="https://api.deepseek.com/chat/completions"; M="deepseek-v4-pro"
N=int(sys.argv[1]) if len(sys.argv)>1 else 40; K=2; SEM=asyncio.Semaphore(24)
keep=load("method"); keep.sort(key=lambda n:(n["repo"], n["latex_proof"] or ""))
sample=rsample(keep, N, seed=7)
random.seed(0)
wrong=sample[:]; random.shuffle(wrong)
for i in range(len(sample)):                       # ensure wrong != correct
    if wrong[i]["latex_proof"]==sample[i]["latex_proof"]: wrong[i]=wrong[(i+1)%len(wrong)]

RP=("Voici une PREUVE formelle Lean 4 (anonymisée). Décris en clair, 2–4 phrases, la MÉTHODE / l'idée "
    "de preuve, sans paraphraser le code.\n\n```lean\n{s}\n```")
JP=("Méthode décrite par le lecteur :\n«{cand}»\n\nPreuve de RÉFÉRENCE :\n«{ref}»\n\nMÊME méthode ? "
    "0=technique différente, 10=même méthode. JSON: {{\"score\":<0-10>}}")
def parse(t):
    import re
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
        async def one(n,w):
            inf=await call(c,[{"role":"user","content":RP.format(s=anon(n["lean_proof"]))}],4000,0.2)
            cor=await asyncio.gather(*[call(c,[{"role":"user","content":JP.format(cand=inf,ref=n["latex_proof"])}],4000,0.7) for _ in range(K)])
            wro=await asyncio.gather(*[call(c,[{"role":"user","content":JP.format(cand=inf,ref=w["latex_proof"])}],4000,0.7) for _ in range(K)])
            cs=[x for x in (parse(t) for t in cor) if x is not None]; ws=[x for x in (parse(t) for t in wro) if x is not None]
            return {"correct":(st.mean(cs) if cs else None),"wrong":(st.mean(ws) if ws else None)}
        res=await asyncio.gather(*[one(sample[i],wrong[i]) for i in range(len(sample))])
    cor=[r["correct"] for r in res if r["correct"] is not None]
    wro=[r["wrong"] for r in res if r["wrong"] is not None]
    both=[(r["correct"],r["wrong"]) for r in res if r["correct"] is not None and r["wrong"] is not None]
    json.dump(res,open("lm_negctrl_results.json","w"),indent=1)
    print(f"### NEGATIVE CONTROL (method, anon)  n={len(both)}  K={K}")
    print(f"correct-gold mean = {st.mean(cor):.2f}")
    print(f"wrong-gold   mean = {st.mean(wro):.2f}")
    print(f"discrimination margin (correct-wrong) = {st.mean([a-b for a,b in both]):+.2f}")
    print(f"% nodes correct>wrong = {100*sum(1 for a,b in both if a>b)/len(both):.0f}%")
asyncio.run(main())

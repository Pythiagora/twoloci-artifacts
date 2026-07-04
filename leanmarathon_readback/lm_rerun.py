# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
# Council-fix re-runs on LeanMarathon: (a) RANDOM seeded sampling (not stride), (b) STRICT anonymization
# (strip comments + mask numerics, on top of identifier masking) → tests the leakage worry, (c) SIG on
# readback (method readback with the proof body removed → method should NOT be recoverable from the
# signature alone). Usage: uv run lm_rerun.py [N]
import os, sys, json, re, asyncio, statistics as st
import httpx
from lm_common import load, anon, anon_strict, rsample
KEY=os.environ["DEEPSEEK_API_KEY"]; URL="https://api.deepseek.com/chat/completions"; M="deepseek-v4-pro"
N=int(sys.argv[1]) if len(sys.argv)>1 else 150; K=2; SEM=asyncio.Semaphore(24)

meth=rsample(load("method"), N, seed=7)
stmt=rsample(load("statement"), N, seed=7)
RP_M=("Voici une PREUVE formelle Lean 4. Décris en clair, 2–4 phrases, la MÉTHODE / l'idée de preuve, "
      "sans paraphraser le code.\n\n```lean\n{s}\n```")
JP_M=("Méthode du lecteur :\n«{cand}»\n\nPreuve de RÉFÉRENCE :\n«{ref}»\n\nMÊME méthode ? 0=différente, "
      "10=même. JSON: {{\"score\":<0-10>}}")
RP_S=("Voici la SIGNATURE d'un énoncé Lean 4. Énonce en clair, 1–2 phrases, CE QUE il affirme.\n\n```lean\n{s}\n```")
JP_S=("Énoncé du lecteur :\n«{cand}»\n\nRÉFÉRENCE :\n«{ref}»\n\nMÊME contenu ? 0=différent, 10=même. "
      "JSON: {{\"score\":<0-10>}}")
def parse(t):
    for x in re.findall(r'\{[^{}]*score[^{}]*\}',t):
        try: return int(round(float(json.loads(x)["score"])))
        except: pass
    return None
async def call(c,msgs,temp):
    async with SEM:
        for _ in range(4):
            try:
                r=await asyncio.wait_for(c.post(URL,headers={"Authorization":f"Bearer {KEY}"},
                    json={"model":M,"messages":msgs,"max_tokens":4000,"temperature":temp}),900)
                if r.status_code==200: return r.json()["choices"][0]["message"].get("content") or ""
            except Exception: await asyncio.sleep(5)
        return ""
async def score(c,RP,JP,src,gold):
    inf=await call(c,[{"role":"user","content":RP.format(s=src)}],0.2)
    sc=await asyncio.gather(*[call(c,[{"role":"user","content":JP.format(cand=inf,ref=gold)}],0.7) for _ in range(K)])
    v=[x for x in (parse(t) for t in sc) if x is not None]; return st.mean(v) if v else None

async def main():
    async with httpx.AsyncClient(timeout=httpx.Timeout(900.0)) as c:
        # method: named / anon / anon_strict / sig(signature-only, no proof)
        async def m_one(n):
            return {c2: await score(c,RP_M,JP_M,src,n["latex_proof"]) for c2,src in
                    {"named":n["lean_proof"],"anon":anon(n["lean_proof"]),
                     "anon_strict":anon_strict(n["lean_proof"]),"sig(no-body)":anon(n["lean_sig"])}.items()}
        # statement: named / anon_strict
        async def s_one(n):
            return {c2: await score(c,RP_S,JP_S,src,n["statement"]) for c2,src in
                    {"named":n["lean_sig"],"anon_strict":anon_strict(n["lean_sig"])}.items()}
        mr=await asyncio.gather(*[m_one(n) for n in meth])
        sr=await asyncio.gather(*[s_one(n) for n in stmt])
    json.dump({"method":mr,"statement":sr},open("lm_rerun_results.json","w"),indent=1)
    print(f"### RE-RUN (random seed=7, strict anon + sig-on-readback)  method n={len(mr)} statement n={len(sr)} K={K}")
    print("METHOD readback:")
    for cond in ["named","anon","anon_strict","sig(no-body)"]:
        v=[r[cond] for r in mr if r.get(cond) is not None]; print(f"  {cond:14} mean={st.mean(v):.2f} (sd {st.pstdev(v):.2f})")
    print("STATEMENT readback:")
    for cond in ["named","anon_strict"]:
        v=[r[cond] for r in sr if r.get(cond) is not None]; print(f"  {cond:14} mean={st.mean(v):.2f} (sd {st.pstdev(v):.2f})")
asyncio.run(main())

# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
# #2 DRIFT DETECTOR. LeanMarathon's selling point: no silent mis-formalization. Test bidirectionality
# AS A TOOL: corrupt a Lean statement (one subtle meaningful change), read it back, judge vs the
# ORIGINAL gold. If the corrupted readback scores much lower than the clean one, the probe DETECTS
# the drift. Usage: uv run lm_drift.py [N]
import os, sys, json, asyncio, re, statistics as st
import httpx
from lm_common import load, rsample
KEY=os.environ["DEEPSEEK_API_KEY"]; URL="https://api.deepseek.com/chat/completions"; M="deepseek-v4-pro"
N=int(sys.argv[1]) if len(sys.argv)>1 else 40; K=2; SEM=asyncio.Semaphore(20)
keep=load("statement"); keep.sort(key=lambda n:(n["repo"], n["statement"] or ""))
sample=rsample(keep, N, seed=7)

CORRUPT=("Voici la signature d'un énoncé Lean 4. Introduis EXACTEMENT UN changement subtil mais "
         "mathématiquement SIGNIFICATIF (inverser un quantificateur ∀↔∃, inverser une inégalité ≤↔≥/<↔>, "
         "changer une constante/un exposant, nier une hypothèse). Garde tout le reste identique et "
         "l'allure bien-formée. Renvoie UNIQUEMENT le code Lean modifié, rien d'autre.\n\n```lean\n{s}\n```")
RP=("Voici la SIGNATURE d'un énoncé formel Lean 4. Énonce en clair, 1–2 phrases, CE QUE cet énoncé "
    "affirme, sans paraphraser la syntaxe.\n\n```lean\n{s}\n```")
JP=("Énoncé du lecteur :\n«{cand}»\n\nÉnoncé de RÉFÉRENCE :\n«{ref}»\n\nMÊME contenu mathématique ? "
    "0=différent/faux, 10=même claim. JSON: {{\"score\":<0-10>}}")
def parse(t):
    for x in re.findall(r'\{[^{}]*score[^{}]*\}',t):
        try: return int(round(float(json.loads(x)["score"])))
        except: pass
    return None
def strip_code(t):
    m=re.search(r"```(?:lean)?\s*(.*?)```", t, re.DOTALL); return (m.group(1).strip() if m else t.strip())
async def call(c,msgs,mt,temp):
    async with SEM:
        for _ in range(4):
            try:
                r=await asyncio.wait_for(c.post(URL,headers={"Authorization":f"Bearer {KEY}"},
                    json={"model":M,"messages":msgs,"max_tokens":mt,"temperature":temp}),900)
                if r.status_code==200: return r.json()["choices"][0]["message"].get("content") or ""
            except Exception: await asyncio.sleep(5)
        return ""
async def score(c, lean, gold):
    inf=await call(c,[{"role":"user","content":RP.format(s=lean)}],3000,0.2)
    sc=await asyncio.gather(*[call(c,[{"role":"user","content":JP.format(cand=inf,ref=gold)}],3000,0.7) for _ in range(K)])
    v=[x for x in (parse(t) for t in sc) if x is not None]; return (st.mean(v) if v else None)
async def main():
    async with httpx.AsyncClient(timeout=httpx.Timeout(900.0)) as c:
        async def one(n):
            corrupted=strip_code(await call(c,[{"role":"user","content":CORRUPT.format(s=n["lean_sig"])}],3000,0.7))
            clean_s = await score(c, n["lean_sig"], n["statement"])
            corr_s  = await score(c, corrupted,     n["statement"]) if corrupted and corrupted!=n["lean_sig"] else None
            return {"clean":clean_s,"corrupt":corr_s,"changed":bool(corrupted and corrupted!=n["lean_sig"])}
        res=await asyncio.gather(*[one(n) for n in sample])
    json.dump(res,open("lm_drift_results.json","w"),indent=1)
    pairs=[(r["clean"],r["corrupt"]) for r in res if r["clean"] is not None and r["corrupt"] is not None]
    drops=[a-b for a,b in pairs]
    print(f"### DRIFT DETECTOR (statement)  n_corrupted={len(pairs)} / {len(sample)} sampled  K={K}")
    print(f"clean readback      mean = {st.mean([a for a,_ in pairs]):.2f}")
    print(f"corrupted readback  mean = {st.mean([b for _,b in pairs]):.2f}")
    print(f"detection drop (clean-corrupt) mean = {st.mean(drops):+.2f}")
    print(f"% drift DETECTED (drop ≥3) = {100*sum(1 for d in drops if d>=3)/len(drops):.0f}%")
asyncio.run(main())

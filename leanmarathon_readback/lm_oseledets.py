# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
# #4 CROSS-CORPUS replication of statement-readback on lean4-oseledets (ergodic theory), a leanblueprint
# project: each theorem/lemma env in blueprint/*.tex pairs a LaTeX statement with \lean{Name}; the Lean
# decl is found in the source. Same probe as LeanMarathon statement-readback -> tests generality
# (not LeanMarathon-specific). Usage: uv run lm_oseledets.py dry | run [N]
import os, sys, re, json, asyncio, statistics as st
from pathlib import Path
from lm_common import anon
ROOT = Path.home()/"Code/AITP/MATHAI/external/lean4-oseledets"

def index_lean():
    idx={}
    for f in ROOT.rglob("*.lean"):
        if "/.lake/" in str(f): continue
        txt=f.read_text(errors="ignore")
        for m in re.finditer(r"(?m)^(?:@\[[^\]]*\]\s*)?(?:noncomputable\s+|private\s+|protected\s+|scoped\s+)*(theorem|lemma|def|abbrev)\s+([A-Za-z_][\w']*)", txt):
            name=m.group(2)
            if name in idx: continue
            tail=txt[m.start():]; sig=re.split(r":=",tail,1)[0].strip()
            if 10<len(sig)<1200: idx[name]=sig
    return idx

def clean_tex(s):
    s=re.sub(r"\\(lean|label|uses)\{[^}]*\}","",s); s=s.replace("\\leanok","")
    s=re.sub(r"\\begin\{[^}]*\}(\[[^\]]*\])?","",s); s=re.sub(r"\\end\{[^}]*\}","",s)
    return re.sub(r"\s+"," ",s).strip()

def parse_pairs():
    lean=index_lean(); pairs=[]
    for tex in (ROOT/"blueprint"/"src").rglob("*.tex"):
        t=tex.read_text(errors="ignore")
        for m in re.finditer(r"\\begin\{(theorem|lemma|proposition|corollary)\}(.*?)\\end\{\1\}", t, re.DOTALL):
            body=m.group(2)
            ln=re.search(r"\\lean\{([^}]+)\}", body)
            if not ln: continue
            short=ln.group(1).split(".")[-1]
            if short not in lean: continue
            stmt=clean_tex(body)
            if len(stmt)>20: pairs.append({"name":short,"statement":stmt,"lean_sig":lean[short]})
    # dedup by name
    seen=set(); out=[]
    for p in pairs:
        if p["name"] in seen: continue
        seen.add(p["name"]); out.append(p)
    return out

if sys.argv[1:] and sys.argv[1]=="dry":
    p=parse_pairs(); print(f"oseledets pairs (LaTeX stmt ↔ Lean decl): {len(p)}")
    for x in p[:2]:
        print(f"\n[{x['name']}]\n LEAN: {x['lean_sig'][:160].replace(chr(10),' ')}\n GOLD: {x['statement'][:160]}")
    sys.exit(0)

import httpx
KEY=os.environ["DEEPSEEK_API_KEY"]; URL="https://api.deepseek.com/chat/completions"; M="deepseek-v4-pro"
N=int(sys.argv[2]) if len(sys.argv)>2 else 60; K=2; SEM=asyncio.Semaphore(24)
pairs=parse_pairs(); pairs.sort(key=lambda p:p["name"])
sample=pairs if N>=len(pairs) else [pairs[i] for i in range(0,len(pairs),max(1,len(pairs)//N))][:N]
RP=("Voici la SIGNATURE d'un énoncé formel Lean 4. Énonce en clair, 1–2 phrases, CE QUE cet énoncé "
    "affirme, sans paraphraser la syntaxe.\n\n```lean\n{s}\n```")
JP=("Énoncé du lecteur :\n«{cand}»\n\nÉnoncé de RÉFÉRENCE :\n«{ref}»\n\nMÊME contenu mathématique ? "
    "0=différent/faux, 10=même claim. JSON: {{\"score\":<0-10>}}")
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
            src=n["lean_sig"] if cond=="named" else anon(n["lean_sig"])
            inf=await call(c,[{"role":"user","content":RP.format(s=src)}],4000,0.2)
            sc=await asyncio.gather(*[call(c,[{"role":"user","content":JP.format(cand=inf,ref=n["statement"])}],4000,0.7) for _ in range(K)])
            v=[x for x in (parse(t) for t in sc) if x is not None]
            return {"cond":cond,"mean":(st.mean(v) if v else None),"gold":n["statement"][:120]}
        res=await asyncio.gather(*[one(n,cond) for n in sample for cond in ("named","anon")])
    json.dump(res,open("lm_oseledets_results.json","w"),indent=1)
    print(f"### OSELEDETS cross-corpus statement-readback  n={len(sample)}  K={K}")
    for cond in ("named","anon"):
        ms=[r["mean"] for r in res if r["cond"]==cond and r["mean"] is not None]
        print(f"{cond:>6}: n={len(ms)} mean={st.mean(ms):.2f} (sd {st.pstdev(ms):.2f})")
    nd={r["gold"]:r["mean"] for r in res if r["cond"]=="named"}; ad={r["gold"]:r["mean"] for r in res if r["cond"]=="anon"}
    d=[nd[k]-ad[k] for k in nd if nd.get(k) is not None and ad.get(k) is not None]
    print(f"Δ(named-anon) mean={st.mean(d):+.2f} | struct(Δ≤0)={sum(1 for x in d if x<=0)} name-dep(Δ>2)={sum(1 for x in d if x>2)} of {len(d)}")
asyncio.run(main())

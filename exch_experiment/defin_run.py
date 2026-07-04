# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
import asyncio,json,os,re
import httpx
KEY=os.environ["DEEPSEEK_API_KEY"]; URL="https://api.deepseek.com/chat/completions"; M="deepseek-v4-pro"
forms=json.load(open("/tmp/exch_forms.json"))
async def call(c,msgs,mt):
    for _ in range(3):
        try:
            r=await asyncio.wait_for(c.post(URL,headers={"Authorization":f"Bearer {KEY}"},json={"model":M,"messages":msgs,"max_tokens":mt}),600)
            if r.status_code==200: return r.json()["choices"][0]["message"].get("content") or ""
        except Exception: await asyncio.sleep(5)
    return ""
READER=("Voici une preuve formelle Lean 4 de « Contractable ⇒ Conditionnellement i.i.d. » "
        "(théorème de de Finetti). Plusieurs méthodes mathématiques distinctes existent pour ce "
        "résultat. Décris en français, concisément, la MÉTHODE et les idées-clés de CETTE preuve-ci "
        "(la technique mathématique employée), sans paraphraser le code ligne à ligne.\n\n```lean\n{s}\n```")
JUDGE=("Description d'une méthode de preuve produite par un lecteur :\n«{cand}»\n\n"
       "Méthode de RÉFÉRENCE :\n«{ref}»\n\n"
       "À quel point la description du lecteur correspond-elle à CETTE méthode de référence précise "
       "(même technique mathématique) ? 0=technique totalement différente, 10=même technique. "
       'Réponds en JSON sur la dernière ligne : {{"score":<0-10>}}')
async def main():
    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as c:
        s1=await asyncio.gather(*[call(c,[{"role":"user","content":READER.format(s=o["script"])}],8000) for o in forms])
        print("=== informalisations produites ===")
        for o,s in zip(forms,s1): print(f"[{o['method']}] {s[:160].strip()}...")
        # confusion : s1[i] jugé vs gold[j]
        conf={}
        for i,oi in enumerate(forms):
            for j,oj in enumerate(forms):
                t=await call(c,[{"role":"user","content":JUDGE.format(cand=s1[i],ref=oj["gold"])}],4000)
                mm=re.findall(r'\{[^{}]*score[^{}]*\}',t); sc=None
                for x in mm:
                    try: sc=int(json.loads(x)["score"])
                    except: pass
                conf[(oi["method"],oj["method"])]=sc
        meths=[o["method"] for o in forms]
        print("\n=== MATRICE DE CONFUSION (ligne=script lu, col=gold jugé) ===")
        print("            "+" ".join(f"{m:>10s}" for m in meths))
        for i in meths:
            print(f"{i:>10s}  "+" ".join(f"{str(conf[(i,j)]):>10s}" for j in meths))
        diag=[conf[(m,m)] for m in meths if conf[(m,m)] is not None]
        off=[conf[(i,j)] for i in meths for j in meths if i!=j and conf[(i,j)] is not None]
        import statistics as st
        print(f"\ndiagonale (récup. bonne méthode) mean={st.mean(diag):.1f} | hors-diag (confusion) mean={st.mean(off):.1f}")
asyncio.run(main())

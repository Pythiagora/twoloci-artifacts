# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
# Hardened de Finetti discrimination: K-repeated judging (variance) on a given forms file.
# Usage: uv run defin_hard.py <forms.json> <tag>
#   reader: 1 DeepSeek informalization per method (saved FULL to exch_<tag>_informal.json)
#   judge : DeepSeek scores each (cand_i vs gold_j) cell K times (temp 1.0) -> mean matrix + sd
# Raw scores dumped to exch_<tag>_judge_raw.json so a 2nd judge (Opus, in-session) can re-score the SAME informalizations.
import asyncio, json, os, re, sys, statistics as st
import httpx

KEY = os.environ["DEEPSEEK_API_KEY"]; URL = "https://api.deepseek.com/chat/completions"; M = "deepseek-v4-pro"
FORMS_PATH = sys.argv[1]; TAG = sys.argv[2]; K = int(os.environ.get("K", "5"))
forms = json.load(open(FORMS_PATH))

async def call(c, msgs, mt, temp):
    for _ in range(4):
        try:
            r = await asyncio.wait_for(c.post(URL, headers={"Authorization": f"Bearer {KEY}"},
                json={"model": M, "messages": msgs, "max_tokens": mt, "temperature": temp}), 900)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"].get("content") or ""
        except Exception:
            await asyncio.sleep(5)
    return ""

READER = ("Voici une preuve formelle Lean 4 de « Contractable ⇒ Conditionnellement i.i.d. » "
          "(théorème de de Finetti). Plusieurs méthodes mathématiques distinctes existent pour ce "
          "résultat. Décris en français, concisément, la MÉTHODE et les idées-clés de CETTE preuve-ci "
          "(la technique mathématique employée), sans paraphraser le code ligne à ligne.\n\n```lean\n{s}\n```")
JUDGE = ("Description d'une méthode de preuve produite par un lecteur :\n«{cand}»\n\n"
         "Méthode de RÉFÉRENCE :\n«{ref}»\n\n"
         "À quel point la description du lecteur correspond-elle à CETTE méthode de référence précise "
         "(même technique mathématique) ? 0=technique totalement différente, 10=même technique. "
         'Réponds en JSON sur la dernière ligne : {{"score":<0-10>}}')

def parse(t):
    for x in re.findall(r'\{[^{}]*score[^{}]*\}', t):
        try: return int(round(float(json.loads(x)["score"])))
        except Exception: pass
    return None

async def main():
    async with httpx.AsyncClient(timeout=httpx.Timeout(900.0)) as c:
        # READER (1 canonical informalization per method, temp 0.2 for stability)
        s1 = await asyncio.gather(*[call(c, [{"role": "user", "content": READER.format(s=o["script"])}], 16000, 0.2) for o in forms])
        meths = [o["method"] for o in forms]
        informal = [{"method": m, "informal": s} for m, s in zip(meths, s1)]
        json.dump(informal, open(f"exch_{TAG}_informal.json", "w"), ensure_ascii=False, indent=1)
        print("=== informalisations (sauvées full) ===")
        for o in informal: print(f"[{o['method']}] {o['informal'][:140].strip()}...")

        # JUDGE K times per cell (temp 1.0 to stress-test stability)
        async def cell(i, j):
            outs = await asyncio.gather(*[
                call(c, [{"role": "user", "content": JUDGE.format(cand=s1[i], ref=forms[j]["gold"])}], 16000, 1.0)
                for _ in range(K)])
            return [parse(t) for t in outs]
        raw = {}
        for i in range(len(forms)):
            for j in range(len(forms)):
                scores = [x for x in await cell(i, j) if x is not None]
                raw[f"{meths[i]}__{meths[j]}"] = scores

        json.dump(raw, open(f"exch_{TAG}_judge_raw.json", "w"), ensure_ascii=False, indent=1)
        mean = {k: (st.mean(v) if v else None) for k, v in raw.items()}
        print(f"\n=== MATRICE moyenne sur K={K} (ligne=script lu, col=gold) ===")
        print("            " + " ".join(f"{m:>10s}" for m in meths))
        for i in meths:
            print(f"{i:>10s}  " + " ".join(f"{mean[f'{i}__{j}']:>10.1f}" for j in meths))
        diag = [mean[f"{m}__{m}"] for m in meths]
        offc = [mean[f"{i}__{j}"] for i in meths for j in meths if i != j]
        offall = [x for i in meths for j in meths if i != j for x in raw[f"{i}__{j}"]]
        print(f"\ndiag mean={st.mean(diag):.2f}  |  hors-diag mean={st.mean(offc):.2f} "
              f"(sd des 6 cellules={st.pstdev(offc):.2f}; sd brut K·6={st.pstdev(offall):.2f}; "
              f"min..max cellules={min(offc):.1f}..{max(offc):.1f})")

asyncio.run(main())

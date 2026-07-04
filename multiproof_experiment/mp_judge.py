# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
# Generic within-theorem method discrimination, hardened (K-repeated DeepSeek judge).
# Usage: uv run mp_judge.py <forms.json> <tag>
#   reader: 1 DeepSeek informalization per method (temp 0.2, saved full)
#   judge : DeepSeek scores each (cand_i vs gold_j) cell K times (temp 1.0) -> mean matrix + margin
# Saves mp_<tag>_informal.json + mp_<tag>_judge_raw.json for a 2nd judge (Opus, in-session).
import asyncio, json, os, re, sys, statistics as st
import httpx

KEY = os.environ["DEEPSEEK_API_KEY"]; URL = "https://api.deepseek.com/chat/completions"; M = "deepseek-v4-pro"
FORMS = json.load(open(sys.argv[1])); TAG = sys.argv[2]; K = int(os.environ.get("K", "5"))

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

READER = ("Voici une preuve formelle Lean 4 du théorème : « {stmt} ». "
          "Plusieurs méthodes mathématiques distinctes existent pour ce résultat. "
          "Décris en français, concisément, la MÉTHODE et les idées-clés de CETTE preuve-ci "
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
    meths = [o["method"] for o in FORMS]
    async with httpx.AsyncClient(timeout=httpx.Timeout(900.0)) as c:
        s1 = await asyncio.gather(*[call(c, [{"role": "user", "content": READER.format(stmt=o["stmt"], s=o["script"])}], 16000, 0.2) for o in FORMS])
        json.dump([{"method": m, "informal": s} for m, s in zip(meths, s1)],
                  open(f"mp_{TAG}_informal.json", "w"), ensure_ascii=False, indent=1)
        print("=== informalisations (sauvées full) ===")
        for m, s in zip(meths, s1): print(f"[{m}] {s[:130].strip()}...")

        async def cell(i, j):
            outs = await asyncio.gather(*[
                call(c, [{"role": "user", "content": JUDGE.format(cand=s1[i], ref=FORMS[j]["gold"])}], 16000, 1.0)
                for _ in range(K)])
            return [x for x in (parse(t) for t in outs) if x is not None]
        raw = {}
        for i in range(len(FORMS)):
            for j in range(len(FORMS)):
                raw[f"{meths[i]}__{meths[j]}"] = await cell(i, j)
        json.dump(raw, open(f"mp_{TAG}_judge_raw.json", "w"), ensure_ascii=False, indent=1)

        mean = {k: (st.mean(v) if v else 0.0) for k, v in raw.items()}
        print(f"\n=== MATRICE moyenne K={K} (ligne=script lu, col=gold) — {TAG} ===")
        print("            " + " ".join(f"{m[:9]:>10s}" for m in meths))
        for i in meths:
            print(f"{i[:10]:>10s}  " + " ".join(f"{mean[f'{i}__{j}']:>10.1f}" for j in meths))
        diag = [mean[f"{m}__{m}"] for m in meths]
        offc = [mean[f"{i}__{j}"] for i in meths for j in meths if i != j]
        print(f"\ndiag mean={st.mean(diag):.2f} | hors-diag mean={st.mean(offc):.2f} | "
              f"MARGE={st.mean(diag)-st.mean(offc):.2f}  (off sd cellules={st.pstdev(offc):.2f})")

asyncio.run(main())

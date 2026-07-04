# DifferentProofs — discrimination de méthode multi-théorèmes (n monté 3 → 17)

Réplication du résultat de Finetti sur `seewoo5/DifferentProofs` (Lean 4 + Mathlib, créé 2026-05-04,
0 sorry/axiom, faible contamination) : **4 théorèmes, 14 preuves** à méthodes distinctes, un `def : Prop`
partagé par théorème, un fichier par méthode. Pipeline : `mp_prep.py` (clôture d'imports intra-repo →
développement complet par preuve ; golds = prose du blueprint Verso de l'auteur ; anonymisation des
identifiants révélateurs de méthode → `F{n}`) + `mp_judge.py` (lecteur DeepSeek → informalisation ;
juge DeepSeek K=5 temp 1.0 ; marge = diag − hors-diag).

## Marges (anonymisé)
| Théorème | méthodes | marge | diag | off | lecture |
|---|---|---|---|---|---|
| Basel | 2 (Cauchy, Parseval) | **10.00** | 10.0 | 0.00 | élémentaire vs Fourier — disjoint |
| FLT | 4 (Binomial, Lagrange, Alkauskas, Dynamical) | **9.97** | 10.0 | 0.03 | 4 routes orthogonales, toutes isolées |
| Primes | 5 (Euclid, Euler, Goldbach, Saidak, Wunderlich) | **7.82** | 10.0 | 2.18 | **cluster** Goldbach/Saidak/Wunderlich |
| √2 | 3 (Descent, Valuation, FermatLast) | **6.63** | 7.33 | 0.70 | Descent/Valuation séparées ; FermatLast = échec récup. |

## Résultats clés
1. **L'anonymisation n'effondre pas la discrimination — la structure porte la méthode.** Réfute l'hypothèse
   « preuve compacte = méthode dans un seul nom de lemme Mathlib → s'effondre une fois masqué ». FLT Binomial
   (9 identifiants masqués, `add_pow_expChar` → `F_n`) discrimine parfaitement : le lecteur lit
   « endomorphisme de Frobenius » depuis l'**induction dans ℤ/pℤ + la forme du goal**, pas depuis le nom.
   Et **anon ≈ avec-noms** sur FLT (9.97 = 9.97) : les noms n'ajoutent rien.
2. **Les confusions résiduelles = parenté mathématique réelle, pas du bruit.**
   - Primes : **{Goldbach, Saidak, Wunderlich}** se confondent (croisés 5–10) = la famille « suite à premiers-
     entre-eux / facteurs toujours nouveaux » (Fermat / n(n+1) / Fibonacci). Euclid (contradiction n!+1) et
     Euler (divergence harmonique) s'isolent. **Confirmé par 2 juges** (DeepSeek off 2.18 / Opus off 1.95).
   - Cf. de Finetti : L² ↔ Koopman (le théorème ergodique en moyenne EST de la convergence L²).
3. **Méthodes vraiment distinctes ⇒ marge ≈ 10** (Basel, FLT). **Méthodes proches ⇒ confusion structurée**
   (Primes, de Finetti). La « résolution » de la relecture = similarité-de-méthode mathématique.

## Caveats honnêtes
- **Théorèmes célèbres = mode plus facile** : le lecteur mobilise sa connaissance générale (Frobenius, Euclide…)
  pour lire la structure. de Finetti (moins canonique) reste le test le plus dur — et il marche aussi.
  → présenter DifferentProofs comme *généralisation à n=17 / domaines variés*, de Finetti comme *cas dur*.
- **√2 FermatLast : diag = 2.0** = échec de récupération (preuve exotique « réduire √2∈ℚ à un contre-exemple
  FLT n=3 », 7 masques, 567c) — le lecteur ne la rattache même pas à son propre gold. Limite de la
  reader-recovery sur preuves très courtes + inhabituelles. À re-checker (gold trop spécifique ?).
- **Confound noms-gardés** : `ZMod/Nat/Real…` gardés dans le KEEP. FLT anon≈named suggère que les noms ne
  portent pas l'effet, mais re-test en **masquage agressif** (tout sauf syntaxe Lean) encore à faire.
- **Opus-juge non aveugle** (connaît l'hypothèse) → sanity-check concordant, pas confirmation indépendante.
  Vrai casse-circularité = gold humain.

## Synthèse pour la thèse
Sur des maths à *choix de méthode non trivial*, l'identité de méthode est **récupérable depuis la structure
de preuve anonymisée**, par un lecteur machine, jugée robuste à 2 juges, résistante à la contamination
(anonymisation + repos récents/obscurs). Les confusions tracent la parenté mathématique. C'est la
**bidirectionnalité structurelle** — à contraster avec le NUL sur l'agrég (méthodes routinières → plafond +
réduction à la taille). La bidirectionnalité est substantielle exactement là où le choix de méthode l'est.

## Contrôles de falsification + les DEUX LOCUS (2026-06-20)
Pour répondre à « ça marche ou c'est trivial ? », 3 conditions au-delà de `anon` :
- **aggr** (`mp_controls.py`) : masquage agressif (ZMod/Nat/Real/types aussi). Tue le confound « noms gardés ».
- **sig** (`mp_controls.py`) : corps de preuve retiré (`:= by sorry`). Tue le confound « priors / théorème célèbre ».
- **locus** (`mp_locus.py`) : objets ÉNONCÉS opacifiés (def-bodies → HIDDEN, types des lemmes auxiliaires → HIDDEN),
  corps tactiques gardés. Isole le contrôle-flux tactique du contenu énoncé.

| condition | FLT (marge) | Primes (marge) |
|---|---|---|
| anonymisé | 9.97 | 7.82 |
| agressif | 10.00 | 5.82 |
| **signature-only** | **0.15** | 6.52 |
| **locus (objets opacifiés)** | **9.97** | **4.02** |

**Conclusions (mesurées, pas narrées) :**
1. **Ce ne sont ni les priors ni les noms.** FLG : aggr 10.0 (pas les noms) + sig 0.15 (pas les priors : sans le
   corps, même en sachant que c'est FLT, le lecteur ne discrimine plus). Bidirectionnalité **structurelle réelle**.
2. **Deux loci, quantifiés :**
   - **Locus (a) — contrôle-flux tactique** (FLT, de Finetti) : **invariant** noms/types/opacification d'objets
     (FLT locus 9.97 = anon) ; ne meurt qu'en retirant le corps (sig 0.15).
   - **Locus (b) — objets énoncés** (Euclid n!+1, Wunderlich Fib(37)) : sig SURVIT (6.52, méthode dans le *quoi*),
     mais locus EFFONDRE leur diagonale → **0.0** (objets cachés ⇒ méthode irrécupérable).
3. **Inséparabilité en Lean** : les tactiques portent des termes ⇒ Goldbach/Saidak restent récupérables sous
   `locus` (diag 10) via l'arithmétique résiduelle dans les corps de lemmes (`2^(2^n)+1`, la récurrence).
   La séparation *propre* (a)/(b) n'existe que pour les preuves à **Prop partagée + méthode-en-contrôle-flux**
   (FLT/de Finetti) — d'où le rôle d'instruments-étalons de ces cas.

**Portée thèse** : la bidirectionnalité existe et est mesurable, mais le critère doit **spécifier le locus** —
un « spaghetti de tactiques » peut être porteur-de-méthode (locus a, l'induction de Frobenius) OU
opaque-mais-méthode-dans-les-énoncés-voisins (locus b). Distinction absente de Rav/Azzouni.

Données : `mp_{THM}.json` (raw) / `_anon` / `_aggr` / `_sig` / `_locus` (.json + `_informal` + `_judge_raw`) ;
harnais `mp_prep.py`, `mp_judge.py`, `mp_controls.py`, `mp_locus.py`.

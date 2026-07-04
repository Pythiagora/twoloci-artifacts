# de Finetti — discrimination de méthode, DURCIE (dual-juge, K=5)

Hardening du résultat de Finetti contre la critique « juge LLM unique, 1 call/cellule, n=3 ».
3 preuves Kallenberg (Martingale / L² / Koopman) du même théorème, **développement complet anonymisé**
(identifiants masqués → `F{n}`, pas de rappel verbatim possible) vs **spine** (squelette seul, contrôle négatif).

Protocole : lecteur DeepSeek informalise chaque preuve (temp 0.2, sauvé en clair) → 2 familles de juges
notent chaque cellule (cand_i vs gold_j) 0–10. Juge A = DeepSeek-v4-pro **K=5 reps, temp 1.0** (variance).
Juge B = **Opus 4.8** (in-session, gratuit) sur les **mêmes** informalisations.

## Métrique : MARGE = diag − hors-diag
Plus honnête que le hors-diag seul : le spine peut échouer soit par **cross-confusion** (off ↑, run original),
soit par **effondrement de la diagonale** (diag ↓, ce run). La marge capture les deux modes ; le hors-diag seul
non. → c'est pourquoi le hors-diag spine est passé de 6.5 (run original) à 3.83 (ici) sans que le spine
ne « marche » mieux : il échoue juste autrement.

| Variante | Juge | diag | hors-diag | **marge** |
|---|---|---|---|---|
| **FULL** (dev complet anonymisé) | DeepSeek (K=5) | 9.87 | 2.70 | **7.17** |
| **FULL** | Opus 4.8 | 9.67 | 1.67 | **8.00** |
| SPINE (squelette anonymisé) | DeepSeek (K=5) | 4.67 | 3.83 | **0.84** |
| SPINE | Opus 4.8 | 3.00 | 1.33 | **1.67** |

**Les deux juges, deux familles indépendantes, concordent** : le développement complet discrimine
(marge ≈ 7–8), le squelette non (marge ≈ 1–2). Le contraste survit au changement de juge.

## Matrices FULL (ligne = script lu, col = gold)

DeepSeek K=5 (moyenne) :
```
            Martingale    L2   Koopman
Martingale       10.0    3.0     0.4
        L2        1.2   10.0     9.8
   Koopman        0.8    1.0     9.6
```
Opus 4.8 :
```
            Martingale    L2   Koopman
Martingale         10      0       0
        L2          2     10       3
   Koopman          1      4       9
```
Structure commune : **Martingale parfaitement isolée** (sans aucun nom révélateur) ;
**L²↔Koopman = seule confusion**, et elle est **mathématiquement correcte** (le théorème ergodique
en moyenne / von Neumann EST de la convergence L² — le lecteur Koopman invoque explicitement « projections L² »).

## Variance (juge DeepSeek, FULL)
sd des 6 cellules hors-diag = 3.28 ; min..max = 0.4..9.8. La **diagonale est solide** (9.87) ;
le hors-diag est bruité (jugement quasi-binaire 0/10 par call, dispersion entre reps). → la marge est
robuste, mais les valeurs hors-diag individuelles ne sont pas précises à n=3.

## Ce qui est durci vs ce qui reste ouvert
- ✓ **Pas un artefact de juge unique** : 2 familles concordent sur le contraste full/spine.
- ✓ **Pas un seul tirage** : K=5, diagonale stable.
- ✓ **Métrique honnête** : la marge, pas le hors-diag seul (dont le run original surévaluait le spine).
- ✗ **n = 3** reste — 1 théorème, 3 preuves. (Chantier : agent en cours pour d'autres théorèmes multi-preuves.)
- ✗ **Opus-juge n'est PAS aveugle** (connaît l'hypothèse) → sanity-check, pas confirmation indépendante.
  Le vrai casse-circularité = **gold humain** (un annotateur humain / collègue note les 9 paires en aveugle). À préparer.
- Contamination : repo créé 2025-09-29, preuves 2025-10-08 → la défense est l'**anonymisation**, pas la date.

## Batterie de contrôle sur l'ancre NON-CANONIQUE (2026-06-20, `exch_controls.py`)
Mêmes contrôles que DifferentProofs (aggr / sig / locus), pour tester si le résultat de Finetti tient
sur un théorème *non célèbre* (≠ FLT/Basel que le lecteur connaît par cœur). DeepSeek K=5, full devs.

| condition | marge | diag | hors-diag | lecture |
|---|---|---|---|---|
| anon (full, rappel) | ~7 | 10 | 2.70 | Martingale isolée, L²/Koopman groupés |
| **aggr** (types masqués) | **5.43** | 10.0 | 4.57 | Martingale isolée ; L²↔Koopman confus |
| **sig** (corps retirés) | **3.87** | 8.07 | 4.20 | L² diag s'effondre (4.4) ; Martingale tient (10) |
| **locus** (objets opacifiés) | **5.90** | 10.0 | 4.10 | Martingale isolée ; L²/Koopman groupés |

**Conclusions :**
1. **Le caveat « famous = easy » était réel et est chiffré** : de Finetti (non-canonique) plafonne à ~5.5,
   loin des 10 de FLT/Basel. La canonicité gonflait les marges DifferentProofs.
2. **aggr + locus survivent** (5.4–5.9) → ni noms, ni objets énoncés : la méthode est dans la **structure
   des corps tactiques** (estimations martingale/L²/ergodiques embarquées). Bidirectionnalité structurelle
   réelle sur l'ancre dure.
3. **sig ne s'effondre PAS proprement** (3.87 vs FLT 0.15) : de Finetti est **locus MIXTE** — son échafaudage
   riche de lemmes auxiliaires fuit un signal partiel même signatures masquées. → **FLT reste le seul
   instrument locus-(a) PUR** (Prop partagée + échafaudage minimal → sig→0).
4. **Martingale isolée dans TOUTES les conditions** = signal structurel le plus robuste ; **L²/Koopman
   confusables partout** = parenté mathématique réelle (mean-ergodique = L²), robuste à tous les masquages.
(Juge = DeepSeek seul sur ces contrôles ; le dual-juge Opus n'a pas été re-passé dessus.)

Données : `exch_{full,spine,aggr,sig,locus}_informal.json` + `_judge_raw.json` (K=5) ;
harnais `defin_hard.py`, `exch_controls.py`.

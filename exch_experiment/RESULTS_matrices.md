# de Finetti (cameronfreer/exchangeability) — discrimination de méthode 3×3
# 3 preuves Kallenberg (Martingale/L²/Koopman) du même théorème (Contractable→cIID)

## RUN 1 — scripts AVEC noms (spine top-level)
=== MATRICE DE CONFUSION (ligne=script lu, col=gold jugé) ===
            Martingale         L2    Koopman
Martingale          10          0          0
        L2          10         10         10
   Koopman           0          0         10

diagonale (récup. bonne méthode) mean=10.0 | hors-diag (confusion) mean=3.3

## RUN 2 — spine ANONYMISÉ
=== MATRICE DE CONFUSION (ligne=script lu, col=gold jugé) ===
            Martingale         L2    Koopman
Martingale          10          1          9
        L2          10         10          1
   Koopman          10          8         10

diagonale (récup. bonne méthode) mean=10.0 | hors-diag (confusion) mean=6.5

## RUN 3 — PLEIN DÉVELOPPEMENT anonymisé
=== MATRICE DE CONFUSION (ligne=script lu, col=gold jugé) ===
            Martingale         L2    Koopman
Martingale          10          0          0
        L2           1         10         10
   Koopman           2         10         10

diagonale (récup. bonne méthode) mean=10.0 | hors-diag (confusion) mean=3.8

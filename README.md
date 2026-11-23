# Pick-and-place par ventouse en simulation (UR5 + PyBullet)

> **Projet inachevé, résultat négatif documenté.** La baseline sans apprentissage n'a réussi aucune saisie. La phase d'apprentissage n'a donc jamais commencé.

Objectif initial : un bras UR5 dépile un flan de carton, le saisit par ventouse, le transporte et le dépose, d'abord avec une baseline sans ML (phase 1), puis avec un flan pliable (phase 2) et de l'apprentissage pour anticiper les décrochages (phase 3).

Je publie ce dépôt tel quel : un résultat négatif bien mesuré est plus utile qu'un projet dont on tait l'échec.

## Résultats

Lancements enregistrés le 18 juin 2026, avec un seul jeu de paramètres physiques (flan de 80 g, friction 1,0). Critère de succès d'une dépose : flan levé de plus de 5 cm **et** erreur de position finale inférieure à 5 cm.

| | Valeur |
|---|---|
| Lancements enregistrés | 12 |
| Lancements sans aucun essai écrit (cause non analysée) | 4 |
| Essais terminés | 8 |
| Saisies réussies | **0 / 8** |
| Hauteur de levée mesurée | de -5,6 mm à 0,0 mm |
| Erreur de dépose (plan xy) | de 25,5 cm à 30,1 cm |

Dans tous les essais terminés, le flan ne suit pas l'effecteur : la hauteur de levée reste nulle, et l'erreur de dépose est de l'ordre de la distance entre la pile et la cible.

## Ce que je sais, et ce que je ne sais pas

- **Mesuré :** les chiffres ci-dessus, issus des fichiers `runs/trials_*.csv`.
- **Non établi :** la cause. Le modèle de ventouse crée une contrainte fixe entre l'effecteur et le flan seulement si le flan est à moins de `SUCTION_CONTACT_DIST` au moment de l'activation. Une levée nulle est compatible avec une contrainte jamais créée (flan hors de portée) comme avec une contrainte qui lâche. Je n'ai pas isolé laquelle, ni testé les deux hypothèses séparément.
- **Non testé :** la sensibilité à la masse et à la friction du flan, qui devait justifier la phase d'apprentissage.

## Ce qui a été construit

- Une configuration centralisée (`config.py`) : un seul endroit pour les paramètres de la scène, du flan, de la ventouse et des durées.
- Une scène (table, pile de 5 flans), un UR5 piloté par cinématique inverse, un modèle de ventouse par contrainte avec vérification du contact avant aspiration.
- Une journalisation CSV de chaque pas de simulation et de chaque essai, et des graphiques générés depuis ces CSV.
- Une première exploration de MuJoCo (modèle Panda) en parallèle de PyBullet.

## Structure

| Fichier | Rôle |
|---|---|
| `config.py` | Paramètres réglables |
| `scene.py` | Monde : sol, table, pile de flans |
| `robot.py` | Chargement de l'UR5, cinématique inverse |
| `suction.py` | Ventouse : aspirer / relâcher |
| `baseline_pick_place.py` | Séquence complète d'un essai |
| `logger.py`, `plots.py` | CSV et graphiques |
| `runs/` | Sorties : CSV (un par lancement) |

## Reproduire

Le modèle du robot vient d'un dépôt tiers, à cloner à côté de ce dossier :

    git clone -b robotflow --depth 1 https://github.com/ElectronicElephant/pybullet_ur5_robotiq
    pip install pybullet numpy matplotlib
    python baseline_pick_place.py --trials 5 --no-gui
    python plots.py

## Suite possible

1. Isoler la cause de l'échec : journaliser la distance effecteur-flan à l'activation de la ventouse et l'état de la contrainte à chaque pas.
2. Une fois la baseline fiable, mesurer son taux de succès sur une grille de masses et de frictions : c'est cette mesure qui justifierait un apprentissage.
3. Seulement ensuite, rendre le flan pliable.

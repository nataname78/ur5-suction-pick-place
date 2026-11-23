# Pick-and-place par ventouse en simulation (UR5 + PyBullet)

> **Projet inachevé, résultat négatif documenté.** L'effecteur n'a jamais atteint le flan : la ventouse n'a donc jamais agi, et aucune saisie n'a réussi. La phase d'apprentissage n'a pas commencé.

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
| Distance effecteur-flan à la fin de la descente | 14 cm (3 lancements), 68 cm (1), 113 cm (4) |

Le détail par lancement est dans `runs/resume_essais.csv`.

## Ce que montrent les données

- **La contrainte de succion n'a jamais été créée.** La ventouse n'agit qu'à moins de 2 cm du flan (`SUCTION_CONTACT_DIST`). `grasp_success` est le retour de `activate()`, qui renvoie faux si aucun flan n'est à portée : il vaut 0 dans les 8 essais. L'hypothèse d'un flan qui lâcherait en cours de transport est donc écartée.
- **La cause en amont : l'effecteur n'arrive pas au contact.** À la fin de la phase de descente, il est à 14 à 113 cm du flan selon le lancement, au lieu de moins de 2 cm.
- **Le reste en découle.** Le flan n'a jamais bougé : la levée est nulle et l'erreur de dépose (25 à 30 cm) correspond à l'écart entre la pile et la cible.

Méthode : les distances sont calculées à partir des CSV de trajectoire (non publiés, environ 200 Ko chacun), en prenant pour position du flan la cible de la descente moins 1 cm en hauteur, comme dans `baseline_pick_place.py`.

## Ce qui reste inconnu

- **Pourquoi l'effecteur n'atteint pas sa cible.** Pistes non testées : cible hors de la zone de travail fiable du bras, posture de repos qui éloigne la solution de la cinématique inverse, limites articulaires, repère `EE_LINK` décalé par rapport au bout de la ventouse.
- **Ce qui a changé entre les groupes de lancements** (distances de 14, 68 et 113 cm). Ce dossier n'a pas d'historique git.
- **La sensibilité à la masse et à la friction du flan**, qui devait justifier la phase d'apprentissage : non testée.

## Ce qui a été construit

- Une configuration centralisée (`config.py`) : un seul endroit pour les paramètres de la scène, du flan, de la ventouse et des durées.
- Une scène (table, pile de 5 flans), un UR5 piloté par cinématique inverse, un modèle de ventouse par contrainte avec vérification du contact avant aspiration.
- Une journalisation CSV de chaque pas de simulation et de chaque essai, et des graphiques générés depuis ces CSV.
- Une première exploration de MuJoCo (modèle Panda) en parallèle de PyBullet, non publiée.

## Structure

| Fichier | Rôle |
|---|---|
| `config.py` | Paramètres réglables |
| `scene.py` | Monde : sol, table, pile de flans |
| `robot.py` | Chargement de l'UR5, cinématique inverse |
| `suction.py` | Ventouse : aspirer / relâcher |
| `baseline_pick_place.py` | Séquence complète d'un essai |
| `logger.py`, `plots.py` | CSV et graphiques |
| `runs/resume_essais.csv` | Synthèse des 8 essais terminés |

## Reproduire

Le modèle du robot vient d'un dépôt tiers, à cloner à côté de ce dossier :

    git clone -b robotflow --depth 1 https://github.com/ElectronicElephant/pybullet_ur5_robotiq
    pip install pybullet numpy matplotlib
    python baseline_pick_place.py --trials 5 --no-gui
    python plots.py

Les CSV sont écrits dans `runs/` à chaque lancement.

## Suite possible

1. Comprendre pourquoi l'effecteur n'atteint pas le flan : comparer position et cible phase par phase, et vérifier le repère `EE_LINK` par rapport au bout de la ventouse.
2. Ajouter un garde-fou : ne pas activer la ventouse tant que l'effecteur n'est pas à moins de 1 cm de sa cible.
3. Une fois la baseline fiable, mesurer son taux de succès sur une grille de masses et de frictions : c'est cette mesure qui justifierait un apprentissage.
4. Seulement ensuite, rendre le flan pliable.

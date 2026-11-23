"""
logger.py — Journalisation des essais en CSV.
=============================================
POURQUOI c'est crucial : le projet precedent affirmait des resultats
(erreurs en mm, taux de reussite) qu'AUCUN fichier ne prouvait. Ici, chaque
essai ecrit une ligne dans un CSV horodatte. Les graphiques (plots.py) sont
ensuite generes A PARTIR de ces CSV. Donc tout chiffre presente sera, par
construction, reproductible et tracable jusqu'a sa source.

Deux fichiers sont produits par session :
  - trials_<horodatage>.csv : une ligne par essai (resume)
  - steps_<horodatage>.csv  : une ligne par pas de temps (trajectoire fine)
"""

import csv
import os
import time
import config as cfg


class RunLogger:
    def __init__(self, tag="baseline"):
        os.makedirs(cfg.RUNS_DIR, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        self.trials_path = os.path.join(cfg.RUNS_DIR, f"trials_{tag}_{stamp}.csv")
        self.steps_path = os.path.join(cfg.RUNS_DIR, f"steps_{tag}_{stamp}.csv")

        # En-tete du fichier "resume par essai"
        self._trials_file = open(self.trials_path, "w", newline="")
        self._trials = csv.writer(self._trials_file)
        self._trials.writerow([
            "trial", "blank_mass", "blank_friction",
            "grasp_success", "place_success",
            "lift_height", "place_error_xy", "duration_s",
        ])

        # En-tete du fichier "trajectoire fine"
        self._steps_file = open(self.steps_path, "w", newline="")
        self._steps = csv.writer(self._steps_file)
        self._steps.writerow([
            "trial", "phase", "t",
            "ee_x", "ee_y", "ee_z",
            "target_x", "target_y", "target_z",
            "tracking_error",
        ])

    def log_step(self, trial, phase, t, ee, target, error):
        self._steps.writerow([
            trial, phase, round(t, 4),
            round(ee[0], 5), round(ee[1], 5), round(ee[2], 5),
            round(target[0], 5), round(target[1], 5), round(target[2], 5),
            round(error, 6),
        ])

    def log_trial(self, trial, mass, friction, grasp_ok, place_ok,
                  lift_height, place_err, duration):
        self._trials.writerow([
            trial, round(mass, 4), round(friction, 3),
            int(grasp_ok), int(place_ok),
            round(lift_height, 4), round(place_err, 4), round(duration, 2),
        ])
        self._trials_file.flush()   # ecrire sur le disque immediatement

    def close(self):
        self._trials_file.close()
        self._steps_file.close()

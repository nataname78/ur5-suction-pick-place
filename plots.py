"""
plots.py — Genere de VRAIS graphiques a partir des CSV.
=======================================================
Contrairement au projet precedent (qui DECRIVAIT des graphiques sans script
pour les produire), ici chaque graphique est genere depuis un CSV reel.

Usage (sur ton PC) :
    python plots.py                       (prend les CSV les plus recents)
    python plots.py --steps steps_xxx.csv --trials trials_xxx.csv

Produit, dans runs/ :
  - fig_tracking_error.png : erreur de suivi de l'effecteur au cours du temps
  - fig_trajectory_xz.png  : la trajectoire de l'effecteur vue de cote (x,z)
  - fig_trial_summary.png  : reussite et precision par essai
"""

import argparse
import glob
import os
import csv
import config as cfg

import matplotlib
matplotlib.use("Agg")   # backend sans ecran : marche partout, ecrit des PNG
import matplotlib.pyplot as plt


def _latest(pattern):
    files = sorted(glob.glob(os.path.join(cfg.RUNS_DIR, pattern)))
    return files[-1] if files else None


def _read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def plot_tracking_error(steps_rows, out):
    plt.figure(figsize=(9, 4))
    # Tracer l'erreur de suivi, une couleur par phase
    phases = {}
    for row in steps_rows:
        phases.setdefault(row["phase"], []).append(
            (float(row["t"]), float(row["tracking_error"]) * 1000)  # en mm
        )
    # On concatene les phases bout a bout sur un axe de temps continu
    t_offset = 0
    for phase, pts in phases.items():
        ts = [t_offset + t for t, _ in pts]
        es = [e for _, e in pts]
        if ts:
            plt.plot(ts, es, label=phase, linewidth=1.5)
            t_offset = ts[-1]
    plt.xlabel("Temps cumule (s)")
    plt.ylabel("Erreur de suivi de l'effecteur (mm)")
    plt.title("Precision de suivi de trajectoire par phase")
    plt.legend(fontsize=8, ncol=4)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=130)
    plt.close()


def plot_trajectory_xz(steps_rows, out):
    plt.figure(figsize=(6, 6))
    xs = [float(r["ee_x"]) for r in steps_rows]
    zs = [float(r["ee_z"]) for r in steps_rows]
    plt.plot(xs, zs, linewidth=1, color="#1f4e79")
    plt.scatter([xs[0]], [zs[0]], c="green", s=60, label="depart", zorder=5)
    plt.scatter([xs[-1]], [zs[-1]], c="red", s=60, label="arrivee", zorder=5)
    plt.xlabel("x (m)  — gauche/droite")
    plt.ylabel("z (m)  — hauteur")
    plt.title("Trajectoire de l'effecteur (vue de cote)")
    plt.axhline(cfg.TABLE_HEIGHT, color="brown", linestyle="--", alpha=0.5, label="dessus de table")
    plt.legend(fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(out, dpi=130)
    plt.close()


def plot_trial_summary(trials_rows, out):
    if not trials_rows:
        return
    trials = [int(r["trial"]) + 1 for r in trials_rows]
    place_err = [float(r["place_error_xy"]) * 1000 for r in trials_rows]
    success = [int(r["place_success"]) for r in trials_rows]

    fig, ax1 = plt.subplots(figsize=(8, 4))
    colors = ["#2e7d32" if s else "#c00000" for s in success]
    ax1.bar(trials, place_err, color=colors, alpha=0.8)
    ax1.set_xlabel("Essai")
    ax1.set_ylabel("Erreur de depose (mm)")
    ax1.set_title("Resultat par essai (vert = reussi, rouge = echoue)")
    ax1.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=130)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", default=None)
    parser.add_argument("--trials", default=None)
    args = parser.parse_args()

    steps_path = args.steps or _latest("steps_*.csv")
    trials_path = args.trials or _latest("trials_*.csv")

    if not steps_path:
        print("Aucun CSV de pas trouve dans runs/. Lance d'abord baseline_pick_place.py.")
        return

    steps_rows = _read_csv(steps_path)
    trials_rows = _read_csv(trials_path) if trials_path else []

    out1 = os.path.join(cfg.RUNS_DIR, "fig_tracking_error.png")
    out2 = os.path.join(cfg.RUNS_DIR, "fig_trajectory_xz.png")
    out3 = os.path.join(cfg.RUNS_DIR, "fig_trial_summary.png")

    plot_tracking_error(steps_rows, out1)
    plot_trajectory_xz(steps_rows, out2)
    plot_trial_summary(trials_rows, out3)

    print("Graphiques generes :")
    for o in (out1, out2, out3):
        print(f"  {o}")


if __name__ == "__main__":
    main()

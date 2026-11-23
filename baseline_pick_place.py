"""
baseline_pick_place.py — LE script principal de la phase 1.
===========================================================
Sequence complete, SANS ML :
  1. Le bras s'approche au-dessus du flan du dessus de la pile.
  2. Il descend jusqu'au contact.
  3. La ventouse aspire (active le vide).
  4. Il souleve le flan.
  5. Il le transporte au-dessus de la zone de depose ("la machine").
  6. Il descend et coupe le vide : le flan est depose.
  7. Il revient en position de repos.

A chaque pas, on enregistre la position de l'effecteur et l'erreur de suivi.
A la fin de chaque essai, on enregistre un resume (reussite, hauteur de
levee, precision de depose, duree).

Lancement (sur ton PC) :
    python baseline_pick_place.py
    python baseline_pick_place.py --trials 5     (pour enchainer 5 essais)
    python baseline_pick_place.py --no-gui       (sans fenetre, plus rapide)
"""

import argparse
import time
import numpy as np
import pybullet as p

import config as cfg
import scene as scene_mod
from robot import UR5Robot
from suction import SuctionGripper
from logger import RunLogger


def smooth(a, b, alpha):
    """Interpolation douce entre deux points 3D (easing cosinus).
    alpha va de 0 a 1 ; le mouvement accelere puis ralentit, sans a-coup."""
    e = 0.5 * (1 - np.cos(np.pi * alpha))
    return [a[i] + e * (b[i] - a[i]) for i in range(3)]


def move(robot, logger, trial, phase, start, end, duration, suction=None):
    """
    Deplace l'effecteur de 'start' a 'end' en 'duration' secondes,
    en enregistrant chaque pas. Si une ventouse tient un flan, il suit.

    On envoie la consigne PUIS on laisse la simulation avancer : le bras a
    ainsi le temps de rattraper sa cible a chaque pas (sinon l'erreur de
    suivi s'accumule et le mouvement devient n'importe quoi).
    """
    n = int(duration * cfg.SIM_HZ)
    for step in range(n):
        alpha = (step + 1) / n
        target = smooth(start, end, alpha)
        robot.set_target(target)
        p.stepSimulation()

        ee = robot.ee_position()
        err = float(np.linalg.norm(ee - np.array(target)))
        logger.log_step(trial, phase, step / cfg.SIM_HZ, ee, target, err)

        if cfg.REAL_TIME and cfg.USE_GUI:
            time.sleep(1.0 / cfg.SIM_HZ)

    # Petite phase de convergence : on maintient la cible finale quelques pas
    # pour laisser le bras s'y poser precisement avant de passer a la suite.
    for _ in range(int(0.4 * cfg.SIM_HZ)):
        robot.set_target(end)
        p.stepSimulation()
        if cfg.REAL_TIME and cfg.USE_GUI:
            time.sleep(1.0 / cfg.SIM_HZ)
    return end   # la nouvelle position "courante"


def settle(seconds):
    """Laisse la simulation tourner sur place (stabilisation)."""
    for _ in range(int(seconds * cfg.SIM_HZ)):
        p.stepSimulation()
        if cfg.REAL_TIME and cfg.USE_GUI:
            time.sleep(1.0 / cfg.SIM_HZ)


def run_one_trial(robot, gripper, scene, logger, trial):
    """Execute une sequence pick-and-place complete. Renvoie un dict de resultats."""
    t0 = time.time()

    # Le flan a prendre = celui du dessus de la pile
    target_blank = scene["stack"][-1]
    blank_pos, _ = p.getBasePositionAndOrientation(target_blank)
    blank_pos = np.array(blank_pos)

    # Points cles de la trajectoire (tous a la verticale du flan / de la cible)
    above_blank = [blank_pos[0], blank_pos[1], blank_pos[2] + 0.15]
    at_blank    = [blank_pos[0], blank_pos[1], blank_pos[2] + 0.01]
    lifted      = [blank_pos[0], blank_pos[1], blank_pos[2] + 0.20]
    above_place = [cfg.PLACE_TARGET[0], cfg.PLACE_TARGET[1], cfg.PLACE_TARGET[2] + 0.20]
    at_place    = [cfg.PLACE_TARGET[0], cfg.PLACE_TARGET[1], cfg.PLACE_TARGET[2] + cfg.BLANK_THICK]

    cur = robot.ee_position().tolist()

    # 1. Approche
    cur = move(robot, logger, trial, "approach", cur, above_blank, cfg.T_APPROACH)
    # 2. Descente
    cur = move(robot, logger, trial, "descend", cur, at_blank, cfg.T_DESCEND)
    # 3. Aspiration
    settle(0.3)
    grasp_ok = gripper.activate(scene["stack"])
    # 4. Levee
    cur = move(robot, logger, trial, "lift", cur, lifted, cfg.T_LIFT, suction=gripper)

    # Verifier que le flan a bien ete souleve (sa hauteur a augmente)
    lifted_pos, _ = p.getBasePositionAndOrientation(target_blank)
    lift_height = lifted_pos[2] - blank_pos[2]

    # 5. Transport
    cur = move(robot, logger, trial, "carry", cur, above_place, cfg.T_CARRY, suction=gripper)
    # 6. Descente + depose
    cur = move(robot, logger, trial, "lower", cur, at_place, cfg.T_LOWER, suction=gripper)
    gripper.release()
    settle(0.5)

    # Mesurer la precision de depose (distance horizontale a la cible)
    placed_pos, _ = p.getBasePositionAndOrientation(target_blank)
    place_err = float(np.linalg.norm(
        np.array(placed_pos[:2]) - np.array(cfg.PLACE_TARGET[:2])
    ))
    place_ok = (lift_height > 0.05) and (place_err < 0.05)

    # 7. Retour au repos
    move(robot, logger, trial, "return", cur, above_blank, cfg.T_RETURN)

    duration = time.time() - t0
    logger.log_trial(trial, cfg.BLANK_MASS, cfg.BLANK_FRICTION,
                     grasp_ok, place_ok, lift_height, place_err, duration)

    # Retirer le flan pris de la pile (il a ete depose ailleurs)
    if target_blank in scene["stack"]:
        scene["stack"].remove(target_blank)

    return {
        "grasp_ok": grasp_ok, "place_ok": place_ok,
        "lift_height": lift_height, "place_err": place_err,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=1, help="nombre d'essais a enchainer")
    parser.add_argument("--no-gui", action="store_true", help="lancer sans fenetre")
    args = parser.parse_args()

    if args.no_gui:
        cfg.USE_GUI = False

    # Connexion au moteur physique : GUI (fenetre) ou DIRECT (invisible)
    p.connect(p.GUI if cfg.USE_GUI else p.DIRECT)
    if cfg.USE_GUI:
        p.resetDebugVisualizerCamera(
            cameraDistance=1.4, cameraYaw=50, cameraPitch=-35,
            cameraTargetPosition=[0, cfg.TABLE_CENTER_Y, cfg.TABLE_HEIGHT],
        )

    scene = scene_mod.build_scene()
    robot = UR5Robot()
    gripper = SuctionGripper(robot)
    logger = RunLogger(tag="baseline")

    settle(cfg.T_SETTLE)

    n_trials = min(args.trials, cfg.STACK_COUNT)
    results = []
    for trial in range(n_trials):
        if not scene["stack"]:
            print("Pile vide, arret.")
            break
        print(f"\n=== Essai {trial + 1}/{n_trials} ===")
        res = run_one_trial(robot, gripper, scene, logger, trial)
        results.append(res)
        print(f"  prise={'OK' if res['grasp_ok'] else 'ECHEC'}  "
              f"depose={'OK' if res['place_ok'] else 'ECHEC'}  "
              f"levee={res['lift_height']*1000:.0f}mm  "
              f"erreur_depose={res['place_err']*1000:.0f}mm")

    logger.close()

    n_ok = sum(r["place_ok"] for r in results)
    print(f"\n--- Bilan : {n_ok}/{len(results)} essais reussis ---")
    print(f"CSV ecrits dans : {cfg.RUNS_DIR}")
    print(f"  {logger.trials_path}")
    print(f"  {logger.steps_path}")

    if cfg.USE_GUI:
        print("\nFerme la fenetre ou Ctrl+C pour quitter.")
        try:
            while p.isConnected():
                robot.hold()
                p.stepSimulation()
                time.sleep(1.0 / cfg.SIM_HZ)
        except KeyboardInterrupt:
            pass
    p.disconnect()


if __name__ == "__main__":
    main()

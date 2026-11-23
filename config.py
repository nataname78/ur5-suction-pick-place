"""
config.py — Tous les parametres du projet au meme endroit.
==========================================================
Pourquoi un fichier de config separe ?
  Le code de l'ancien projet avait des nombres "en dur" disperses partout
  (0.55 ici, 0.60 la, des angles a deux endroits incoherents...). C'est la
  porte ouverte aux bugs. Ici, TOUT parametre reglable vit dans ce fichier.
  Si on veut changer la taille du flan ou la hauteur de la table, on touche
  UN seul endroit.

Repere de coordonnees PyBullet (a retenir une fois pour toutes) :
  - x : gauche (-) / droite (+)
  - y : profondeur (avant/arriere)
  - z : hauteur (le haut, c'est +z). Le sol est a z=0.
  - Les distances sont en METRES. Les angles en RADIANS.
"""

import os
import math

# ─────────────────────────────────────────────────────────
#  CHEMINS (ou trouver les fichiers du robot)
# ─────────────────────────────────────────────────────────
# Dossier ou se trouve CE fichier (cardboard_robot/)
HERE = os.path.dirname(os.path.abspath(__file__))
# Dossier parent, ou se trouve le depot du robot
PROJECT_ROOT = os.path.dirname(HERE)

# Le depot tiers qui contient l'UR5 et ses meshes
UR5_REPO_DIR = os.path.join(PROJECT_ROOT, "pybullet_ur5_robotiq")
# On utilise l'URDF du bras AVEC pince Robotiq : c'est le seul dont TOUS les
# meshes existent dans le depot (ur5.urdf seul reclame des .dae absents).
UR5_URDF = os.path.join(UR5_REPO_DIR, "urdf", "ur5_robotiq_85.urdf")

# Ou ecrire les sorties (CSV + graphiques)
RUNS_DIR = os.path.join(HERE, "runs")

# ─────────────────────────────────────────────────────────
#  SIMULATION
# ─────────────────────────────────────────────────────────
SIM_HZ = 240            # nombre de pas de simulation par seconde (standard PyBullet)
GRAVITY = -9.81         # m/s^2, vers le bas
USE_GUI = True          # True = fenetre visible (sur TON PC) ; False = invisible (serveur)
REAL_TIME = True        # True = ralentit a la vitesse reelle pour que l'oeil suive

# ─────────────────────────────────────────────────────────
#  TABLE (un simple bloc fixe qui sert de plan de travail)
# ─────────────────────────────────────────────────────────
# IMPORTANT : le robot est pose AU SOL (z=0). La table est BASSE et placee
# DEVANT lui, pas sous lui. Un UR5 deploye fait ~0.85 m : il faut donc une
# table basse a portee de son bras qui se penche en avant.
TABLE_HEIGHT = 0.20      # dessus de table a 20 cm du sol (table basse)
TABLE_HALF = [0.35, 0.30, TABLE_HEIGHT / 2]   # demi-dimensions du bloc table
TABLE_CENTER_Y = 0.45    # la table est centree a 45 cm DEVANT le robot (axe +y)

# ─────────────────────────────────────────────────────────
#  FLAN DE CARTON (le "die-cut blank" de la video)
# ─────────────────────────────────────────────────────────
# Pour l'instant, en phase 1, le flan est une simple plaque rectangulaire.
# On le rendra "pliable" (multi-panneaux) en phase 2.
BLANK_LENGTH = 0.18     # longueur du flan (axe x), en m
BLANK_WIDTH  = 0.14     # largeur du flan (axe y), en m
BLANK_THICK  = 0.004    # epaisseur du carton, en m
BLANK_MASS   = 0.08     # masse d'un flan, en kg (~80 g, realiste pour du carton)
BLANK_FRICTION = 1.0    # coefficient de friction (le carton accroche bien)

# ─────────────────────────────────────────────────────────
#  PILE DE FLANS (la stack a cote de la machine)
# ─────────────────────────────────────────────────────────
# La pile et la zone de depose sont sur la table, DEVANT le robot, dans sa
# zone de travail fiable (distance 0.45-0.60 m de la base au sol).
STACK_COUNT = 5                          # nombre de flans empiles au depart
STACK_CENTER = [-0.12, TABLE_CENTER_Y, 0]  # devant-gauche, sur la table

# Position ou on veut DEPOSER le flan apres l'avoir pris (la "machine").
# A cote de la pile, sur la meme table, donc a portee.
PLACE_TARGET = [0.15, TABLE_CENTER_Y, TABLE_HEIGHT + 0.01]

# ─────────────────────────────────────────────────────────
#  ROBOT UR5
# ─────────────────────────────────────────────────────────
# Base du bras : POSEE AU SOL (z=0), a l'origine. La table de travail est
# devant lui (en +y). C'est la disposition d'une vraie cellule robotique.
ROBOT_BASE_POS = [0.0, 0.0, 0.0]
ROBOT_BASE_ORN = [0, 0, 0]      # orientation (Euler), bras droit

# Indices des articulations du bras dans l'URDF ur5_robotiq_85.urdf.
# VERIFIE en parsant le fichier : les 6 articulations du bras UR5 sont aux
# indices 0 a 5 (la pince Robotiq vient apres, indices 7+). L'effecteur
# "ee_link" est au bout du joint d'index 6, c'est le link d'index 7.
# Ne pas modifier sans re-verifier l'URDF.
ARM_JOINTS = [0, 1, 2, 3, 4, 5]
EE_LINK = 7                     # le link "ee_link", ou on attachera la ventouse

# Posture de repos (angles des 6 articulations, en radians).
# Reglee pour que le bras pointe vers l'AVANT (+y, vers la table) et plonge
# vers le bas, pret a saisir. Le 1er angle (base) = 0 garde le bras face a +y.
# Si le bras pointait du mauvais cote, c'est ce 1er angle qu'il faudrait
# changer (ex: math.pi pour le retourner).
REST_POSES = [0.0, -1.0, 1.2, -1.4, -math.pi/2, 0.0]

# Limites articulaires de l'UR5 (donnees constructeur), pour guider l'IK.
JOINT_LOWER = [-2*math.pi] * 6
JOINT_UPPER = [ 2*math.pi] * 6
JOINT_RANGE = [ 4*math.pi] * 6

# Force max des moteurs (Nm). Assez pour tenir le bras sans le rendre "mou".
MAX_FORCE = 300
POSITION_GAIN = 0.15            # "raideur" du suivi de consigne

# ─────────────────────────────────────────────────────────
#  VENTOUSE (suction gripper)
# ─────────────────────────────────────────────────────────
# Distance max entre la ventouse et un flan pour pouvoir "aspirer".
# Au-dela, le vide ne prend pas (comme dans la vraie vie).
SUCTION_CONTACT_DIST = 0.02     # 2 cm
# Force de tenue de la contrainte de succion. C'est LA grandeur que le ML
# apprendra a regler plus tard. En baseline, on la fixe.
SUCTION_HOLD_FORCE = 50         # N

# ─────────────────────────────────────────────────────────
#  DUREES DES PHASES (en secondes)
# ─────────────────────────────────────────────────────────
T_SETTLE   = 1.0    # laisser la scene se stabiliser au demarrage
T_APPROACH = 2.0    # descendre au-dessus du flan
T_DESCEND  = 1.5    # descendre au contact
T_LIFT     = 2.0    # soulever le flan
T_CARRY    = 2.5    # transporter vers la zone de depose
T_LOWER    = 1.5    # redescendre pour deposer
T_RETURN   = 2.5    # revenir en position de repos

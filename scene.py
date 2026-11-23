"""
scene.py — Construit le monde de la simulation.
===============================================
Une "scene" en simulation, c'est tout ce qui n'est pas le robot :
  - le sol
  - la table (plan de travail)
  - la pile de flans de carton
  - (la zone de depose est juste une coordonnee, pas un objet physique)

Chaque objet cree renvoie un "id" (un numero entier) que PyBullet nous donne.
On garde ces ids pour pouvoir parler aux objets plus tard (les bouger, lire
leur position, etc.).
"""

import pybullet as p
import pybullet_data
import config as cfg


def build_world():
    """Cree le sol et regle la gravite. Renvoie l'id du sol."""
    # setAdditionalSearchPath dit a PyBullet ou trouver ses modeles de base
    # (le sol "plane.urdf" est fourni avec PyBullet).
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, cfg.GRAVITY)
    p.setTimeStep(1.0 / cfg.SIM_HZ)
    plane_id = p.loadURDF("plane.urdf")
    return plane_id


def build_table():
    """
    Cree la table : un simple bloc rectangulaire FIXE.
    'Fixe' = masse 0 : la gravite ne l'affecte pas, elle ne tombe pas.
    Renvoie l'id de la table.
    """
    col = p.createCollisionShape(p.GEOM_BOX, halfExtents=cfg.TABLE_HALF)
    vis = p.createVisualShape(
        p.GEOM_BOX, halfExtents=cfg.TABLE_HALF,
        rgbaColor=[0.55, 0.40, 0.28, 1.0],   # marron table
    )
    # La table est placee DEVANT le robot (a TABLE_CENTER_Y en +y), et son
    # centre est a mi-hauteur pour que son DESSUS soit a z = TABLE_HEIGHT.
    table_id = p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=col,
        baseVisualShapeIndex=vis,
        basePosition=[0, cfg.TABLE_CENTER_Y, cfg.TABLE_HEIGHT / 2],
    )
    p.changeDynamics(table_id, -1, lateralFriction=1.0)
    return table_id


def _make_blank(x, y, z, color):
    """
    Cree UN flan de carton (une plaque rectangulaire) a la position donnee.
    En phase 1 c'est une plaque rigide ; on la rendra pliable en phase 2.
    Renvoie l'id du flan.
    """
    half = [cfg.BLANK_LENGTH / 2, cfg.BLANK_WIDTH / 2, cfg.BLANK_THICK / 2]
    col = p.createCollisionShape(p.GEOM_BOX, halfExtents=half)
    vis = p.createVisualShape(p.GEOM_BOX, halfExtents=half, rgbaColor=color)
    blank_id = p.createMultiBody(
        baseMass=cfg.BLANK_MASS,
        baseCollisionShapeIndex=col,
        baseVisualShapeIndex=vis,
        basePosition=[x, y, z],
    )
    # Friction elevee + un peu d'amortissement : les flans ne glissent pas
    # tout seuls et la pile reste stable.
    p.changeDynamics(blank_id, -1,
                     lateralFriction=cfg.BLANK_FRICTION,
                     spinningFriction=0.002,
                     restitution=0.0)
    return blank_id


def build_stack():
    """
    Empile cfg.STACK_COUNT flans les uns sur les autres sur la table.
    Renvoie la liste des ids, du BAS vers le HAUT.
    Le dernier de la liste est celui du dessus = celui qu'on prendra en premier.
    """
    cx, cy, _ = cfg.STACK_CENTER
    ids = []
    # Couleurs alternees pour bien voir les flans separes a l'ecran
    palette = [
        [0.80, 0.66, 0.45, 1.0],
        [0.85, 0.72, 0.52, 1.0],
    ]
    for i in range(cfg.STACK_COUNT):
        # Chaque flan est pose au-dessus du precedent.
        # On ajoute un mince espace pour eviter qu'ils se chevauchent au depart.
        z = cfg.TABLE_HEIGHT + cfg.BLANK_THICK / 2 + i * (cfg.BLANK_THICK + 0.0005)
        color = palette[i % 2]
        ids.append(_make_blank(cx, cy, z, color))
    return ids


def build_scene():
    """
    Construit toute la scene d'un coup et renvoie un dictionnaire d'ids,
    pratique a passer aux autres modules.
    """
    plane = build_world()
    table = build_table()
    stack = build_stack()
    return {
        "plane": plane,
        "table": table,
        "stack": stack,        # liste, [-1] = flan du dessus
    }

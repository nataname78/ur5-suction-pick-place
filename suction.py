"""
suction.py — Le prehenseur a ventouses.
========================================
Comment on modelise une ventouse en simulation (technique standard) :

  Une vraie ventouse aspire l'air pour creer une depression qui colle l'objet.
  On NE simule PAS l'air (trop couteux). A la place :

    activate() : SI la ventouse touche (ou frole) un flan, on cree une
                 contrainte rigide entre l'effecteur et ce flan. Le flan
                 "suit" alors le bout du bras, comme s'il etait aspire.

    release()  : on supprime la contrainte. Le flan retombe (gravite).

  C'est honnete physiquement : on verifie le CONTACT avant d'aspirer (on ne
  peut pas aspirer dans le vide), et la force de tenue est limitee (un flan
  trop lourd "decrocherait", ce que le ML apprendra a anticiper).

Difference avec l'ancien code : lui collait le panneau en aveugle, sans
verifier le contact ni modeliser l'activation/desactivation du vide.
"""

import pybullet as p
import numpy as np
import config as cfg


class SuctionGripper:
    def __init__(self, robot):
        self.robot = robot
        self.constraint = None     # l'id de la contrainte quand le vide est actif
        self.held_object = None    # l'id du flan tenu, ou None

    def is_holding(self):
        return self.constraint is not None

    def _find_object_in_reach(self, candidate_ids):
        """
        Cherche, parmi les flans candidats, le plus proche de la ventouse
        ET assez proche pour etre aspire (< SUCTION_CONTACT_DIST).
        Renvoie (id_du_flan, distance) ou (None, None) si rien a portee.
        """
        ee = self.robot.ee_position()
        best_id, best_dist = None, None
        for obj_id in candidate_ids:
            pos, _ = p.getBasePositionAndOrientation(obj_id)
            dist = np.linalg.norm(ee - np.array(pos))
            if dist <= cfg.SUCTION_CONTACT_DIST and (best_dist is None or dist < best_dist):
                best_id, best_dist = obj_id, dist
        return best_id, best_dist

    def activate(self, candidate_ids):
        """
        Tente d'aspirer un flan a portee. Renvoie True si la prise reussit.
        candidate_ids : liste des flans qu'on a le droit de saisir.
        """
        if self.is_holding():
            return True  # deja en train de tenir quelque chose

        obj_id, dist = self._find_object_in_reach(candidate_ids)
        if obj_id is None:
            return False  # rien a portee : le vide ne prend pas

        # On cree une contrainte FIXE entre l'effecteur et le flan.
        # Cela revient a "coller" le flan au bout du bras (le vide est actif).
        self.constraint = p.createConstraint(
            parentBodyUniqueId=self.robot.id,
            parentLinkIndex=cfg.EE_LINK,
            childBodyUniqueId=obj_id,
            childLinkIndex=-1,
            jointType=p.JOINT_FIXED,
            jointAxis=[0, 0, 0],
            parentFramePosition=[0, 0, 0.01],   # juste sous le poignet
            childFramePosition=[0, 0, 0],
        )
        # La force max de la contrainte = force de tenue de la ventouse.
        # Si le flan etait trop lourd, la contrainte "lacherait".
        p.changeConstraint(self.constraint, maxForce=cfg.SUCTION_HOLD_FORCE)
        self.held_object = obj_id
        return True

    def release(self):
        """Coupe le vide : supprime la contrainte, le flan est relache."""
        if self.constraint is not None:
            p.removeConstraint(self.constraint)
            self.constraint = None
            self.held_object = None

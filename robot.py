"""
robot.py — Le bras UR5 et son pilotage.
=======================================
Ce module gere TOUT ce qui concerne le bras :
  - le charger dans la simulation
  - l'empecher de tomber (le maintenir en position)
  - le deplacer vers une position 3D voulue (via la cinematique inverse)
  - lire ou se trouve son effecteur (le bout du bras)

RAPPEL des termes :
  - Effecteur (end-effector) : le bout du bras, la ou on mettra la ventouse.
  - Cinematique inverse (IK) : on dit "je veux le bout du bras ICI (x,y,z)"
    et l'IK calcule les 6 angles d'articulation pour y arriver.
"""

import pybullet as p
import numpy as np
import config as cfg


class UR5Robot:
    def __init__(self):
        """Charge le bras et le met en position de repos, statique."""
        # PyBullet doit savoir ou trouver les meshes (.dae/.stl) references
        # par l'URDF via des chemins relatifs "../meshes/...". On ajoute donc
        # le dossier du depot UR5 a son chemin de recherche AVANT loadURDF.
        p.setAdditionalSearchPath(cfg.UR5_REPO_DIR)
        # useFixedBase=True : la base du bras est boulonnee, elle ne bouge pas.
        self.id = p.loadURDF(
            cfg.UR5_URDF,
            basePosition=cfg.ROBOT_BASE_POS,
            baseOrientation=p.getQuaternionFromEuler(cfg.ROBOT_BASE_ORN),
            useFixedBase=True,
            flags=p.URDF_ENABLE_CACHED_GRAPHICS_SHAPES,
        )

        # Retirer l'amortissement parasite des articulations (mouvement plus net)
        for j in range(p.getNumJoints(self.id)):
            p.changeDynamics(self.id, j, linearDamping=0, angularDamping=0)

        # Placer chaque articulation a sa posture de repos ET activer le moteur
        # en POSITION_CONTROL tout de suite : sans ca, le bras s'effondre sous
        # la gravite des la premiere image (c'etait un bug de l'ancien code).
        for idx, j in enumerate(cfg.ARM_JOINTS):
            angle = cfg.REST_POSES[idx]
            p.resetJointState(self.id, j, angle)
            p.setJointMotorControl2(
                self.id, j,
                controlMode=p.POSITION_CONTROL,
                targetPosition=angle,
                force=cfg.MAX_FORCE,
                positionGain=cfg.POSITION_GAIN,
                velocityGain=1.0,
            )

        # La pince Robotiq a ses propres articulations (au-dela du bras).
        # On les maintient a 0 (pince stable, ni molle ni agitee). On ne s'en
        # sert pas en phase 1 : c'est la ventouse qui fait la prise.
        n_joints = p.getNumJoints(self.id)
        for j in range(n_joints):
            if j not in cfg.ARM_JOINTS:
                info = p.getJointInfo(self.id, j)
                joint_type = info[2]
                # On ne pilote que les articulations mobiles (pas les fixes)
                if joint_type != p.JOINT_FIXED:
                    p.setJointMotorControl2(
                        self.id, j,
                        controlMode=p.POSITION_CONTROL,
                        targetPosition=0.0,
                        force=20,
                    )

    # ─────────────────────────────────────────────────────
    #  LECTURE
    # ─────────────────────────────────────────────────────
    def ee_position(self):
        """Renvoie la position (x,y,z) actuelle de l'effecteur."""
        state = p.getLinkState(self.id, cfg.EE_LINK, computeForwardKinematics=True)
        return np.array(state[4])   # state[4] = position du repere du link dans le monde

    def joint_angles(self):
        """Renvoie les 6 angles actuels des articulations du bras."""
        states = p.getJointStates(self.id, cfg.ARM_JOINTS)
        return np.array([s[0] for s in states])

    # ─────────────────────────────────────────────────────
    #  COMMANDE
    # ─────────────────────────────────────────────────────
    def _solve_ik(self, target_pos, target_orn=None):
        """
        Cinematique inverse : transforme une cible (x,y,z) en 6 angles.
        Par defaut, la ventouse pointe vers le BAS (pour saisir par le dessus).
        """
        if target_orn is None:
            # Quaternion correspondant a "pointer vers le bas"
            target_orn = p.getQuaternionFromEuler([0, np.pi, 0])
        angles = p.calculateInverseKinematics(
            self.id, cfg.EE_LINK,
            targetPosition=target_pos,
            targetOrientation=target_orn,
            lowerLimits=cfg.JOINT_LOWER,
            upperLimits=cfg.JOINT_UPPER,
            jointRanges=cfg.JOINT_RANGE,
            restPoses=cfg.REST_POSES,
            maxNumIterations=200,
            residualThreshold=1e-5,
        )
        # calculateInverseKinematics renvoie un angle PAR articulation mobile ;
        # on ne garde que les 6 du bras.
        return angles[:len(cfg.ARM_JOINTS)]

    def set_target(self, target_pos, target_orn=None):
        """Envoie une consigne de position aux moteurs (UN pas, non bloquant)."""
        angles = self._solve_ik(target_pos, target_orn)
        for i, j in enumerate(cfg.ARM_JOINTS):
            p.setJointMotorControl2(
                self.id, j,
                controlMode=p.POSITION_CONTROL,
                targetPosition=angles[i],
                force=cfg.MAX_FORCE,
                positionGain=cfg.POSITION_GAIN,
                velocityGain=1.0,
            )

    def hold(self):
        """Maintient le bras la ou il est (renvoie sa cible actuelle a l'IK)."""
        self.set_target(self.ee_position())

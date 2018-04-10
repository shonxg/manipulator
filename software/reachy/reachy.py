import os
import time

from numpy import sum
from threading import Thread
from functools import partial
from collections import deque

from pypot.creatures import AbstractPoppyCreature
from pypot.vrep import from_vrep, VrepConnectionError

from .primitives import (Record, Play,
                         GotoRest, Idle, TiringDemo,
                         TurnCompliant)
from .ik import IkChain


class Reachy(AbstractPoppyCreature):
    @classmethod
    def setup(cls, robot):
        robot._primitive_manager._filter = partial(sum, axis=0)

        for m in robot.motors:
            m.moving_speed = 50

        robot.attach_primitive(TiringDemo(robot), 'tiring_demo')
        robot.attach_primitive(TurnCompliant(robot), 'turn_compliant')
        robot.attach_primitive(GotoRest(robot), 'goto_rest')
        robot.attach_primitive(Idle(robot), 'idle')

        robot.attach_primitive(Record(robot), 'record')
        robot.attach_primitive(Play(robot), 'play')

        if robot.simulated:
            vrep_io = robot._controllers[0].io
            robot.is_colliding = lambda: vrep_io.get_collision_state('Collision')

            robot.last_collision = None
            robot.recent_collisions = deque([], 10)

            def did_collide():
                while True:
                    if robot.is_colliding:
                        t = time.time()
                        robot.last_collision = t
                        robot.recent_collisions.append(t)
                    time.sleep(0.02)

            t = Thread(target=did_collide)
            t.daemon = True
            t.start()

        robot.ik_chain = IkChain(robot, tip=[0, 0, -0.02409])


def Leachy(*args, **kwargs):
    if 'config' not in kwargs and 'simulator' not in kwargs:
        config = os.path.join(os.path.dirname(__file__),
                              'configuration', 'leachy.json')
        kwargs['config'] = config
        robot = Reachy(*args, **kwargs)

    if 'simulator' in kwargs:
        config = os.path.join(os.path.dirname(__file__),
                              'configuration', 'leachy.json')
        scene = os.path.join(os.path.dirname(__file__),
                             'vrep-scene', 'leachy.ttt')
        try:
            robot = from_vrep(config, '127.0.0.1', 19997, scene)
        except VrepConnectionError:
            raise IOError('Connection to V-REP failed!')

    robot.urdf_file = robot.urdf_file.replace('reachy.urdf', 'leachy.urdf')
    robot.ik_chain = IkChain(robot, tip=[0, 0, -0.8])
    return robot

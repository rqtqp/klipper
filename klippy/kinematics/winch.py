# Code for handling the kinematics of cable winch robots
#
# Copyright (C) 2018-2021  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging
import stepper, mathutil

class WinchKinematics:
    def __init__(self, toolhead, config):
        # Setup steppers at each anchor
        self.steppers = []
        self.anchors = []
        for i in range(26):
            name = 'stepper_' + chr(ord('a') + i)
            if i >= 3 and not config.has_section(name):
                break
            stepper_config = config.getsection(name)
            s = stepper.PrinterStepper(stepper_config)
            self.steppers.append(s)
            a = tuple([stepper_config.getfloat('anchor_' + n) for n in 'xyz'])
            self.anchors.append(a)
            s.setup_itersolve('winch_stepper_alloc', *a)
            s.set_trapq(toolhead.get_trapq())
            toolhead.register_step_generator(s.generate_steps)
        # Setup boundary checks
        acoords = list(zip(*self.anchors))
        self.axes_min = toolhead.Coord(*[min(a) for a in acoords], e=0.)
        self.axes_max = toolhead.Coord(*[max(a) for a in acoords], e=0.)
        self.set_position([0., 0., 0.], ())

        # added by me
        self.logger = logging.getLogger(__name__)
        self.limits = [(-500.0, 500.0)] * len(self.steppers)
        # // added by me

    def get_steppers(self):
        return list(self.steppers)
    def calc_position(self, stepper_positions):
        # Use only first three steppers to calculate cartesian position
        pos = [stepper_positions[rail.get_name()] for rail in self.steppers[:3]]
        return mathutil.trilateration(self.anchors[:3], [sp*sp for sp in pos])
    def set_position(self, newpos, homing_axes):
        for s in self.steppers:
            s.set_position(newpos)
    def home(self, homing_state):
        # XXX - homing not implemented
        homing_state.set_axes([0, 1, 2])
        homing_state.set_homed_position([0., 0., 0.])

    # added by me
    def _check_endstops(self, move):
        end_pos = move.end_pos
        for i in range(len(self.steppers)):
            self.logger.debug(f"Checking endstop for axis {i}: end_pos={end_pos[i]}, limits={self.limits[i]}")
            if (move.axes_d[i] and (end_pos[i] < self.limits[i][0] or end_pos[i] > self.limits[i][1])):
                if self.limits[i][0] > self.limits[i][1]:
                    raise move.move_error("Must home winch first")
                raise move.move_error()
    # // added by me

    def check_move(self, move):
        
        # added by me
        limits = self.limits
        end_pos = move.end_pos
        for i in range(len(self.anchors)):
            if end_pos[i] < limits[i][0] or end_pos[i] > limits[i][1]:
                self._check_endstops(move)
        # //added by me

        # XXX - boundary checks and speed limits not implemented
        pass
    def get_status(self, eventtime):
        # XXX - homed_checks and rail limits not implemented
        return {
            'homed_axes': 'xyz',
            'axis_minimum': self.axes_min,
            'axis_maximum': self.axes_max,
        }

def load_kinematics(toolhead, config):
    return WinchKinematics(toolhead, config)

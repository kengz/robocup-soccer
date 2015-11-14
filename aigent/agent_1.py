#!/usr/bin/env python

from soccerpy.agent import Agent as baseAgent
from soccerpy.world_model import WorldModel

# methods from actionHandler are
# CATCH = "catch"(rel_direction)
# CHANGE_VIEW = "change_view"
# DASH = "dash"(power)
# KICK = "kick"(power, rel_direction)
# MOVE = "move"(x,y) only pregame
# SAY = "say"(you_can_try_cursing)
# SENSE_BODY = "sense_body"
# TURN = "turn"(rel_degrees in 360)
# TURN_NECK = "turn_neck"(rel_direction)

class Agent(baseAgent):
    """
    The extended Agent class with specific heuritics
    """

    def think(self):
        """
        Performs a single step of thinking for our agent.  Gets called on every
        iteration of our think loop.
        """

        # DEBUG:  tells us if a thread dies
        if not self.__think_thread.is_alive() or not self.__msg_thread.is_alive():
            raise Exception("A thread died.")

        # take places on the field by uniform number
        if not self.in_kick_off_formation:

            # used to flip x coords for other side
            side_mod = 1
            if self.wm.side == WorldModel.SIDE_R:
                side_mod = -1

                if self.wm.uniform_number == 1:
                    self.wm.teleport_to_point((-5 * side_mod, 30))
                elif self.wm.uniform_number == 2:
                    self.wm.teleport_to_point((-40 * side_mod, 15))
                elif self.wm.uniform_number == 3:
                    self.wm.teleport_to_point((-40 * side_mod, 00))
                elif self.wm.uniform_number == 4:
                    self.wm.teleport_to_point((-40 * side_mod, -15))
                elif self.wm.uniform_number == 5:
                    self.wm.teleport_to_point((-5 * side_mod, -30))
                elif self.wm.uniform_number == 6:
                    self.wm.teleport_to_point((-20 * side_mod, 20))
                elif self.wm.uniform_number == 7:
                    self.wm.teleport_to_point((-20 * side_mod, 0))
                elif self.wm.uniform_number == 8:
                    self.wm.teleport_to_point((-20 * side_mod, -20))
                elif self.wm.uniform_number == 9:
                    self.wm.teleport_to_point((-10 * side_mod, 0))
                elif self.wm.uniform_number == 10:
                    self.wm.teleport_to_point((-10 * side_mod, 20))
                elif self.wm.uniform_number == 11:
                    self.wm.teleport_to_point((-10 * side_mod, -20))

                    self.in_kick_off_formation = True

                    return

        # determine the enemy goal position
        goal_pos = None
        if self.wm.side == WorldModel.SIDE_R:
            goal_pos = (-55, 0)
        else:
            goal_pos = (55, 0)

        # kick off!
        if self.wm.is_before_kick_off():
            # player 9 takes the kick off
            if self.wm.uniform_number == 9:
                if self.wm.is_ball_kickable():
                    # kick with 100% extra effort at enemy goal
                    self.wm.kick_to(goal_pos, 1.0)
                else:
                    # move towards ball
                    if self.wm.ball is not None:
                        if (self.wm.ball.direction is not None and
                            -7 <= self.wm.ball.direction <= 7):
                        self.wm.ah.dash(50)
                    else:
                        self.wm.turn_body_to_point((0, 0))

                # turn to ball if we can see it, else face the enemy goal
                if self.wm.ball is not None:
                    self.wm.turn_neck_to_object(self.wm.ball)

                    return

        # attack!
        else:
            # find the ball
            if self.wm.ball is None or self.wm.ball.direction is None:
                self.wm.ah.turn(30)

                return

            # kick it at the enemy goal
            if self.wm.is_ball_kickable():
                self.wm.kick_to(goal_pos, 1.0)
                return
            else:
                # move towards ball
                if -7 <= self.wm.ball.direction <= 7:
                    self.wm.ah.dash(65)
                else:
                    # face ball
                    self.wm.ah.turn(self.wm.ball.direction / 2)

                    return

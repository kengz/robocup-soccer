#!/usr/bin/env python

import random
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

# potentially useful from aima
# learning.py
# mdp
# 

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
            print "the side is", self.wm.side

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
        # self.enemy_goal_pos = None
        # self.own_goal_pos = None
        if self.wm.side == WorldModel.SIDE_R:
            self.enemy_goal_pos = (-55, 0)
            self.own_goal_pos = (55, 0)
        else:
            self.enemy_goal_pos = (55, 0)
            self.own_goal_pos = (-55, 0)

        if not self.wm.is_before_kick_off() or self.wm.is_kick_off_us() or self.wm.is_playon():
            # The main decision loop
            return self.decisionLoop()

        # # kick off!
        # if self.wm.is_before_kick_off():
        #     # player 9 takes the kick off
        #     if self.wm.uniform_number == 9:
        #         if self.wm.is_ball_kickable():
        #             # kick with 100% extra effort at enemy goal
        #             self.wm.kick_to(self.enemy_goal_pos, 1.0)
        #         else:
        #             # move towards ball
        #             if self.wm.ball is not None:
        #                 if (self.wm.ball.direction is not None and
        #                     -7 <= self.wm.ball.direction <= 7):
        #                     self.wm.ah.dash(50)
        #             else:
        #                 self.wm.turn_body_to_point((0, 0))

        #         # turn to ball if we can see it, else face the enemy goal
        #         if self.wm.ball is not None:
        #             self.wm.turn_neck_to_object(self.wm.ball)

        #             return

        # # attack!
        # else:
            # # find the ball
            # if self.wm.ball is None or self.wm.ball.direction is None:
            #     self.wm.ah.turn(30)

            #     return

            # # kick it at the enemy goal
            # if self.wm.is_ball_kickable():
            #     self.wm.kick_to(self.enemy_goal_pos, 1.0)
            #     return
            # else:
            #     # move towards ball
            #     if -7 <= self.wm.ball.direction <= 7:
            #         self.wm.ah.dash(65)
            #     else:
            #         # face ball
            #         self.wm.ah.turn(self.wm.ball.direction / 2)

            #         return



    # Heuristics begin

    # check if ball is close to self
    def ball_close(self):
        return self.wm.ball.distance < 10

    # check if enemy goalpost is close enough
    def goalpos_close(self):
        return self.wm.get_distance_to_point(self.enemy_goal_pos) < 20

    # check if path to target's coordinate is clear, by direction
    def is_clear(self, target_coords):
        q = self.wm.get_nearest_enemy()
        if q == None:
            return False
        q_coords = self.wm.get_object_absolute_coords(q)
        qDir = self.wm.get_angle_to_point(q_coords)
        qDist = self.wm.get_distance_to_point(q_coords)
        
        tDir = self.wm.get_angle_to_point(target_coords)
        tDist = self.wm.get_distance_to_point(target_coords)

        # the closest teammate is closer, or angle is clear
        return tDist < qDist or abs(qDir - tDir) > 20


    # Action decisions start
    # 
    # find the ball by rotating if ball not found
    def find_ball(self):
        # find the ball`
        if self.wm.ball is None or self.wm.ball.direction is None:
            self.wm.ah.turn(30)

    # look around randomly
    def lookaround(self):
        print "lookaround"
        # kick off!
        if self.wm.is_before_kick_off():
            # player 9 takes the kick off
            if self.wm.uniform_number == 9:
                if self.wm.is_ball_kickable():
                    # kick with 100% extra effort at enemy goal
                    self.wm.kick_to(self.enemy_goal_pos, 1.0)
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
                self.wm.kick_to(self.enemy_goal_pos, 1.0)
                return
            else:
                # move towards ball
                if -7 <= self.wm.ball.direction <= 7:
                    self.wm.ah.dash(65)
                else:
                    # face ball
                    self.wm.ah.turn(self.wm.ball.direction / 2)

                return



    # condition for shooting to the goal
    def shall_shoot(self):
        return self.wm.is_ball_kickable() and self.goalpos_close() and self.is_clear(self.enemy_goal_pos)

    # do shoot
    def shoot(self):
        print "shoot"
        return self.wm.kick_to(self.enemy_goal_pos, 1.0)

    # condition for passing to the closest teammate
    # if can kick ball, teammate is closer to goal, path clear
    def shall_pass(self):
        self.lookaround()
        p = self.wm.get_nearest_teammate()
        if p == None:
            return False
        p_coords = self.wm.get_object_absolute_coords(p)
        pDistToGoal = self.wm.euclidean_distance(p_coords, self.enemy_goal_pos)
        myDistToGoal = self.wm.get_distance_to_point(self.enemy_goal_pos)
        # kickable, pass closer to goal, path is clear
        return self.wm.is_ball_kickable() and pDistToGoal < myDistToGoal and self.is_clear(p_coords)

    # do passes
    def passes(self):
        print "pass"
        p = self.wm.get_nearest_teammate()
        if p == None:
            return False
        p_coords = self.wm.get_object_absolute_coords(p)
        dist = self.wm.get_distance_to_point(p_coords)
        power_ratio = 2*dist/55.0
        # kick to closest teammate, power is scaled
        return self.wm.kick_to(p_coords, power_ratio)

    # condition for dribbling, if can't shoot or pass
    def shall_dribble(self):
        # find the ball
        self.find_ball()
        if self.wm.ball is None or self.wm.ball.direction is None:
            self.wm.ah.turn(30)
        return self.wm.is_ball_kickable()

    # dribble: turn body, kick, then run towards ball
    def dribble(self):
        print "dribbling"
        # self.wm.turn_body_to_point(self.enemy_goal_pos)
        # self.wm.align_neck_with_body()
        self.wm.kick_to(self.enemy_goal_pos, 1.0)
        self.wm.ah.dash(50)
        return

    # if enemy has the ball, and not too far move towards it
    def shall_move_to_ball(self):
        while self.wm.ball is None:
            self.find_ball()
        self.wm.align_neck_with_body()
        return self.wm.is_ball_owned_by_enemy() and self.wm.ball.distance < 30

    # move to ball, if enemy owns it
    def move_to_ball(self):
        print "move_to_ball"
        self.wm.ah.dash(60)
        return 

    # defensive, when ball isn't ours, and has entered our side of the field
    def shall_move_to_defend(self):
        self.lookaround()
        if self.wm.ball is not None or self.wm.ball.direction is not None:
            b_coords = self.wm.get_object_absolute_coords(self.wm.ball)
            return self.wm.is_ball_owned_by_enemy() and self.wm.euclidean_distance(self.own_goal_pos, b_coords) < 55.0
        return False

    # defend
    def move_to_defend(self):
        print "move_to_defend"
        q = self.wm.get_nearest_enemy()
        if q == None:
            return False
        q_coords = self.wm.get_object_absolute_coords(q)
        qDir = self.wm.get_angle_to_point(q_coords)
        qDistToOurGoal = self.wm.euclidean_distance(self.own_goal_pos, q_coords)
        # if close to the goal, aim at it
        if qDistToOurGoal < 55:
            self.wm.turn_body_to_point(q_coords)
        # otherwise aim at own goalpos, run there to defend
        else:
            self.wm.turn_body_to_point(self.own_goal_pos)

        self.wm.align_neck_with_body()
        self.wm.ah.dash(80)
        return

    # when our team has ball, and self is not close enough to goalpos. advance to enemy goalpos
    def shall_move_to_enemy_goalpos(self):
        return self.wm.is_ball_owned_by_us() and not self.goalpos_close()

    # if our team has the ball n u r striker
    def move_to_enemy_goalpos(self):
        print "move_to_enemy_goalpos"
        if self.wm.is_ball_kickable():
            # kick with 100% extra effort at enemy goal
            self.wm.kick_to(self.enemy_goal_pos, 1.0)
        self.wm.turn_body_to_point(self.enemy_goal_pos)
        self.wm.align_neck_with_body()
        self.wm.ah.dash(70)
        return


    def decisionLoop(self):
        try:
            self.find_ball()
            # if should shoot, full power
            if self.shall_shoot():
                return self.shoot()
            # else shd pass to closest teammate
            elif self.shall_pass():
                return self.passes()
            # else shd dribble
            elif self.shall_dribble():
                return self.dribble()
            elif self.shall_move_to_ball():
                return self.move_to_ball()
            elif self.shall_move_to_defend():
                return self.move_to_defend()
            elif self.shall_move_to_enemy_goalpos():
                return self.move_to_enemy_goalpos()
            else:
                return self.lookaround()
        except:
            print "exceptions thrown, using fallback"
            self.lookaround()
        


# by role: striker, defender
# do the same preconds, but def on role diff actions
# 1. 
# shoot:
# close enuf to ball and to self.enemy_goal_pos
# if self.wm.ball.distance < 10 and self.get_distance_to_point(self.enemy_goal_pos) < 20 and self.is_ball_kickable():



# shoot
# pass
# move

# striker:
# 

# strategy: ordered
# 1. close to ball: grab, carry toward goal, pass or shoot
# 2. ain't, move to enemy (if enemy has ball), goal (if we have ball n jersey num), ball (if enemy n closest, or jersey num)
# 3. 

# conditions shd be:
# shoot: ball aint none, ball kickable, close to goalpos


# Enum fields
# self.get_distance_to_point(self.enemy_goal_pos)
# self.get_angle_to_point(self.enemy_goal_pos)
# self.wm.ball.distance
# self.wm.ball.direction
# p = self.get_nearest_teammate()
# p.distance
# p.direction
# q = self.get_neatest_enemy()
# q.distance
# q.direction
# self.is_ball_owned_by_us
# self.is_ball_owned_by_enemy
# self.is_ball_kickable

# actions and their triggers
# shoot
# pass
# move

print dir(WorldModel(''))
# print dir(Agent())

# va = 1
# print None or va[0]
# print random.randrange(-30,30)
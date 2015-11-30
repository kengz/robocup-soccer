import math
import random

import message_parser
import sp_exceptions
import game_object

class WorldModel:
    """
    Holds and updates the model of the world as known from current and past
    data.
    """

    # constants for team sides
    SIDE_L = "l"
    SIDE_R = "r"

    class PlayModes:
        """
        Acts as a static class containing variables for all valid play modes.
        The string values correspond to what the referee calls the game modes.
        """

        BEFORE_KICK_OFF = "before_kick_off"
        PLAY_ON = "play_on"
        TIME_OVER = "time_over"
        KICK_OFF_L = "kick_off_l"
        KICK_OFF_R = "kick_off_r"
        KICK_IN_L = "kick_in_l"
        KICK_IN_R = "kick_in_r"
        FREE_KICK_L = "free_kick_l"
        FREE_KICK_R = "free_kick_r"
        CORNER_KICK_L = "corner_kick_l"
        CORNER_KICK_R = "corner_kick_r"
        GOAL_KICK_L = "goal_kick_l"
        GOAL_KICK_R = "goal_kick_r"
        DROP_BALL = "drop_ball"
        OFFSIDE_L = "offside_l"
        OFFSIDE_R = "offside_r"

        def __init__(self):
            raise NotImplementedError("Don't instantiate a PlayModes class,"
                    " access it statically through WorldModel instead.")

    class RefereeMessages:
        """
        Static class containing possible non-mode messages sent by a referee.
        """

        # these are referee messages, not play modes
        FOUL_L = "foul_l"
        FOUL_R = "foul_r"
        GOALIE_CATCH_BALL_L = "goalie_catch_ball_l"
        GOALIE_CATCH_BALL_R = "goalie_catch_ball_r"
        TIME_UP_WITHOUT_A_TEAM = "time_up_without_a_team"
        TIME_UP = "time_up"
        HALF_TIME = "half_time"
        TIME_EXTENDED = "time_extended"

        # these are special, as they are always followed by '_' and an int of
        # the number of goals scored by that side so far.  these won't match
        # anything specifically, but goals WILL start with these.
        GOAL_L = "goal_l_"
        GOAL_R = "goal_r_"

        def __init__(self):
            raise NotImplementedError("Don't instantiate a RefereeMessages class,"
                    " access it statically through WorldModel instead.")

    def __init__(self, action_handler):
        """
        Create the world model with default values and an ActionHandler class it
        can use to complete requested actions.
        """

        # we use the action handler to complete complex commands
        self.ah = action_handler

        # these variables store all objects for any particular game step
        self.ball = None
        self.flags = []
        self.goals = []
        self.players = []
        self.lines = []

        # the default position of this player, its home position
        self.home_point = (None, None)

        # scores for each side
        self.score_l = 0
        self.score_r = 0

        # the name of the agent's team
        self.teamname = None

        # handle player information, like uniform number and side
        self.side = None
        self.uniform_number = None

        # stores the most recent message heard
        self.last_message = None

        # the mode the game is currently in (default to not playing yet)
        self.play_mode = WorldModel.PlayModes.BEFORE_KICK_OFF

        # body state
        self.view_width = None
        self.view_quality = None
        self.stamina = None
        self.effort = None
        self.speed_amount = None
        self.speed_direction = None
        self.neck_direction = None

        # counts of actions taken so far
        self.kick_count = None
        self.dash_count = None
        self.turn_count = None
        self.say_count = None
        self.turn_neck_count = None
        self.catch_count = None
        self.move_count = None
        self.change_view_count = None

        # apparent absolute player coordinates and neck/body directions
        self.abs_coords = (None, None)
        self.abs_neck_dir = None
        self.abs_body_dir = None

        # create a new server parameter object for holding all server params
        self.server_parameters = ServerParameters()

    def triangulate_direction(self, flags, flag_dict):
        """
        Determines absolute view angle for the player given a list of visible
        flags.  We find the absolute angle to each flag, then return the average
        of those angles.  Returns 'None' if no angle could be determined.
        """

        # average all flag angles together and save that as absolute angle
        abs_angles = []
        for f in self.flags:
            # if the flag has useful data, consider it
            if f.distance is not None and f.flag_id in flag_dict:
                flag_point = flag_dict[f.flag_id]
                abs_dir = self.angle_between_points(self.abs_coords, flag_point)
                abs_angles.append(abs_dir)

        # return the average if available
        if len(abs_angles) > 0:
            return sum(abs_angles) / len(abs_angles)

        return None

    def triangulate_position(self, flags, flag_dict, angle_step=36):
        """
        Returns a best-guess position based on the triangulation via distances
        to all flags in the flag list given.  'angle_step' specifies the
        increments between angles for projecting points onto the circle
        surrounding a flag.
        """

        points = []
        for f in flags:
            # skip flags without distance information or without a specific id
            if f.distance is None or f.flag_id not in flag_dict:
                continue

            # generate points every 'angle_step' degrees around each flag,
            # discarding those off-field.
            for i in xrange(0, 360, angle_step):
                dy = f.distance * math.sin(math.radians(i))
                dx = f.distance * math.cos(math.radians(i))

                fcoords = flag_dict[f.flag_id]
                new_point = (fcoords[0] + dx, fcoords[1] + dy)

                # skip points with a coordinate outside the play boundaries
                if (new_point[0] > 60 or new_point[0] < -60 or
                        new_point[1] < -40 or new_point[1] > 40):
                    continue

                # add point to list of all points
                points.append(new_point)

        # get the dict of clusters mapped to centers
        clusters = self.cluster_points(points)

        # return the center that has the most points as an approximation to our
        # absolute position.
        center_with_most_points = (0, 0)
        max_points = 0
        for c in clusters:
            if len(clusters[c]) > max_points:
                center_with_most_points = c
                max_points = len(clusters[c])

        return center_with_most_points

    def cluster_points(self, points, num_cluster_iterations=15):
        """
        Cluster a set of points into a dict of centers mapped to point lists.
        Uses the k-means clustering algorithm with random initial centers and a
        fixed number of iterations to find clusters.
        """

        # generate initial random centers, ignoring identical ones
        centers = set([])
        for i in xrange(int(math.sqrt(len(points) / 2))):
            # a random coordinate somewhere within the field boundaries
            rand_center = (random.randint(-55, 55), random.randint(-35, 35))
            centers.add(rand_center)

        # cluster for some iterations before the latest result
        latest = {}
        cur = {}
        for i in xrange(num_cluster_iterations):
            # initialze cluster lists
            for c in centers:
                cur[c] = []

            # put every point into the list of its nearest cluster center
            for p in points:
                # get a list of (distance to center, center coords) tuples
                c_dists = map(lambda c: (self.euclidean_distance(c, p), c),
                             centers)

                # find the smallest tuple's c (second item)
                nearest_center = min(c_dists)[1]

                # add point to this center's cluster
                cur[nearest_center].append(p)

            # recompute centers
            new_centers = set([])
            for cluster in cur.values():
                tot_x = 0
                tot_y = 0

                # remove empty clusters
                if len(cluster) == 0:
                    continue

                # generate average center of cluster
                for p in cluster:
                    tot_x += p[0]
                    tot_y += p[1]

                # get average center and add to new centers set
                ave_center = (tot_x / len(cluster), tot_y / len(cluster))
                new_centers.add(ave_center)

            # move on to next iteration
            centers = new_centers
            latest = cur
            cur = {}

        # return latest cluster iteration
        return latest

    def euclidean_distance(self, point1, point2):
        """
        Returns the Euclidean distance between two points on a plane.
        """

        try:
            x1 = point1[0]
            y1 = point1[1]
            x2 = point2[0]
            y2 = point2[1]
    
            return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        except:
            return 200

    def angle_between_points(self, point1, point2):
        """
        Returns the angle from the first point to the second, assuming that
        these points exist on a plane, and that the positive x-axis is 0 degrees
        and the positive y-axis is 90 degrees.  All returned angles are positive
        and relative to the positive x-axis.
        """

        try:
            x1 = point1[0]
            y1 = point1[1]
            x2 = point2[0]
            y2 = point2[1]

            # get components of vector between the points
            dx = x2 - x1
            dy = y2 - y1

            # return the angle in degrees
            a = math.degrees(math.atan2(dy, dx))
            if a < 0:
                a = 360 + a
    
            return a
        except:
            return 0

    def process_new_info(self, ball, flags, goals, players, lines):
        """
        Update any internal variables based on the currently available
        information.  This also calculates information not available directly
        from server-reported messages, such as player coordinates.
        """

        # update basic information
        self.ball = ball
        self.flags = flags
        self.goals = goals
        self.players = players
        self.lines = lines

        # TODO: make all triangulate_* calculations more accurate

        # update the apparent coordinates of the player based on all flag pairs
        flag_dict = game_object.Flag.FLAG_COORDS
        self.abs_coords = self.triangulate_position(self.flags, flag_dict)

        # set the neck and body absolute directions based on flag directions
        self.abs_neck_dir = self.triangulate_direction(self.flags, flag_dict)

        # set body dir only if we got a neck dir, else reset it
        if self.abs_neck_dir is not None and self.neck_direction is not None:
            self.abs_body_dir = self.abs_neck_dir - self.neck_direction
        else:
            self.abs_body_dir = None

    def is_playon(self):
        """
        Tells us whether it's play time
        """
        return self.play_mode == WorldModel.PlayModes.PLAY_ON or
        self.play_mode == WorldModel.PlayModes.KICK_OFF_L or
        self.play_mode == WorldModel.PlayModes.KICK_OFF_R or
        self.play_mode == WorldModel.PlayModes.KICK_IN_L or
        self.play_mode == WorldModel.PlayModes.KICK_IN_R or
        self.play_mode == WorldModel.PlayModes.FREE_KICK_L or
        self.play_mode == WorldModel.PlayModes.FREE_KICK_R or
        self.play_mode == WorldModel.PlayModes.CORNER_KICK_L or
        self.play_mode == WorldModel.PlayModes.CORNER_KICK_R or
        self.play_mode == WorldModel.PlayModes.GOAL_KICK_L or
        self.play_mode == WorldModel.PlayModes.GOAL_KICK_R or
        self.play_mode == WorldModel.PlayModes.DROP_BALL or
        self.play_mode == WorldModel.PlayModes.OFFSIDE_L or
        self.play_mode == WorldModel.PlayModes.OFFSIDE_R

    def is_before_kick_off(self):
        """
        Tells us whether the game is in a pre-kickoff state.
        """

        return self.play_mode == WorldModel.PlayModes.BEFORE_KICK_OFF

    def is_kick_off_us(self):
        """
        Tells us whether it's our turn to kick off.
        """

        ko_left = WorldModel.PlayModes.KICK_OFF_L
        ko_right = WorldModel.PlayModes.KICK_OFF_R

        # print self.play_mode

        # return whether we're on the side that's kicking off
        return (self.side == WorldModel.SIDE_L and self.play_mode == ko_left or
                self.side == WorldModel.SIDE_R and self.play_mode == ko_right)

    def is_dead_ball_them(self):
        """
        Returns whether the ball is in the other team's posession and it's a
        free kick, corner kick, or kick in.
        """

        # shorthand for verbose constants
        kil = WorldModel.PlayModes.KICK_IN_L
        kir = WorldModel.PlayModes.KICK_IN_R
        fkl = WorldModel.PlayModes.FREE_KICK_L
        fkr = WorldModel.PlayModes.FREE_KICK_R
        ckl = WorldModel.PlayModes.CORNER_KICK_L
        ckr = WorldModel.PlayModes.CORNER_KICK_R

        # shorthand for whether left team or right team is free to act
        pm = self.play_mode
        free_left = (pm == kil or pm == fkl or pm == ckl)
        free_right = (pm == kir or pm == fkr or pm == ckr)

        # return whether the opposing side is in a dead ball situation
        if self.side == WorldModel.SIDE_L:
            return free_right
        else:
            return free_left

    def is_ball_kickable(self):
        """
        Tells us whether the ball is in reach of the current player.
        """

        # ball must be visible, not behind us, and within the kickable margin
        return (self.ball is not None and
                self.ball.distance is not None and
                self.ball.distance <= self.server_parameters.kickable_margin)

    def get_ball_speed_max(self):
        """
        Returns the maximum speed the ball can be kicked at.
        """

        return self.server_parameters.ball_speed_max

    def kick_to(self, point, extra_power=0.0):
        """
        Kick the ball to some point with some extra-power factor added on.
        extra_power=0.0 means the ball should stop at the given point, anything
        higher means it should have proportionately more speed.
        """

        # how far are we from the desired point?
        point_dist = self.euclidean_distance(self.abs_coords, point)

        # get absolute direction to the point
        abs_point_dir = self.angle_between_points(self.abs_coords, point)

        # get relative direction to point from body, since kicks are relative to
        # body direction.
        if self.abs_body_dir is not None:
            rel_point_dir = self.abs_body_dir - abs_point_dir

        # we do a simple linear interpolation to calculate final kick speed,
        # assuming a kick of power 100 goes 45 units in the given direction.
        # these numbers were obtained from section 4.5.3 of the documentation.
        # TODO: this will fail if parameters change, needs to be more flexible
        max_kick_dist = 45.0
        dist_ratio = point_dist / max_kick_dist

        # find the required power given ideal conditions, then add scale up by
        # difference bewteen actual aceivable power and maxpower.
        required_power = dist_ratio * self.server_parameters.maxpower
        effective_power = self.get_effective_kick_power(self.ball,
                required_power)
        required_power += 1 - (effective_power / required_power)

        # add more power!
        power_mod = 1.0 + extra_power
        power = required_power * power_mod

        # do the kick, finally
        self.ah.kick(rel_point_dir, power)

    def get_effective_kick_power(self, ball, power):
        """
        Returns the effective power of a kick given a ball object.  See formula
        4.21 in the documentation for more details.
        """

        # we can't calculate if we don't have a distance to the ball
        if ball.distance is None:
            return

        # first we get effective kick power:
        # limit kick_power to be between minpower and maxpower
        kick_power = max(min(power, self.server_parameters.maxpower),
                self.server_parameters.minpower)

        # scale it by the kick_power rate
        kick_power *= self.server_parameters.kick_power_rate

        # now we calculate the real effective power...
        a = 0.25 * (ball.direction / 180)
        b = 0.25 * (ball.distance / self.server_parameters.kickable_margin)

        # ...and then return it
        return 1 - a - b

    def turn_neck_to_object(self, obj):
        """
        Turns the player's neck to a given object.
        """

        self.ah.turn_neck(obj.direction)

    def get_distance_to_point(self, point):
        """
        Returns the linear distance to some point on the field from the current
        point.
        """

        return self.euclidean_distance(self.abs_coords, point)

    # Keng-added
    def get_angle_to_point(self, point):
        """
        Returns the relative angle to some point on the field from self.
        """

        # calculate absolute direction to point
        # subtract from absolute body direction to get relative angle
        return self.abs_body_dir - self.angle_between_points(self.abs_coords, point)

    # Keng-added
    def turn_body_to_point(self, point):
        """
        Turns the agent's body to face a given point on the field.
        """

        relative_dir = self.get_angle_to_point(point)

        if relative_dir > 180:
            relative_dir = relative_dir - 180
        elif relative_dir < -180:
            relative_dir = relative_dir + 180

        # turn to that angle
        self.ah.turn(relative_dir)

    def get_object_absolute_coords(self, obj):
        """
        Determines the absolute coordinates of the given object based on the
        agent's current position.  Returns None if the coordinates can't be
        calculated.
        """

        # we can't calculate this without a distance to the object
        if obj.distance is None:
            return None

        # get the components of the vector to the object
        dx = obj.distance * math.cos(obj.direction)
        dy = obj.distance * math.sin(obj.direction)

        # return the point the object is at relative to our current position
        return (self.abs_coords[0] + dx, self.abs_coords[1] + dy)

    def teleport_to_point(self, point):
        """
        Teleports the player to a given (x, y) point using the 'move' command.
        """

        self.ah.move(point[0], point[1])

    def align_neck_with_body(self):
        """
        Turns the player's neck to be in line with its body, making the angle
        between the two 0 degrees.
        """

        # neck angle is relative to body, so we turn it back the inverse way
        if self.neck_direction is not None:
            self.ah.turn_neck(self.neck_direction * -1)

    def get_nearest_teammate_to_point(self, point):
        """
        Returns the uniform number of the fastest teammate to some point.
        """

        # holds tuples of (player dist to point, player)
        distances = []
        for p in self.players:
            # skip enemy and unknwon players
            if p.side == self.side:
                # find their absolute position
                p_coords = self.get_object_absolute_coords(p)

                distances.append((self.euclidean_distance(point, p_coords), p))

        # return the nearest known teammate to the given point
        try:
            nearest = min(distances)[1]
            return nearest
        except:
            return None

    # Keng-added
    def get_nearest_teammate(self):
        """
        Returns the teammate player closest to self.
        """

        # holds tuples of (player dist to point, player)
        distances = []
        # print "checking from get_nearest_teammate"
        # print "selfside", self.side
        for p in self.players:
            # print p.side
            # print p.side == self.side
            # skip enemy and unknwon players
            if p.side == self.side:
                # find their absolute position
                p_coords = self.get_object_absolute_coords(p)

                distances.append((self.get_distance_to_point(p_coords), p))

        # print "finally", distances
        # return the nearest known teammate to the given point
        try:
            nearest = min(distances)[1]
            return nearest
        except:
            return None

    # Keng-added
    def get_nearest_enemy(self):
        """
        Returns the enemy player closest to self.
        """

        # holds tuples of (player dist to point, player)
        distances = []
        for p in self.players:
            # skip enemy and unknwon players
            if p.side != self.side:
                # find their absolute position
                p_coords = self.get_object_absolute_coords(p)

                distances.append((self.get_distance_to_point(p_coords), p))

        # return the nearest known teammate to the given point
        try:
            nearest = min(distances)[1]
            return nearest
        except:
            return None

    # Keng-added
    def is_ball_owned_by_us(self):
        """
        Returns if the ball is in possession by our team.
        """

        # holds tuples of (player dist to point, player)
        for p in self.players:
            # skip enemy and unknwon players
            if p.side == self.side and self.euclidean_distance(self.get_object_absolute_coords(self.ball), self.get_object_absolute_coords(p)) < self.server_parameters.kickable_margin:
                return True
            else:
                continue

        return False

    # Keng-added
    def is_ball_owned_by_enemy(self):
        """
        Returns if the ball is in possession by the enemy team.
        """

        # holds tuples of (player dist to point, player)
        for p in self.players:
            # skip enemy and unknwon players
            if p.side != self.side and self.euclidean_distance(self.get_object_absolute_coords(self.ball), self.get_object_absolute_coords(p)) < self.server_parameters.kickable_margin:
                return True
            else:
                continue

        return False

    def get_stamina(self):
        """
        Returns the agent's current stamina amount.
        """

        return self.stamina

    def get_stamina_max(self):
        """
        Returns the maximum amount of stamina a player can have.
        """

        return self.server_parameters.stamina_max

    def turn_body_to_object(self, obj):
        """
        Turns the player's body to face a particular object.
        """

        self.ah.turn(obj.direction)

class ServerParameters:
    """
    A storage container for all the settings of the soccer server.
    """

    def __init__(self):
        """
        Initialize default parameters for a server.
        """

        self.audio_cut_dist = 50
        self.auto_mode = 0
        self.back_passes = 1
        self.ball_accel_max = 2.7
        self.ball_decay = 0.94
        self.ball_rand = 0.05
        self.ball_size = 0.085
        self.ball_speed_max = 2.7
        self.ball_stuck_area = 3
        self.ball_weight = 0.2
        self.catch_ban_cycle = 5
        self.catch_probability = 1
        self.catchable_area_l = 2
        self.catchable_area_w = 1
        self.ckick_margin = 1
        self.clang_advice_win = 1
        self.clang_define_win = 1
        self.clang_del_win = 1
        self.clang_info_win = 1
        self.clang_mess_delay = 50
        self.clang_mess_per_cycle = 1
        self.clang_meta_win = 1
        self.clang_rule_win = 1
        self.clang_win_size = 300
        self.coach = 0
        self.coach_port = 6001
        self.coach_w_referee = 0
        self.connect_wait = 300
        self.control_radius = 2
        self.dash_power_rate =0.006
        self.drop_ball_time = 200
        self.effort_dec = 0.005
        self.effort_dec_thr = 0.3
        self.effort_inc = 0.01
        self.effort_inc_thr = 0.6
        self.effort_init = 1
        self.effort_min = 0.6
        self.forbid_kick_off_offside = 1
        self.free_kick_faults = 1
        self.freeform_send_period = 20
        self.freeform_wait_period = 600
        self.fullstate_l = 0
        self.fullstate_r = 0
        self.game_log_compression = 0
        self.game_log_dated = 1
        self.game_log_dir = './'
        self.game_log_fixed = 0
        self.game_log_fixed_name = 'rcssserver'
        self.game_log_version = 3
        self.game_logging = 1
        self.game_over_wait = 100
        self.goal_width = 14.02
        self.goalie_max_moves = 2
        self.half_time = 300
        self.hear_decay = 1
        self.hear_inc = 1
        self.hear_max = 1
        self.inertia_moment = 5
        self.keepaway = 0
        self.keepaway_length = 20
        self.keepaway_log_dated = 1
        self.keepaway_log_dir = './'
        self.keepaway_log_fixed = 0
        self.keepaway_log_fixed_name = 'rcssserver'
        self.keepaway_logging = 1
        self.keepaway_start = -1
        self.keepaway_width = 20
        self.kick_off_wait = 100
        self.kick_power_rate = 0.027
        self.kick_rand = 0
        self.kick_rand_factor_l = 1
        self.kick_rand_factor_r = 1
        self.kickable_margin = 0.7
        self.landmark_file = '~/.rcssserver-landmark.xml'
        self.log_date_format = '%Y%m%d%H%M-'
        self.log_times = 0
        self.max_goal_kicks = 3
        self.maxmoment = 180
        self.maxneckang = 90
        self.maxneckmoment = 180
        self.maxpower = 100
        self.minmoment = -180
        self.minneckang = -90
        self.minneckmoment = -180
        self.minpower = -100
        self.nr_extra_halfs = 2
        self.nr_normal_halfs = 2
        self.offside_active_area_size = 2.5
        self.offside_kick_margin = 9.15
        self.olcoach_port = 6002
        self.old_coach_hear = 0
        self.pen_allow_mult_kicks = 1
        self.pen_before_setup_wait = 30
        self.pen_coach_moves_players = 1
        self.pen_dist_x = 42.5
        self.pen_max_extra_kicks = 10
        self.pen_max_goalie_dist_x = 14
        self.pen_nr_kicks = 5
        self.pen_random_winner = 0
        self.pen_ready_wait = 50
        self.pen_setup_wait = 100
        self.pen_taken_wait = 200
        self.penalty_shoot_outs = 1
        self.player_accel_max = 1
        self.player_decay = 0.4
        self.player_rand = 0.1
        self.player_size = 0.3
        self.player_speed_max = 1.2
        self.player_weight = 60
        self.point_to_ban = 5
        self.point_to_duration = 20
        self.port = 6000
        self.prand_factor_l = 1
        self.prand_factor_r = 1
        self.profile = 0
        self.proper_goal_kicks = 0
        self.quantize_step = 0.1
        self.quantize_step_l = 0.01
        self.record_messages = 0
        self.recover_dec = 0.002
        self.recover_dec_thr = 0.3
        self.recover_init = 1
        self.recover_min = 0.5
        self.recv_step = 10
        self.say_coach_cnt_max = 128
        self.say_coach_msg_size = 128
        self.say_msg_size = 10
        self.send_comms = 0
        self.send_step = 150
        self.send_vi_step = 100
        self.sense_body_step = 100
        self.simulator_step = 100
        self.slow_down_factor = 1
        self.slowness_on_top_for_left_team = 1
        self.slowness_on_top_for_right_team = 1
        self.stamina_inc_max = 45
        self.stamina_max = 4000
        self.start_goal_l = 0
        self.start_goal_r = 0
        self.stopped_ball_vel = 0.01
        self.synch_micro_sleep = 1
        self.synch_mode = 0
        self.synch_offset = 60
        self.tackle_back_dist = 0.5
        self.tackle_cycles = 10
        self.tackle_dist = 2
        self.tackle_exponent = 6
        self.tackle_power_rate = 0.027
        self.tackle_width = 1
        self.team_actuator_noise = 0
        self.text_log_compression = 0
        self.text_log_dated = 1
        self.text_log_dir = './'
        self.text_log_fixed = 0
        self.text_log_fixed_name = 'rcssserver'
        self.text_logging = 1
        self.use_offside = 1
        self.verbose = 0
        self.visible_angle = 90
        self.visible_distance = 3
        self.wind_ang = 0
        self.wind_dir = 0
        self.wind_force = 0
        self.wind_none = 0
        self.wind_rand = 0
        self.wind_random = 0


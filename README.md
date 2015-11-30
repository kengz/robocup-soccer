# Robocup
For the AI class.


## Setup
Whole thing shd be self-contained, properly packaged.
To specify agent profile, go to `main.py`


## Run

```
rcsoccersim
[TEAM=<NAME>] python main.py
```

## Strategies
input, output


### kickoff
act if it's your team's ball.
`is_before_kick_off() && is_kick_off_us()`

### whistle
Throw in, free kick, penalty, goalkick
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

### offense
When your team has the ball.
- advance: if not close enuf
- shoot: if close enuf and clear

### defense
When ball is in your half of the field, and enemy's possession
- just swarm them for now

### player maneuver
block, evades


##  Neural Net
on top of predefined conditional actions and heuristics

Fields, per robot
want: input = conditions, output = actions

env input:
- distance to goal
- distance to ball
- distance to enemy
- distance to teammate

output actions:
- shoot to goal
- pass to teammate
- run to position (ball, teammate, enemy, side)
- 

unsupervised pretraining on autoencoder:
- output = input, i.e. input env conds

supervised training:
- set {env, actions} collected in the last round of game, only if result is positive


ok yoyo now define the env and actions

logis:

First define ur env vars n simple heuristics

or skip the pretraining by using a random net first, plug in net n repeat

run a game, each think step collect data of outcome n prev actions, inject to db.
game ends, train autoencoder w/ all actions, then train real
plug in the net, repeat above for evolution

where to incorp action success: reward n cost? in selection of data, by evolution n natural selection - generation
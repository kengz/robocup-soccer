# Robocup
For the AI class.


## Setup
Whole thing shd be self-contained, properly packaged.
To specify agent profile, go to `main.py`


## Run

```
rcsoccersim
python main.py
```

## Strategies
input, output


### kickoff
act if it's your team's ball.
`is_before_kick_off() && is_kick_off_us()`

### whistle
Throw in, free kick wutever,

### offense
When your team has the ball.
- advance: if not close enuf
- shoot: if close enuf and clear

### defense
When ball is in your half of the field, and enemy's possession
- just swarm them for now
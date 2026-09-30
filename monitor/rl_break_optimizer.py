import json
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Q_TABLE_FILE = os.path.join(BASE_DIR, "data", "break_q_table.json")

ACTIONS = [
    "NO_BREAK",
    "MICRO_BREAK",
    "SHORT_BREAK",
    "LONG_BREAK"
]

ALPHA = 0.1
GAMMA = 0.9
EPSILON = 0.2


def load_q_table():

    if not os.path.exists(Q_TABLE_FILE):
        return {}

    with open(Q_TABLE_FILE, "r") as f:
        return json.load(f)


def save_q_table(table):

    with open(Q_TABLE_FILE, "w") as f:
        json.dump(table, f, indent=2)


def state_key(fatigue, burnout, momentum):

    f = int(fatigue // 10)
    b = int(burnout * 10)
    m = int(momentum // 2)

    return f"{f}_{b}_{m}"


def choose_action(q_table, state):

    if random.random() < EPSILON:
        return random.choice(ACTIONS)

    values = q_table.get(state, {})

    if not values:
        return random.choice(ACTIONS)

    return max(values, key=values.get)


def update_q(q_table, state, action, reward, next_state):

    q_table.setdefault(state, {})
    q_table[state].setdefault(action, 0)

    next_values = q_table.get(next_state, {})

    max_next = max(next_values.values()) if next_values else 0

    old_q = q_table[state][action]

    new_q = old_q + ALPHA * (
        reward + GAMMA * max_next - old_q
    )

    q_table[state][action] = new_q


def decide_break_rl(
    fatigue_score,
    burnout_probability,
    fatigue_momentum
):

    q_table = load_q_table()

    state = state_key(
        fatigue_score,
        burnout_probability,
        fatigue_momentum
    )

    action = choose_action(q_table, state)

    save_q_table(q_table)

    return action
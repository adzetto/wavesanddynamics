"""The grid world of the machine learning guide's section 7 (Figures 28, 29, 30).

A 5 x 5 grid, the start in the bottom left square, the goal in the top right.
Four actions (up, down, left, right); a move into the wall leaves the agent
where it is. The reward is the one the text gives for its Figure 30: +1 for
reaching the goal, which ends the episode, and -0.02 for every other step.

Tabular Q-learning (Watkins 1989) with a learning rate ALPHA, a discount GAMMA
and epsilon-greedy exploration, ties between equal values broken at random:

    Q(s, a) <- Q(s, a) + ALPHA [r + GAMMA max_a' Q(s', a') - Q(s, a)]

(max_a' Q(goal, a') = 0: the episode is over). Everything here is plain numpy
and seeded, so a run is reproducible to the last bit; run() returns the whole
transcript, every transition in order, so a page can replay it exactly.
"""
import numpy as np

N = 5                                   # squares per side
START = (0, 0)                          # (x, y): column from the left, row from the bottom
GOAL = (4, 4)
ACTIONS = ("up", "down", "left", "right")
MOVES = ((0, 1), (0, -1), (-1, 0), (1, 0))
R_GOAL, R_STEP = 1.0, -0.02
ALPHA, GAMMA, EPS = 0.5, 0.95, 0.1


def sid(x, y):
    return y * N + x


def xy(s):
    return s % N, s // N


def step(s, a):
    """The environment: next state, reward, whether the episode is over."""
    x, y = xy(s)
    dx, dy = MOVES[a]
    nx, ny = min(N - 1, max(0, x + dx)), min(N - 1, max(0, y + dy))
    s2 = sid(nx, ny)
    if (nx, ny) == GOAL:
        return s2, R_GOAL, True
    return s2, R_STEP, False


def greedy(q, rng):
    best = np.flatnonzero(q == q.max())
    return int(best[0] if len(best) == 1 else rng.choice(best))


def eps_decay(k):
    """Exploration that starts high and decays, as the text advises: 0.5 in
    the first episode, falling linearly to 0.2 by the three hundredth."""
    return max(0.2, 0.5 - 0.3 * k / 300)


def run(episodes=300, seed=21, alpha=ALPHA, gamma=GAMMA, eps=eps_decay, max_steps=2000):
    """Q-learning from Q = 0. `eps` is a number or a function of the episode
    index. Returns (Q after each episode, transcript), the transcript a list of
    (episode, s, a, r, s2, done, q_before, q_after)."""
    rng = np.random.default_rng(seed)
    Q = np.zeros((N * N, 4))
    snaps, log = [], []
    for ep in range(episodes):
        s = sid(*START)
        e = eps(ep) if callable(eps) else eps
        for _ in range(max_steps):
            a = int(rng.integers(4)) if rng.random() < e else greedy(Q[s], rng)
            s2, r, done = step(s, a)
            target = r + (0.0 if done else gamma * Q[s2].max())
            before = Q[s, a]
            Q[s, a] = before + alpha * (target - before)
            log.append((ep, s, a, r, s2, done, before, Q[s, a]))
            s = s2
            if done:
                break
        snaps.append(Q.copy())
    return snaps, log


def v_star(gamma=GAMMA):
    """Exact optimal values by value iteration (the closed form is
    gamma^(d-1) - 0.02 (1 - gamma^(d-1)) / (1 - gamma) at Manhattan distance d)."""
    V = np.zeros(N * N)
    for _ in range(2000):
        Vn = V.copy()
        for s in range(N * N):
            if xy(s) == GOAL:
                Vn[s] = 0.0
                continue
            best = -1e9
            for a in range(4):
                s2, r, done = step(s, a)
                best = max(best, r + (0.0 if done else gamma * V[s2]))
            Vn[s] = best
        if np.max(np.abs(Vn - V)) < 1e-15:
            break
        V = Vn
    return V


def q_star(gamma=GAMMA):
    V = v_star(gamma)
    Qs = np.zeros((N * N, 4))
    for s in range(N * N):
        for a in range(4):
            s2, r, done = step(s, a)
            Qs[s, a] = r + (0.0 if done else gamma * V[s2])
    return Qs


def closed_form_v(x, y, gamma=GAMMA):
    d = abs(GOAL[0] - x) + abs(GOAL[1] - y)
    if d == 0:
        return 0.0
    return gamma ** (d - 1) + R_STEP * (1 - gamma ** (d - 1)) / (1 - gamma)


def pi_eps_greedy(q, eps):
    """The behaviour policy's action probabilities in one state: eps spread
    evenly, the rest shared by the actions tied for the largest value."""
    best = np.flatnonzero(q == q.max())
    p = np.full(4, eps / 4)
    p[best] += (1 - eps) / len(best)
    return p


def policy_is_shortest(Q):
    """Every non goal square's greedy action (by the largest value) moves one
    square closer to the goal."""
    bad = []
    for s in range(N * N):
        if xy(s) == GOAL:
            continue
        a = int(np.argmax(Q[s]))
        s2, _, _ = step(s, a)
        d = lambda q: abs(GOAL[0] - xy(q)[0]) + abs(GOAL[1] - xy(q)[1])
        if d(s2) != d(s) - 1:
            bad.append(xy(s))
    return bad

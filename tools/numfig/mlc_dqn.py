"""A deep Q-network for the grid world when its state is a continuous
measurement (Figure 29 of the machine learning guide).

The same world as mlc_grid.py, but the agent's position is two real numbers,
x and y in [0, 5), not a square's index: a move shifts it by 1 in one
direction (a move into the wall leaves it at the wall), and entering the top
right square [4, 5) x [4, 5) is the goal (+1, the episode ends); every other
step costs 0.02. No table can hold a row for every such position, so a small
network takes (x, y) in and puts out the value of each action.

DQN (Mnih et al. 2015) with the two additions the text names: experience
replay and a target network. 2 inputs, two hidden layers of 12 tanh units,
4 linear outputs. torch, CPU, seeded.
"""
import numpy as np
import torch

HID = 12
GAMMA = 0.95
MOVES = np.array([(0, 1), (0, -1), (-1, 0), (1, 0)], float)   # up, down, left, right
TOP = 5 - 1e-6


def env_step(p, a):
    q = np.clip(p + MOVES[a], 0.0, TOP)
    if q[0] >= 4 and q[1] >= 4:
        return q, 1.0, True
    return q, -0.02, False


def random_start(rng):
    while True:
        p = rng.uniform(0, 5, 2)
        if not (p[0] >= 4 and p[1] >= 4):
            return p


def norm(p):
    return p / 2.5 - 1.0          # [0, 5) -> [-1, 1)


class Net(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.l1 = torch.nn.Linear(2, HID)
        self.l2 = torch.nn.Linear(HID, HID)
        self.l3 = torch.nn.Linear(HID, 4)

    def forward(self, x):
        return self.l3(torch.tanh(self.l2(torch.tanh(self.l1(x)))))


def train(seed=3, steps=40000, batch=64, buf=20000, lr=1e-3, sync=250, eps_steps=15000):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    net, tgt = Net(), Net()
    tgt.load_state_dict(net.state_dict())
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    S = np.zeros((buf, 2)); A = np.zeros(buf, int); R = np.zeros(buf); S2 = np.zeros((buf, 2)); D = np.zeros(buf)
    n = 0
    p, ep_len, episodes, lens = random_start(rng), 0, 0, []
    for k in range(steps):
        eps = max(0.05, 1.0 - 0.95 * k / eps_steps)
        if rng.random() < eps:
            a = int(rng.integers(4))
        else:
            with torch.no_grad():
                a = int(net(torch.tensor(norm(p), dtype=torch.float32)).argmax())
        q, r, done = env_step(p, a)
        i = n % buf
        S[i], A[i], R[i], S2[i], D[i] = p, a, r, q, float(done)
        n += 1
        ep_len += 1
        p = q
        if done or ep_len >= 60:
            p, ep_len, episodes = random_start(rng), 0, episodes + 1
        if n >= 500:
            idx = rng.integers(0, min(n, buf), batch)
            s = torch.tensor(norm(S[idx]), dtype=torch.float32)
            s2 = torch.tensor(norm(S2[idx]), dtype=torch.float32)
            with torch.no_grad():
                target = torch.tensor(R[idx], dtype=torch.float32) + GAMMA * (1 - torch.tensor(D[idx], dtype=torch.float32)) * tgt(s2).max(1).values
            qsa = net(s).gather(1, torch.tensor(A[idx]).view(-1, 1)).squeeze(1)
            loss = torch.nn.functional.smooth_l1_loss(qsa, target)
            opt.zero_grad()
            loss.backward()
            opt.step()
        if k % sync == 0:
            tgt.load_state_dict(net.state_dict())
    return net, {"episodes": episodes, "transitions": n}


def weights(net):
    """The layers as plain lists: W (out x in) and b, float64."""
    out = []
    for l in (net.l1, net.l2, net.l3):
        out.append((l.weight.detach().double().numpy(), l.bias.detach().double().numpy()))
    return out


def forward(W, p):
    """Forward pass in numpy, the same arithmetic the page does."""
    h = norm(np.asarray(p, float))
    acts = [h]
    for i, (w, b) in enumerate(W):
        z = w @ h + b
        h = np.tanh(z) if i < 2 else z
        acts.append(h)
    return acts

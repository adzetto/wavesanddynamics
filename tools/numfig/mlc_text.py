"""The small corpus and the language models behind Figures 24, 25 and 26 of the
machine learning guide.

CORPUS: 88 short English sentences written for these figures in three topics,
pets, rivers and money. "bank" appears in both of its senses (13 river, 19
money), and the little words ("is", "near", "the") appear with both senses, so
only the content words tell them apart. The two sentences Figure 26 reads,
"The bank is near the river" and "The bank approved the loan", are not in it.

counts(), ppmi(), factorise(): word vectors from co-occurrence (Figure 25): the
    positive pointwise mutual information of the counts, factorised to 4
    numbers per word by gradient descent from small random vectors; it
    converges to the best rank 4 approximation (SVD, Eckart and Young).
sense_head(): one scaled dot-product attention head on those vectors, trained
    to tell the two senses of "bank" apart (Figure 26).
tiny_transformer(): a two block transformer, attention both ways, trained to
    fill in a masked word from the words on both sides of it, as BERT is
    (Figure 24).
"""
import re

import numpy as np

PETS = """The cat sat on the mat. The cat sat on the rug. The cat sat on the sofa. The cat sat on the chair.
The cat sat on the bed. The cat sat on the windowsill. The cat sat on the mat. The cat sat by the door.
The cat sat by the window. The cat sat near the fire. The dog sat on the rug. The dog sat by the door.
The dog chased the cat. The cat chased the mouse. The dog chased the ball. The puppy chased the kitten.
A cat is a small pet. A dog is a loyal pet. The kitten slept on the sofa. The puppy slept on the rug.
My dog barks at night. My cat purrs at night. The dog ate its food. The cat ate its food.
We fed the cat and the dog. The vet checked the dog. The vet checked the cat. The kitten and the puppy played.
The dog wagged its tail. The cat licked its paw. Our pet dog loves the garden. Our pet cat loves the garden."""
RIVER = """The river flows to the sea. The river flooded the fields. Fish swim in the river.
The boat drifted down the river. We walked along the river bank. The river bank was muddy.
Reeds grow on the bank of the river. The fisherman sat on the bank of the river. The water of the river was cold.
The stream joins the river. Children swam in the river. The river carries water and mud.
Ducks rest on the river bank. The shore of the lake was sandy. Water washed over the muddy bank.
The boat reached the far bank. The bridge crosses the river. The fish jumped out of the water.
Rain filled the stream with water. The river rose after the rain. The bank is steep.
The bank is muddy after the rain. Grass grows on the steep bank. Children played on the grassy bank.
The canoe landed on the bank. The flood washed away the bank. The old mill is near the river.
The path is near the water. Our cabin is near the stream."""
MONEY = """The bank gave her a loan. The bank raised the interest rate. He borrowed money from the bank.
She paid the loan back to the bank. The bank charges interest on the loan. The loan has a high interest rate.
They opened an account at the bank. The bank holds our money. He took a loan to buy a house.
She saved money in her account. The bank refused the loan. The bank lends money to firms.
Interest on the loan is paid monthly. The manager of the bank signed the loan. The credit card bill is due.
He deposited money at the bank. The loan and the interest were repaid. The bank offers credit to small firms.
She asked the bank for credit. The mortgage is a loan for a house. Money and credit flow through the bank.
The bank approved her mortgage. The firm repaid the loan early. The bank closed his account.
The bank is near the station. The bank is closed on Sunday. The bank is open until five."""

TOPICS = {"pets": PETS, "river": RIVER, "money": MONEY}
TEST = ["The bank is near the river", "The bank approved the loan"]


def sentences():
    """[(topic, [tokens])], tokens as written (sentence start capitalised)."""
    out = []
    for topic, text in TOPICS.items():
        for s in re.split(r"\.\s*", " ".join(text.split())):
            if s:
                out.append((topic, s.split()))
    return out


def cos(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


# ---------------------------------------------------------------------- embeddings (Figure 25)
def counts(window=4):
    """Plain co-occurrence counts between words (lower case, every word) no
    more than `window` positions apart in a sentence. Returns (vocab, X)."""
    ss = [[w.lower() for w in t] for _, t in sentences()]
    vocab = sorted({w for s in ss for w in s})
    ix = {w: i for i, w in enumerate(vocab)}
    X = np.zeros((len(vocab), len(vocab)))
    for s in ss:
        for i, w in enumerate(s):
            for j in range(max(0, i - window), min(len(s), i + window + 1)):
                if j != i:
                    X[ix[w], ix[s[j]]] += 1
    return vocab, X


def ppmi(X):
    tot = X.sum()
    pw = X.sum(1, keepdims=True) / tot
    with np.errstate(divide="ignore"):
        pmi = np.log(X / tot / (pw @ pw.T))
    return np.where(X > 0, np.maximum(pmi, 0), 0)


def factorise(P, d=4, lr=0.02, iters=400, seed=0):
    """Word vectors by gradient descent on 0.5 ||P - W C^T||^2 from small
    random vectors; the vector of a word is (W + C) / 2. Returns the vectors
    after every iteration and the loss."""
    rng = np.random.default_rng(seed)
    n = P.shape[0]
    W = rng.normal(0, .01, (n, d))
    C = rng.normal(0, .01, (n, d))
    traj, losses = [], []
    for _ in range(iters + 1):
        traj.append((W + C) / 2)
        R = W @ C.T - P
        losses.append(.5 * np.sum(R * R))
        gW, gC = R @ C, R.T @ W
        W = W - lr * gW
        C = C - lr * gC
    return np.array(traj), np.array(losses)


SHOWN = ["cat", "dog", "river", "bank", "loan", "kitten", "puppy", "pet", "water", "stream", "boat", "fish",
         "money", "interest", "credit", "account"]           # his five words first, then context


def embedding(d=4, iters=400):
    """The word vectors of Figures 25 and 26 and the map both draw them on.

    Vectors: the gradient descent factorisation of PPMI, rotated (orthogonal
    Procrustes, which leaves every length and angle alone) onto the SVD
    basis, whose axes are ordered by importance; column signs fixed so the
    largest entry of each is positive. Map: every vector scaled to length 1
    (so that nearness on the map is cosine similarity), on the first two
    principal axes of the SHOWN words. Returns a dict."""
    vocab, X = counts()
    P = ppmi(X)
    U, S, _ = np.linalg.svd(P)
    Es = U[:, :d] * np.sqrt(S[:d])
    sgn = np.sign(Es[np.argmax(np.abs(Es), 0), np.arange(d)])
    Es = Es * sgn
    traj, losses = factorise(P, d=d, iters=iters)
    A = traj[-1].T @ Es
    Uo, _, Vo = np.linalg.svd(A)
    Rot = Uo @ Vo                                 # traj[-1] @ Rot ~ Es
    traj = traj @ Rot
    ix = {w: i for i, w in enumerate(vocab)}
    M = np.array([Es[ix[w]] / np.linalg.norm(Es[ix[w]]) for w in SHOWN])
    mean = M.mean(0)
    _, sv, Vt = np.linalg.svd(M - mean, full_matrices=False)
    basis = Vt[:2].T
    basis = basis * np.sign(basis[np.argmax(np.abs(basis), 0), [0, 1]])
    return {"vocab": vocab, "ix": ix, "X": X, "P": P, "E": Es, "S": S, "traj": traj, "losses": losses,
            "mean": mean, "basis": basis, "explained": sv ** 2 / np.sum(sv ** 2),
            "floor": .5 * np.sum(S[d:] ** 2)}


def project(emb, v):
    v = np.asarray(v, float)
    return (v / np.linalg.norm(v) - emb["mean"]) @ emb["basis"]


# ---------------------------------------------------------------------- the attention head (Figure 26)
def sense_head(E, vocab, lam=1e-3, steps=1500, lr=0.03, seed=0):
    """One scaled dot-product attention head reading the sentence around
    "bank": query W_q e_bank, keys W_k e_j, values e_j (every word, "bank"
    itself included), c = sum_j a_j e_j, and p(river sense) = sigmoid(u . c + b).
    Trained on the corpus's sentences with "bank", each labelled with its
    sense by its topic; L2 on (W_q - I), (W_k - I) and u. Returns the fitted
    parameters, a reader for a sentence, and training numbers."""
    import torch
    torch.manual_seed(seed)
    ix = {w: i for i, w in enumerate(vocab)}
    d = E.shape[1]
    Et = torch.tensor(E, dtype=torch.float64)
    eye = torch.eye(d, dtype=torch.float64)
    Wq = torch.nn.Parameter(eye + .1 * torch.randn(d, d, dtype=torch.float64))
    Wk = torch.nn.Parameter(eye + .1 * torch.randn(d, d, dtype=torch.float64))
    u = torch.nn.Parameter(torch.zeros(d, dtype=torch.float64))
    b0 = torch.nn.Parameter(torch.zeros((), dtype=torch.float64))
    data = [([w.lower() for w in t], 1.0 if topic == "river" else 0.0)
            for topic, t in sentences() if "bank" in [w.lower() for w in t]]

    def read(tokens):
        e = Et[torch.tensor([ix[w] for w in tokens])]
        q = Wq @ e[tokens.index("bank")]
        a = torch.softmax((e @ Wk.T) @ q / np.sqrt(d), 0)
        c = a @ e
        return a, c, torch.sigmoid(u @ c + b0)

    opt = torch.optim.Adam([Wq, Wk, u, b0], lr=lr)
    for _ in range(steps):
        loss = 0
        for toks, y in data:
            p = read(toks)[2]
            loss = loss - (y * torch.log(p) + (1 - y) * torch.log(1 - p))
        loss = loss / len(data) + lam * (torch.sum((Wq - eye) ** 2) + torch.sum((Wk - eye) ** 2) + torch.sum(u ** 2))
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        wrong = [" ".join(t) for t, y in data if (read(t)[2].item() > .5) != (y > .5)]

    def reader(sentence):
        toks = sentence.lower().split()
        with torch.no_grad():
            a, c, p = read(toks)
        return toks, a.numpy(), c.numpy(), float(p)

    params = {"Wq": Wq.detach().numpy(), "Wk": Wk.detach().numpy(), "u": u.detach().numpy(), "b": float(b0.detach())}
    info = {"n": len(data), "river": int(sum(y for _, y in data)), "acc": 1 - len(wrong) / len(data),
            "wrong": wrong, "loss": float(loss)}
    return params, reader, info


# ---------------------------------------------------------------------- the transformer (Figure 24)
MASK = "[MASK]"


def masked_examples():
    """Every sentence once per word, that word replaced by MASK: [(tokens, position, word)]."""
    return [(s[:i] + [MASK] + s[i + 1:], i, s[i]) for _, s in sentences() for i in range(len(s))]


def tiny_transformer(d=8, heads=2, ff=16, blocks=2, steps=6000, lr=0.01, seed=0):
    """A two block transformer encoder (Vaswani et al. 2017, post norm:
    attention, add and norm, feed forward, add and norm), sinusoidal positions,
    trained as BERT is (Devlin et al. 2019) to fill in a masked word: every
    sentence once per word, that word replaced by the token MASK, and the word
    read from the output at its position. Attention runs both ways: every token
    attends to every token of its sentence (only the padding is masked), so the
    words after the gap can count as much as those before it. 6000 full batch
    steps: the loss settles at the corpus's own minimum (the cross entropy of
    each masked sentence's own word frequencies).
    Returns the model, the vocabulary (MASK is token V, after the V words), the
    position table and training numbers."""
    import torch
    torch.manual_seed(seed)
    sents = [t for _, t in sentences()]
    vocab = sorted({w for s in sents for w in s})
    ix = {w: i for i, w in enumerate(vocab)}
    V = len(vocab)
    ix[MASK] = V
    Lmax = max(len(s) for s in sents)
    pe = np.zeros((Lmax, d))
    pos = np.arange(Lmax)[:, None]
    div = 10000 ** (np.arange(0, d, 2) / d)
    pe[:, 0::2], pe[:, 1::2] = np.sin(pos / div), np.cos(pos / div)
    PE = torch.tensor(pe, dtype=torch.float32)

    class Block(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.q, self.k, self.v, self.o = (torch.nn.Linear(d, d) for _ in range(4))
            self.n1, self.n2 = torch.nn.LayerNorm(d), torch.nn.LayerNorm(d)
            self.f1, self.f2 = torch.nn.Linear(d, ff), torch.nn.Linear(ff, d)

        def forward(self, x, keep):                 # keep[b, j]: position j is a word, not padding
            B, L, _ = x.shape
            dk = d // heads
            sp = lambda z: z.view(B, L, heads, dk).transpose(1, 2)
            q, k, v = sp(self.q(x)), sp(self.k(x)), sp(self.v(x))
            s = q @ k.transpose(-1, -2) / np.sqrt(dk)
            s = s.masked_fill(~keep[:, None, None, :], -1e9)
            a = torch.softmax(s, -1)
            h = (a @ v).transpose(1, 2).reshape(B, L, d)
            x = self.n1(x + self.o(h))
            x = self.n2(x + self.f2(torch.relu(self.f1(x))))
            return x, a

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = torch.nn.Embedding(V + 1, d)                            # the V words and MASK
            self.blocks = torch.nn.ModuleList([Block() for _ in range(blocks)])
            self.out = torch.nn.Linear(d, V)

        def forward(self, ids, lens, at):                                       # at: the masked position
            B, L = ids.shape
            keep = torch.arange(L)[None, :] < lens[:, None]
            x = self.emb(ids) + PE[:L]
            trace, atts = [x], []
            for b in self.blocks:
                x, a = b(x, keep)
                trace.append(x)
                atts.append(a)
            return self.out(x[torch.arange(B), at]), trace, atts

    X, Y, Ls, A = [], [], [], []
    for toks, i, w in masked_examples():
        X.append([ix[q] for q in toks] + [0] * (Lmax - len(toks)))
        Y.append(ix[w])
        Ls.append(len(toks))
        A.append(i)
    X, Y, Ls, A = torch.tensor(X), torch.tensor(Y), torch.tensor(Ls), torch.tensor(A)
    model = Model()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    for _ in range(steps):
        loss = torch.nn.functional.cross_entropy(model(X, Ls, A)[0], Y)
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        logits = model(X, Ls, A)[0]
        acc = float((logits.argmax(1) == Y).float().mean())
        loss = float(torch.nn.functional.cross_entropy(logits, Y))
    return model, vocab, pe, {"loss": loss, "acc": acc, "examples": len(Y), "V": V}

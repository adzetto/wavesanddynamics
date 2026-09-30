"""The experiment behind Figure 31 of the machine learning guide (mlc_modelmap.py).

Five model families, from simple to flexible, are trained on n examples of two
regression tasks and scored against the true pattern on 4000 fresh points:

  simple pattern:  y = x1 - 0.8 x2 + 0.6 x3 + 0.4 x4 + noise (a straight line)
  complex pattern: the same, plus an interaction and four oscillating terms

four features uniform on [-1, 1], noise standard deviation 0.3. Each size is
repeated (16 times up to 200 examples, 8 up to 1600, 4 at 3200, 2 at 6400) and averaged.
Hyperparameters: ridge penalty, tree leaf size and the number of neighbours
are chosen by internal cross-validation; the forest has 100 trees, the MLP two
layers of 64 units with early stopping. scikit-learn, seeded.
"""
import json
import os
import tempfile
import warnings

import numpy as np

warnings.filterwarnings("ignore")
D = 4
NS = [25, 50, 100, 200, 400, 800, 1600, 3200, 6400]
MODELS = ["linear", "tree", "knn", "forest", "mlp"]
CACHE = os.path.join(tempfile.gettempdir(), "mlc_modelmap_v3.json")


def target(X, complex_):
    y = X @ np.array([1.0, -0.8, 0.6, 0.4])
    if complex_:
        y = (y + 1.2 * X[:, 0] * X[:, 1] + np.sin(2.5 * X[:, 2]) * np.cos(1.5 * X[:, 3])
             + 0.9 * np.sin(4.0 * X[:, 0] + 3.0 * X[:, 1]) + 0.8 * np.sin(6.0 * X[:, 2] * X[:, 3])
             + 0.6 * np.cos(7.0 * X[:, 0] - 5.0 * X[:, 3]))
    return y


def make(name, n):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import GridSearchCV
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.neural_network import MLPRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeRegressor
    if name == "linear":
        return make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13)))
    if name == "tree":
        m = DecisionTreeRegressor(random_state=0)
        return GridSearchCV(m, {"min_samples_leaf": [1, 3, 10, 30]}, cv=3) if n >= 40 else DecisionTreeRegressor(min_samples_leaf=3, random_state=0)
    if name == "knn":
        m = make_pipeline(StandardScaler(), KNeighborsRegressor())
        return GridSearchCV(m, {"kneighborsregressor__n_neighbors": [3, 7, 15, 31]}, cv=3) if n >= 40 else make_pipeline(StandardScaler(), KNeighborsRegressor(5))
    if name == "forest":
        return RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=0, n_jobs=4)
    return make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 64), alpha=1e-3, learning_rate_init=3e-3,
                                                        max_iter=1000, early_stopping=True, validation_fraction=.2, random_state=0))


def run():
    if os.path.isfile(CACHE):
        with open(CACHE) as fh:
            return json.load(fh)
    Xte = np.random.default_rng(0).uniform(-1, 1, (4000, D))
    out = {}
    for task in ("simple", "complex"):
        yte = target(Xte, task == "complex")
        for n in NS:
            reps = 16 if n <= 200 else 8 if n <= 1600 else 4 if n <= 3200 else 2
            for rep in range(reps):
                r = np.random.default_rng(1000 * (task == "complex") + 37 * rep + n)
                X = r.uniform(-1, 1, (n, D))
                y = target(X, task == "complex") + r.normal(0, 0.3, n)
                for name in MODELS:
                    m = make(name, n).fit(X, y)
                    out.setdefault(f"{task}|{n}|{name}", []).append(float(np.sqrt(np.mean((m.predict(Xte) - yte) ** 2))))
            print(task, n, " ".join(f"{k} {np.mean(out[f'{task}|{n}|{k}']):.3f}" for k in MODELS), flush=True)
    with open(CACHE, "w") as fh:
        json.dump(out, fh)
    return out


if __name__ == "__main__":
    run()

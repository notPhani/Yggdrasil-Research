"""E3: quasi-Poisson vs NB2 MLE on a self-exciting softplus count model with NB2 noise."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln
def sp(x): return np.logaddexp(0, x)
def simulate(rng, n, b0, a, r, am=0.9):
    y = np.zeros(n); z = 0.0; zs = np.zeros(n)
    for t in range(n):
        zs[t] = z; lam = sp(b0 + a * z)
        y[t] = rng.negative_binomial(r, r / (r + lam)); z = am * z + (1 - am) * y[t]
    return y, zs
def fit(y, zs, kind):
    def lam(th): return np.maximum(sp(th[0] + th[1] * zs), 1e-9)
    if kind == "qp":
        f = lambda th: np.sum(lam(th) - y * np.log(lam(th)))
        return minimize(f, [0.5, 0.1], method="L-BFGS-B").x
    def nll(th):
        mu = lam(th); r = np.exp(th[2])
        return -np.sum(gammaln(y + r) - gammaln(r) - gammaln(y + 1) + r * np.log(r / (r + mu)) + y * np.log(mu / (r + mu)))
    return minimize(nll, [0.5, 0.1, 0.0], method="L-BFGS-B").x[:2]
rng = np.random.default_rng(3); true = (1.0, 0.6, 1.5)
for n in (2000, 8000):
    d, q, b, rel = [], [], [], []
    for rep in range(30):
        y, zs = simulate(rng, n, *true)
        tq, tb = fit(y, zs, "qp"), fit(y, zs, "nb2")
        q.append(tq); b.append(tb); d.append(tq - tb)
        lq, lb = sp(tq[0] + tq[1] * zs), sp(tb[0] + tb[1] * zs); rel.append(np.mean(np.abs(lq - lb) / lb))
    q, b, d = map(np.array, (q, b, d))
    print(f"E3 n={n}: true (b0, a) = {true[:2]}, NB2 size r = {true[2]}, 30 reps")
    print(f"   QP  mean {q.mean(0).round(3)}  sd {q.std(0).round(3)}")
    print(f"   NB2 mean {b.mean(0).round(3)}  sd {b.std(0).round(3)}")
    print(f"   QP - NB2: mean {d.mean(0).round(4)}  sd {d.std(0).round(3)}   mean |lam_QP - lam_NB2| / lam = {np.mean(rel):.4f}")

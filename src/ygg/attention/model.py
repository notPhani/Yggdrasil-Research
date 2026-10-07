"""Engine 2b math (Session 4 + 4.2'): traces, drive, softplus, divisive competition, quasi-Poisson fit.

  z[j][m](t)  = a_m z[j][m](t-1) + (1 - a_m) y_j(t-1),       a_m = exp(-15 min / tau_m), tau = 1 h, 6 h, 1 d, 1 w
  eta_i(t)    = b0_i + c_i(how) + sum_e d_ie D_e(t) + sum_{j in K(i), m} A_ijm z[j][m](t)
  lam_raw     = s * softplus(eta / s);  lam = lam_raw * (B / (B + S_raw))^omega
  fit (4.2')  = quasi-Poisson loss sum(c*lam_raw - y*log(c*lam_raw)) + sparse group lasso on A + ridge,
                subject to sum_{j,m} pos(A_ijm) <= rho_cap (only while omega is ~0)
Rows are separable given the competition factors c(t) (Lemma 6.7), so each row is solved by FISTA with a
fixed iteration count (deterministic), and an outer loop refreezes c and profiles omega on a held-out day.
Cut note: the hour-of-week gain g(how) is fixed at 0, and the phenomenon baseline beta*log(Phi) is deferred.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

TAU_H = np.array([1.0, 6.0, 24.0, 168.0])
A_M = np.exp(-0.25 / TAU_H)
Q = (1, 2, 7, 14, 21)


def softplus(x: np.ndarray, s: float) -> np.ndarray:
    return s * np.logaddexp(0.0, x / s)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.tanh(0.5 * x))


def fourier(how: np.ndarray) -> np.ndarray:
    """10 hour-of-week features (cos, sin for q in Q); how in [0, 168)."""
    ang = 2.0 * np.pi * np.outer(how, Q) / 168.0
    return np.concatenate([np.cos(ang), np.sin(ang)], axis=1)


def traces(y: np.ndarray, z0: np.ndarray | None = None) -> np.ndarray:
    """y: T x N (windows x narratives) -> Z: T x N x 4 with Z[t] built from y[:t] only (predictable)."""
    T, N = y.shape
    Z = np.zeros((T, N, 4))
    z = np.zeros((N, 4)) if z0 is None else z0.copy()
    for t in range(T):
        Z[t] = z
        z = A_M * z + (1.0 - A_M) * y[t][:, None]
    return Z


@dataclass
class FitConfig:
    s: float = 1.0
    lam_group: float = 0.005
    lam_l1: float = 0.00125
    ridge: float = 1e-6
    refit_ridge: float = 1e-3      # small ridge in the relaxed refit: stops near-collinear timescales from cancelling
    rho_cap: float = 0.95
    iters: int = 60
    omega_grid: tuple = (0.0, 0.25, 0.5, 0.75, 1.0)
    beta_b_grid: tuple = (-1.0, 0.0, 1.0)
    outer: int = 2


def prox_row(theta: np.ndarray, n_base: int, groups: int, step: float, cfg: FitConfig, cap: bool) -> np.ndarray:
    """Prox of l1 + group lasso on the A block (groups of 4 timescales), then projection onto sum(pos(A)) <= rho_cap."""
    out = theta.copy()
    A = out[n_base:].reshape(groups, 4)
    A = np.sign(A) * np.maximum(np.abs(A) - step * cfg.lam_l1, 0.0)
    norms = np.linalg.norm(A, axis=1, keepdims=True)
    A = A * np.maximum(0.0, 1.0 - step * cfg.lam_group / np.maximum(norms, 1e-12))
    if cap:
        pos = np.maximum(A, 0.0)
        tot = pos.sum()
        if tot > cfg.rho_cap:
            flat = np.sort(pos.ravel())[::-1]
            cums = np.cumsum(flat)
            k = np.arange(1, len(flat) + 1)
            ok = flat - (cums - cfg.rho_cap) / k > 0
            thr = (cums[ok][-1] - cfg.rho_cap) / k[ok][-1]
            A = np.where(A > 0, np.maximum(A - thr, 0.0), A)
    out[n_base:] = A.ravel()
    return out


def _fista(X: np.ndarray, y: np.ndarray, c: np.ndarray, mask: np.ndarray, theta0: np.ndarray, n_base: int,
           cfg: FitConfig, cap: bool, support: np.ndarray | None = None) -> np.ndarray:
    """FISTA on the quasi-Poisson row objective (Lemma 6.7: convex in eta, eta affine in theta)."""
    Xm, ym, cm = X[mask], y[mask], c[mask]
    if len(ym) == 0:
        return theta0
    # exact reparameterization for conditioning: centre the trace columns (they are nearly collinear with the
    # intercept), fit, then fold the centring back into b0. The penalty on A is unchanged.
    mu = Xm[:, n_base:].mean(axis=0)
    Xm = Xm.copy()
    Xm[:, n_base:] -= mu
    theta0 = theta0.copy()
    theta0[0] += theta0[n_base:] @ mu
    groups = (X.shape[1] - n_base) // 4
    s = cfg.s

    n = len(ym)

    def obj_grad(th):                                      # mean loss per window, so penalties are per-observation
        eta = Xm @ th
        lr = np.maximum(softplus(eta, s), 1e-9)
        lam = cm * lr
        f = float(np.sum(lam - ym * np.log(lam))) / n + cfg.ridge * float(th @ th)
        g_eta = sigmoid(eta / s) * (cm - ym / lr) / n
        return f, Xm.T @ g_eta + 2.0 * cfg.ridge * th

    # initial step from the spectral norm of the design (power iteration, fixed count); backtracking shrinks it
    v = np.ones(Xm.shape[1]) / math.sqrt(Xm.shape[1])
    for _ in range(20):
        v = Xm.T @ (Xm @ v)
        v /= max(np.linalg.norm(v), 1e-12)
    sigma2 = float(np.linalg.norm(Xm @ v) ** 2)
    step = n / max(sigma2 * float(np.max(cm)) * (0.25 / s + 1.0), 1e-9)
    x_prev = theta0.copy()
    yk = theta0.copy()
    tk = 1.0
    f_prev, _ = obj_grad(x_prev)
    for _ in range(cfg.iters):
        f_y, g_y = obj_grad(yk)
        step *= 1.5                                        # let the step grow back; backtracking bounds it
        for _bt in range(30):                              # backtracking: fixed cap, deterministic
            x_new = prox_row(yk - step * g_y, n_base, groups, step, cfg, cap)
            if support is not None:
                x_new[n_base:] *= support
            f_new, _ = obj_grad(x_new)
            d = x_new - yk
            if f_new <= f_y + g_y @ d + (0.5 / step) * (d @ d):
                break
            step *= 0.5
        t_next = 0.5 * (1.0 + math.sqrt(1.0 + 4.0 * tk * tk))
        if f_new > f_prev:                                 # monotone restart (keeps Lemma 8.2's descent)
            yk, tk = x_prev.copy(), 1.0
            continue
        yk = x_new + ((tk - 1.0) / t_next) * (x_new - x_prev)
        x_prev, f_prev, tk = x_new, f_new, t_next
    out = x_prev.copy()
    out[0] -= out[n_base:] @ mu
    return out


def fit_row(X: np.ndarray, y: np.ndarray, c: np.ndarray, mask: np.ndarray, theta0: np.ndarray, n_base: int,
            cfg: FitConfig, cap: bool) -> np.ndarray:
    """Relaxed sparse group lasso: select edge groups with the penalty, then refit them without it
    (ridge and the stability cap kept). This removes the lasso shrinkage bias on the selected edges."""
    sel = _fista(X, y, c, mask, theta0, n_base, cfg, cap)
    groups = (X.shape[1] - n_base) // 4
    support = np.repeat(np.linalg.norm(sel[n_base:].reshape(groups, 4), axis=1) > 0, 4).astype(float)
    free = FitConfig(**{**cfg.__dict__, "lam_group": 0.0, "lam_l1": 0.0, "ridge": cfg.refit_ridge})
    return _fista(X, y, c, mask, sel, n_base, free, cap, support)


def qp_deviance(y: np.ndarray, lam: np.ndarray) -> float:
    lam = np.maximum(lam, 1e-9)
    with np.errstate(divide="ignore", invalid="ignore"):
        term = np.where(y > 0, y * np.log(y / lam), 0.0)
    return float(2.0 * np.sum(term - (y - lam)))

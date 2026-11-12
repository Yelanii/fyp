"""Checks the exact formulas in theory.py against the simulator's own random outcomes (env.Environment.call), and
draws the figure for THEORY_2026-10-31.md.

The step logic below mirrors runner.py (retry on loud or flag; cross-check branch of rule v5), applied to one step
at a time with fixed p, so every step index t of a long run is an independent replication.

Usage: python -m ereplan.theory_check
"""
import os, time
import numpy as np

from .config import Setting
from .env import Environment
from .theory import Step, loss_never, loss_check, loss_cross, fail_prob_correct, wrong_check_region


def simulate(st: Step, policy: str, seeds=range(7000, 7004), n_tasks=4000):
    total, n = 0.0, 0
    for seed in seeds:
        s = Setting(n_tasks=n_tasks, rho=st.rho, q_true=st.q, false_alarm=st.f, fa_persistence=st.pi, r_max=st.R)
        env = Environment(s, "drop_0.95", seed)
        env.p[0, :] = st.p
        env.p[1, :] = st.a
        for t in range(env.T):
            loss, done = 0.0, False
            for att in range(st.R + 1):
                checked = policy != "N"
                loss += st.w + (st.c if checked else 0.0)
                out = env.call(0, t, att, checked)
                truly_correct = out == "false_alarm"
                if out == "false_alarm":
                    out = "caught"
                if out == "caught" and policy == "X":
                    loss += st.wB
                    alt = env.call(1, t, att, False)
                    if alt == "loud":
                        continue
                    if truly_correct and alt == "ok":
                        done = True; break                    # agree: keep the (correct) output
                    if alt == "leak":
                        loss += st.L                          # the alternative's wrong output is used
                    done = True; break
                if out == "ok":
                    done = True; break
                if out == "leak":
                    loss += st.L; done = True; break
            if not done:
                loss += st.F
            total += loss; n += 1
    return total / n, n


def main():
    t0 = time.time()
    cases = [Step(p=p, f=f, pi=pi, R=R) for p in (0.6, 0.85, 0.95) for f in (0.05, 0.15)
             for pi in (0.0, 0.5, 1.0) for R in (1, 2)]
    L = ["# Theory check: exact formulas vs the simulator's outcomes", "",
         "| p | f | pi | R | N exact | N sim | C exact | C sim | X exact | X sim | max rel. error |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    worst = 0.0
    for st in cases:
        ex = dict(N=loss_never(st), C=loss_check(st), X=loss_cross(st))
        sm = {k: simulate(st, k)[0] for k in ex}
        err = max(abs(sm[k] / ex[k] - 1) for k in ex)
        worst = max(worst, err)
        L.append(f"| {st.p} | {st.f} | {st.pi} | {st.R} | {ex['N']:.2f} | {sm['N']:.2f} | {ex['C']:.2f} | "
                 f"{sm['C']:.2f} | {ex['X']:.2f} | {sm['X']:.2f} | {100 * err:.2f}% |")
    L += ["", f"Worst relative error {100 * worst:.2f}% over {len(cases)} cases x 3 policies "
          f"(80,000 simulated steps each); {time.time() - t0:.0f} s."]

    # failure probability of a correct step: true vs assumed under independence
    L += ["", "## Chance that a correct step fails because every attempt is flagged", "",
          "| f | R | pi = 0 (assumed) | pi = 0.8 | pi = 1 | ratio pi=1 / pi=0 |", "|---|---|---|---|---|---|"]
    for f in (0.05, 0.14, 0.15):
        for R in (1, 2):
            a0, a8, a1 = (fail_prob_correct(f, pi, R) for pi in (0.0, 0.8, 1.0))
            L.append(f"| {f} | {R} | {a0:.5f} | {a8:.4f} | {a1:.4f} | {a1 / a0:.0f}x |")

    # wrong-check region at the default step, for three persistence levels
    L += ["", "## Wrong-check region (rule assumes pi = 0 and checks; never checking is cheaper)", "",
          "| f | L = F | pi | p ranges where it happens | max excess loss per step |", "|---|---|---|---|---|"]
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    base = Step(p=0.9)
    for f in (0.05, 0.15):
        for LF in (120.0, 360.0):
            for pi in (0.5, 0.8, 1.0):
                g, mask, dpi, d0 = wrong_check_region(base.with_(f=f, pi=pi, L=LF, F=LF))
                runs = np.flatnonzero(np.diff(np.r_[0, mask.astype(int), 0]))
                rng = ", ".join(f"{g[a]:.3f}-{g[b - 1]:.3f}" for a, b in zip(runs[::2], runs[1::2])) or "none"
                ex = f"{dpi[mask].max():.2f}" if mask.any() else "-"
                L.append(f"| {f} | {LF:.0f} | {pi} | {rng} | {ex} |")
    st = base.with_(f=0.15, L=360.0, F=360.0)
    g, mask, dpi, d0 = wrong_check_region(st.with_(pi=1.0))
    ax.axhline(0, color="#6B7280", lw=0.8)
    ax.plot(g, d0, color="#9CA3AF", lw=2, ls="--", label="what a rule assuming independent flags expects (pi = 0)")
    for pi, col in ((0.5, "#5FA8B5"), (1.0, "#0B5D6B")):
        _, _, dd, _ = wrong_check_region(st.with_(pi=pi))
        ax.plot(g, dd, color=col, lw=2, label=f"true extra loss of checking, pi = {pi}")
    dx = np.array([loss_cross(st.with_(p=p, pi=1.0)) - loss_never(st.with_(p=p)) for p in g])
    ax.plot(g, dx, color="#B45309", lw=1.6, ls=":", label="cross-check on a second tool (rule v5), pi = 1")
    ax.fill_between(g, -40, 70, where=mask, color="#F59E0B", alpha=0.18, lw=0,
                    label="rule checks, but never checking is cheaper (pi = 1)")
    ax.set_ylim(-40, 70); ax.set_xlim(0.3, 1.0)
    ax.set_xlabel("tool success rate p on this step"); ax.set_ylabel("extra loss vs never checking, per step")
    ax.set_title("f = 0.15, R = 2 retries, L = F = 360", fontsize=9, loc="left")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    out = os.path.join("results", f"theory_check_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, "wrong_check_region.png"), dpi=200)
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L)); print("Saved to", out)


if __name__ == "__main__":
    main()

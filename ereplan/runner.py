"""Runs one strategy through one simulated run and computes the Table 3.14 metrics."""
import math
import numpy as np

from .config import Setting
from .env import Environment, _rng
from .strategies import REGISTRY, switch_line
from . import selfcal, fa_rule, litbaselines, crosscheck  # noqa: F401  (registers v3, v4, v4_pi, B9-B12 and v5)
from . import rule_v5s, rule_rho, rule_v5_1, ablation_v51  # noqa: F401 (registers v5_s/v5_rho/v5.1/FR21 ablation)
from . import rule_v6  # noqa: F401  (registers rule v6 and the fixed-tool references, FR18)


def true_line(s: Setting, env: Environment, cur: int, u: int, t: int, switch_cost: float) -> float:
    p = {j: float(env.p[j, t]) for j in range(len(s.tools))}
    return switch_line(s, cur, u, p, switch_cost)[0]


def run(strategy_name: str, params: dict, s: Setting, scenario: str, seed: int,
        record: bool = False) -> dict:
    env = Environment(s, scenario, seed)
    params = dict(params)
    horizon_mode = params.pop("horizon_mode", "task")
    session_cap = params.pop("session_cap", 50)
    cls = REGISTRY[strategy_name]
    # FR20 confirmatory test only: a strategy can be handed a WRONG fixed belief about rho (the loud-failure
    # share) while the environment keeps generating failures at the true s.rho. Added 9 Nov 2026; None (the
    # default) keeps the old behaviour -- strategy and environment share the same Setting -- for every
    # existing caller and test.
    rho_belief = params.pop("rho_belief", None)
    strat_s = s if rho_belief is None else s.with_(rho=rho_belief)
    # variants of one rule can share its random stream (rng_name), so their comparison is fully paired
    strat = cls(strat_s, _rng("strategy", getattr(cls, "rng_name", strategy_name), seed), **params)
    strat.horizon_mode, strat.session_cap = horizon_mode, session_cap
    S, T = s.steps_per_task, env.T

    spend = 0.0
    successes = leaks = unrecovered = checks = switches = false_switches = crossing_checks = false_alarms = 0
    fa_failed = rechecks = paid_switches = 0               # added 24 Oct 2026 (part E)
    crosschecks = fa_resolved = 0                          # added 27 Oct 2026 (rule v5)
    third_checks = audits = fallback_calls = 0              # added 6 Nov 2026 (rule v5.1, FR19)
    xcheck = bool(getattr(strat, "crosscheck", False))
    reverify_k = int(getattr(strat, "reverify_k", 0))
    ssv = bool(getattr(strat, "ssv", False))
    env_agree = bool(getattr(env, "real_compare", False))  # only the real-judge FreshQA scenarios set it
    tool_at = np.full(T, -1)
    trace = [] if record else None
    t = 0
    for task in range(s.n_tasks):
        ctx = {"env": env, "t": t, "u": S, "cur": None, "left_in_run": T - t}
        prev = int(tool_at[t - 1]) if t > 0 else None
        cur = strat.start_task(ctx)
        if prev is not None and cur != prev:          # planner moved away between tasks
            switches += 1
            if env.p[prev, t] >= true_line(s, env, prev, S, t, 0.0):
                false_switches += 1
        leaked = failed = False
        for step in range(S):
            t = task * S + step
            u = S - step
            ctx = {"env": env, "t": t, "u": u, "cur": cur, "left_in_run": T - t}
            action = strat.decide(ctx, allow_switch=True)
            if action == "switch":
                if env.p[cur, t] >= true_line(s, env, cur, u, t, s.switch_cost):
                    false_switches += 1
                if record:
                    trace.append(dict(t=t, tool=cur, action="switch", true_p=float(env.p[cur, t]), **ctx["trace"]))
                new = strat.switch_to(ctx)
                spend += s.switch_cost
                switches += 1
                paid_switches += 1
                cur = new
                ctx = {"env": env, "t": t, "u": u, "cur": cur, "left_in_run": T - t}
                action = strat.decide(ctx, allow_switch=False)
            checked = action == "call_and_check"
            tr = ctx.get("trace", {})
            fallback_calls += int(tr.get("fallback", False))
            if checked:
                if tr.get("low", 0) <= tr.get("line", -1) <= tr.get("high", 0):
                    crossing_checks += 1
            if record:
                trace.append(dict(t=t, tool=cur, action=action, true_p=float(env.p[cur, t]), **tr))
            tool_at[t] = cur
            step_ok = False
            step_fa = False
            for attempt in range(s.r_max + 1):
                spend += s.eff_price(cur) + (s.check_price if checked else 0.0)
                checks += int(checked)
                outcome = env.call(cur, t, attempt, checked)
                truly_correct = outcome == "false_alarm"
                if outcome == "false_alarm":
                    false_alarms += 1
                    step_fa = True
                    outcome = "caught"                  # the agent sees the same thing as a real catch
                if checked and getattr(strat, "wants_audit", False) and s.audit_frac > 0 and \
                        _rng("audit", scenario, seed, t, attempt).random() < s.audit_frac:
                    # FR19's small labelled audit: a rare true label, fed straight to the rule (never through
                    # the label-free cross-check machinery). Costed like a check at audit_price.
                    ap = s.audit_price if s.audit_price >= 0 else s.mean_price
                    spend += ap
                    audits += 1
                    strat.observe_audit(checked, outcome, truly_correct)
                if ssv and checked and outcome != "loud":
                    # B13 (31 Oct 2026): SSV-style weak/strong verification (Kiyani et al., 2026). Only strategies
                    # with ssv = True reach this branch, so earlier results are unchanged.
                    flagged = outcome == "caught"
                    correct = truly_correct or outcome == "ok"
                    act = strat.ssv_action(cur, flagged)
                    if act == "SV":
                        j = strat.crosscheck_tool(ctx)
                        spend += s.eff_price(j)
                        crosschecks += 1
                        alt = env.call(j, t, attempt, False)
                        strat.observe(j, False, alt == "loud")
                        if alt == "loud":
                            act = "R" if flagged else "A"          # no comparison: fall back to the weak verdict
                        else:
                            agree = env.agree(cur, j, t, correct, alt) if env_agree else (correct and alt == "ok")
                            if not env_agree and s.xc_shared > 0 and not correct and alt == "leak" and \
                                    _rng("xcshared", scenario, seed, t, attempt).random() < s.xc_shared:
                                agree = True                         # Core 4: shared mistake
                            strat.ssv_feedback(1 if agree else 0)
                            strat.observe(cur, True, not agree)
                            fa_resolved += int(agree and flagged)
                            step_ok = True
                            if not agree and alt == "leak":
                                leaked = True                        # the alternative's wrong output is used
                            break
                    strat.observe(cur, True, flagged)
                    if act == "A":
                        step_ok = True
                        if not correct:
                            leaked = True
                        break
                    continue                                         # "R": reject and retry
                if outcome == "caught" and reverify_k > 0:
                    # re-verification of the same output (strategies modelled on VRR-Stop): re-ask the checker,
                    # then accept or reject the output from the votes
                    votes, prev = [True], True
                    for j in range(1, reverify_k + 1):
                        if not strat.wants_recheck(cur, votes):
                            break
                        spend += s.check_price
                        checks += 1
                        rechecks += 1
                        prev = env.recheck(cur, t, attempt, j, prev, truly_correct)
                        votes.append(prev)
                    if strat.accept(cur, votes):
                        outcome = "ok" if truly_correct else "leak"
                        strat.observe(cur, checked, False, kind="none")
                        if outcome == "ok":
                            step_ok = True
                            break
                        leaked = True                   # a wrong output accepted after re-verification
                        step_ok = True
                        break
                if outcome == "caught" and xcheck and checked:
                    # rule v5 / B12 (27 Oct 2026): run the flagged step on the alternative tool and compare outputs.
                    # Only strategies with crosscheck = True reach this branch, so earlier results are unchanged.
                    j = strat.crosscheck_tool(ctx)
                    a_hat = strat.alt_mean(j)
                    spend += s.eff_price(j)
                    crosschecks += 1
                    alt = env.call(j, t, attempt, False)      # 'ok', 'loud' or 'leak' (silently wrong)
                    strat.observe(j, False, alt == "loud", kind="loud" if alt == "loud" else "none")
                    if alt == "loud":
                        strat.observe(cur, checked, True, kind="flag_altloud", a=a_hat)
                        continue                                # no comparison possible: retry as before
                    agree = truly_correct and alt == "ok"
                    if env_agree:                               # real comparison of the two answers (Core 1, 31 Oct)
                        agree = env.agree(cur, j, t, truly_correct, alt)
                    elif s.xc_shared > 0 and not truly_correct and alt == "leak" and \
                            _rng("xcshared", scenario, seed, t, attempt).random() < s.xc_shared:
                        agree = True                            # Core 4: both wrong in the same way, so they agree
                    if s.xc_noise > 0 and _rng("xcnoise", scenario, seed, t, attempt).random() < s.xc_noise:
                        agree = not agree                       # stress test: the comparison itself is wrong
                    if getattr(strat, "third_source", False) and s.third_source_frac > 0 and \
                            _rng("thirduse", scenario, seed, t, attempt).random() < s.third_source_frac:
                        # FR19: a third source (a different model family) on a few flags. Label-free: the rule
                        # is told only whether it confirmed or disputed the two-source verdict, never the truth.
                        tp = s.third_check_price if s.third_check_price >= 0 else s.check_price
                        spend += tp
                        third_checks += 1
                        shared_event = agree and not truly_correct
                        third_says_correct = env.third_source(t, attempt, truly_correct, shared_event)
                        third_confirms = third_says_correct if agree else (not third_says_correct)
                        strat.observe_third(agree, third_confirms)
                    if agree:                                   # outputs agree: the original output is kept
                        strat.observe(cur, checked, False, kind="flag_agree", a=a_hat)
                        fa_resolved += int(truly_correct)
                        step_ok = True
                        if not truly_correct:
                            leaked = True                       # a wrong output kept after a false agreement
                        break
                    strat.observe(cur, checked, True, kind="flag_disagree", a=a_hat)
                    step_ok = True                              # the alternative's output is used
                    if alt == "leak":
                        leaked = True
                    break
                strat.observe(cur, checked, outcome in ("loud", "caught"), kind=outcome)
                if outcome == "ok":
                    step_ok = True
                    break
                if outcome == "leak":                   # silent failure passed unchecked
                    leaked = True
                    step_ok = True                      # the agent believes the step succeeded
                    break
            if not step_ok:                             # retries exhausted on detected failures
                failed = True
                fa_failed += int(step_fa)               # a false alarm took part in this failure
                tool_at[t + 1:(task + 1) * S] = cur
                break
        t = (task + 1) * S
        if leaked:
            leaks += 1
        elif failed:
            unrecovered += 1
        else:
            successes += 1

    # switch delay (S1, S2): calls from the true rate crossing the line to leaving the primary tool
    delay = math.nan
    a = 0
    lines = np.array([true_line(s, env, a, S, tt, s.switch_cost) for tt in range(T)])
    below = np.where(env.p[a] < lines)[0]
    if len(below) and below[0] > 0 and tool_at[below[0] - 1] == a:
        t_cross = below[0]
        left = np.where((np.arange(T) >= t_cross) & (tool_at != a))[0]
        delay = float((left[0] if len(left) else T) - t_cross)

    n = s.n_tasks
    out = dict(
        strategy=strategy_name, scenario=scenario, seed=seed,
        q=s.q_true, check_frac=s.check_frac,
        spend=spend, successes=successes, leaks=leaks, unrecovered=unrecovered,
        cost_per_success=spend / successes if successes else math.inf,
        total_loss_per_task=(spend + s.leak_loss * leaks) / n,
        # also charges one task cost for a task that ends in a KNOWN failure (it has to be redone)
        total_loss_fail=(spend + s.leak_loss * leaks + s.task_cost * unrecovered) / n,
        fail_rate=unrecovered / n, false_alarms_per_task=false_alarms / n,
        checks_per_task=checks / n, switches=switches,
        false_switches_per_1000=1000.0 * false_switches / n,
        leak_rate=leaks / n, switch_delay=delay,
        crossing_share=(crossing_checks / checks) if checks else math.nan,
        # part E (24 Oct 2026): cost split and false-alarm effects
        fa_failed_rate=fa_failed / n, rechecks_per_task=rechecks / n,
        switch_spend_per_task=s.switch_cost * paid_switches / n,
        tool_check_spend_per_task=(spend - s.switch_cost * paid_switches) / n,
        leak_cost_per_task=s.leak_loss * leaks / n, fail_cost_per_task=s.task_cost * unrecovered / n,
        crosschecks_per_task=crosschecks / n, fa_resolved_per_task=fa_resolved / n,   # rule v5 (27 Oct 2026)
        third_checks_per_task=third_checks / n, audits_per_task=audits / n,            # rule v5.1 (6 Nov 2026)
        fallback_share=fallback_calls / checks if checks else math.nan,
    )
    cm = getattr(strat, "cm", None)
    if cm is not None:
        out.update(f_hat=cm.f_mean, q_hat_cm=cm.q_mean, cm_obs=cm.n)
    sigma_hat = getattr(strat, "sigma_hat", None)
    if sigma_hat is not None:
        out["sigma_hat"] = sigma_hat
    if hasattr(strat, "retests"):                           # FR18 (added 10 Nov 2026)
        out["retests"] = strat.retests
    rho_hat = getattr(strat, "rho_hat", None)               # FR20 (added 9 Nov 2026)
    if rho_hat is not None:
        out["rho_hat"] = rho_hat
    if record:
        out["trace"] = trace
    return out

"""
Hand-rolled property-based testing — no external library.
Shows the core idea: generate random inputs, assert a relationship, report failure.
Uses stdlib `random` only.

Domain: ideal gas law  P = nRT / V

Copy this file and adapt:
  1. Replace `pressure(n, T, V)` with your function under test.
  2. Replace `rand_pos()` with generators appropriate for your domain.
  3. Replace each check_* function with a property or MR that must hold.
  4. Run with: python property_test_plain.py

You lose automatic shrinking (Hypothesis does this for you), but the
generate-and-check loop is identical. The manual `shrink()` function below
illustrates the mechanism: try smaller inputs that still fail.
"""

import random
import sys

R = 8.314  # J / (mol·K)
SEED = 42
NUM_TRIALS = 2000


def pressure(n, T, V):
    """Ideal gas law: P = nRT / V"""
    return (n * R * T) / V


# ADAPT: change lo / hi to match your domain.
def rand_pos(lo=0.01, hi=1000.0):
    return random.uniform(lo, hi)


# ── Manual shrink: when we find a bad triple, try halving each value ──────────
def shrink(n, T, V, predicate, steps=20):
    """Naive one-at-a-time shrink toward smaller values that still fail.

    `predicate(n, T, V)` returns True when the property PASSES.
    We keep halving each variable while the property still fails (predicate is False).
    Hypothesis does this automatically and more thoroughly.
    """
    for _ in range(steps):
        improved = False
        for cand in [(n / 2, T, V), (n, T / 2, V), (n, T, V / 2)]:
            cn, cT, cV = cand
            if cn > 1e-9 and cT > 1e-9 and cV > 1e-9 and not predicate(cn, cT, cV):
                n, T, V = cn, cT, cV
                improved = True
                break
        if not improved:
            break
    return n, T, V


# ── Property 1: absolute invariant (P > 0) ───────────────────────────────────
def check_positivity():
    """Property: P > 0 for all positive n, T, V."""
    n, T, V = rand_pos(), rand_pos(), rand_pos()
    P = pressure(n, T, V)
    ok = P > 0
    info = {"property": "P > 0", "inputs": (n, T, V), "got": P}
    return ok, info


# ── Property 2: scaling MR (doubling n doubles P) ────────────────────────────
def check_scaling():
    """Metamorphic relation (scaling): pressure(2n, T, V) / pressure(n, T, V) == 2.0"""
    n, T, V = rand_pos(), rand_pos(), rand_pos()
    p1 = pressure(n, T, V)
    p2 = pressure(2 * n, T, V)
    ratio = p2 / p1
    ok = abs(ratio - 2.0) < 1e-9
    info = {"property": "2n → 2P", "inputs": (n, T, V), "ratio": ratio}
    return ok, info


# ── Property 3: Boyle's law  P1*V1 == P2*V2 (conservation MR) ───────────────
def check_boyle():
    """Metamorphic relation (conservation): Boyle's law at fixed n, T."""
    n, T = rand_pos(), rand_pos()
    V1, V2 = rand_pos(), rand_pos()
    p1, p2 = pressure(n, T, V1), pressure(n, T, V2)
    product1 = p1 * V1
    product2 = p2 * V2
    rel_err = abs(product1 - product2) / product1
    ok = rel_err < 1e-9
    info = {
        "property": "P1*V1 == P2*V2",
        "inputs": (n, T, V1, V2),
        "P1*V1": product1,
        "P2*V2": product2,
        "rel_err": rel_err,
    }
    return ok, info


def run_all(num_trials=NUM_TRIALS):
    random.seed(SEED)
    all_passed = True

    tests = [
        ("Positivity  (P > 0)", check_positivity),
        ("Scaling MR  (2n → 2P)", check_scaling),
        ("Boyle's law (P1V1 == P2V2)", check_boyle),
    ]

    for name, check_fn in tests:
        failed_info = None
        for _ in range(num_trials):
            ok, info = check_fn()
            if not ok:
                failed_info = info
                break

        if failed_info is not None:
            d = failed_info
            prop = d.get("property", name)
            inputs = d.get("inputs", "?")
            extra = {k: v for k, v in d.items() if k not in ("property", "inputs")}
            print(f"FAIL  {name}")
            print(f"      Property: {prop}")
            print(f"      Inputs:   {inputs}")
            for k, v in extra.items():
                print(f"      {k}: {v}")
            all_passed = False
        else:
            print(f"PASS  {name}  ({num_trials} trials)")

    return all_passed


if __name__ == "__main__":
    passed = run_all()
    if passed:
        print(f"\nAll properties passed over {NUM_TRIALS} random trials each.")
    else:
        sys.exit(1)

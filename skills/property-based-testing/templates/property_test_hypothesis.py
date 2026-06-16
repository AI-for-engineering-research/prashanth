"""
Property-based tests for the ideal gas law: P = nRT / V
Uses the Hypothesis library to generate thousands of random inputs automatically.

Metamorphic relations (MRs) express RELATIONSHIPS between outputs,
so we never need to know the "correct" output for any specific input.

Copy this file into your test suite and adapt:
  1. Replace `pressure(n, T, V)` with your function under test.
  2. Replace the `pos_float` strategy with physically sensible ranges for your domain.
  3. Replace each test body with a property or MR that must hold for your function.

Run with:
    pytest property_test_hypothesis.py -v
"""

import pytest
from hypothesis import given, settings
import hypothesis.strategies as st

R = 8.314  # J / (mol·K)


def pressure(n, T, V):
    """Ideal gas law: P = nRT / V"""
    return (n * R * T) / V


# --- Strategy: physically sensible ranges ---
# ADAPT: change min_value / max_value to match your domain.
# Always set allow_nan=False, allow_infinity=False for numerical code.
pos_float = dict(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False)


# --- Property 1: Absolute invariant (no oracle needed) ---
@given(
    n=st.floats(**pos_float),
    T=st.floats(**pos_float),
    V=st.floats(**pos_float),
)
@settings(max_examples=500)
def test_pressure_is_positive(n, T, V):
    """Property: P > 0 for all positive n, T, V.

    This is an absolute invariant — it holds for every input, no relation needed.
    If this fires, the implementation returned zero or negative pressure.
    """
    P = pressure(n, T, V)
    assert P > 0, (
        f"Positivity property failed: n={n}, T={T}, V={V} → P={P}"
    )


# --- Property 2: Scaling / linearity metamorphic relation ---
@given(
    n=st.floats(**pos_float),
    T=st.floats(**pos_float),
    V=st.floats(**pos_float),
)
@settings(max_examples=500)
def test_doubling_n_doubles_pressure(n, T, V):
    """Metamorphic relation (scaling): double the moles → double the pressure.

    MR: pressure(2n, T, V) / pressure(n, T, V) == 2.0
    We never compute the "expected" pressure — we check a ratio between two runs.
    Hypothesis will shrink this to the smallest n, T, V that breaks the ratio.
    """
    p1 = pressure(n, T, V)
    p2 = pressure(2 * n, T, V)
    ratio = p2 / p1
    assert abs(ratio - 2.0) < 1e-9, (
        f"Scaling MR failed: doubling n should double P. "
        f"n={n:.4f}, T={T:.4f}, V={V:.4f} → P1={p1:.6f}, P2={p2:.6f}, ratio={ratio:.10f}"
    )


# --- Property 3: Conservation metamorphic relation (Boyle's law) ---
@given(
    n=st.floats(**pos_float),
    T=st.floats(**pos_float),
    V1=st.floats(**pos_float),
    V2=st.floats(**pos_float),
)
@settings(max_examples=500)
def test_boyles_law(n, T, V1, V2):
    """Metamorphic relation (conservation): Boyle's law P*V = constant at fixed n, T.

    MR: P1*V1 == P2*V2   (both equal nRT)
    Two different volumes at the same n, T must give pressures whose P*V product is equal.
    This tests the structure of the formula without knowing the answer for any specific input.
    """
    p1 = pressure(n, T, V1)
    p2 = pressure(n, T, V2)
    product1 = p1 * V1
    product2 = p2 * V2
    rel_err = abs(product1 - product2) / product1
    assert rel_err < 1e-9, (
        f"Boyle's law MR failed: P1*V1 should equal P2*V2 at fixed n, T. "
        f"n={n:.4f}, T={T:.4f}, V1={V1:.4f}, V2={V2:.4f} "
        f"→ P1*V1={product1:.6f}, P2*V2={product2:.6f}, rel_err={rel_err:.2e}"
    )

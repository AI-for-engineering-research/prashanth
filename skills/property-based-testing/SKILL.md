---
name: property-based-testing
description: Use when writing or improving tests, testing scientific or numerical code, when a codebase lacks coverage beyond hand-picked examples, when property-based testing or metamorphic testing come up, or when Hypothesis (Python) or Supposition.jl (Julia) are mentioned. Also use when an agent is about to write tests that just encode the implementation's output, or when there is no ground-truth oracle for the function under test.
---

# Property-Based and Metamorphic Testing

## When to use PBT/MT vs example tests

Use **example-based tests** when: the expected output for a specific input is known and stable (e.g., parsing a fixed string, a lookup table, a regression value).

Use **property-based tests (PBT)** when: a function should satisfy an invariant across all valid inputs — "P > 0 for any positive n, T, V" — and you want the framework to search for counterexamples automatically.

Use **metamorphic tests (MT)** when: there is no oracle — you cannot compute the expected output, but you know a relationship that must hold between two or more runs (e.g., "doubling the moles doubles the pressure"). This is the correct tool for scientific/research/numerical code.

**The oracle problem:** when you write the code and then write an example test that calls the same code and asserts its output, the test encodes what the code happens to produce — not what it should produce. A bug that was present when you wrote the test will pass forever. Metamorphic relations break this circularity by checking consistency across runs, not correctness of any single output.

---

## Choosing a property: the hard part

The hardest part of PBT is picking the right property. Use this question as your guide:

> "What must always be true about the output, regardless of the specific input?"

If you can't answer that, reach for a **metamorphic relation**: what relationship must hold between `f(x)` and `f(x2)` when `x2` is a transformed version of `x`?

See `reference/property-catalog.md` for the full catalog with one-line examples. Short version:

| Relation | Trigger phrase | Example |
|---|---|---|
| Invariance | "permuting inputs shouldn't change output" | sort(shuffle(x)) == sort(x) |
| Scaling / linearity | "twice the input → twice the output" | pressure(2n,T,V) / pressure(n,T,V) ≈ 2 |
| Symmetry | "swapping inputs leaves output unchanged" | sin(π−x) = sin(x) |
| Idempotence | "applying twice = applying once" | sort(sort(x)) == sort(x) |
| Inverse / round-trip | "decode(encode(x)) = x" | kelvin_to_celsius(celsius_to_kelvin(C)) ≈ C |
| Conservation | "total is preserved" | sum of probabilities = 1.0 after softmax |
| Monotonicity | "more of X → more (or less) of Y, never the reverse" | Brayton η increases with pressure ratio |
| Subset | "filtering returns a subset" | len(filter(results)) <= len(results) |

---

## How to write them

### Python — Hypothesis

```python
from hypothesis import given, settings
import hypothesis.strategies as st

pos_float = dict(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False)

@given(n=st.floats(**pos_float), T=st.floats(**pos_float), V=st.floats(**pos_float))
@settings(max_examples=500)
def test_doubling_n_doubles_pressure(n, T, V):
    """MR (scaling): pressure(2n, T, V) / pressure(n, T, V) == 2.0"""
    p1 = pressure(n, T, V)
    p2 = pressure(2 * n, T, V)
    assert abs(p2 / p1 - 2.0) < 1e-9, (
        f"Scaling MR failed: n={n}, T={T}, V={V} → ratio={p2/p1:.6f}, expected 2.0"
    )
```

Key points:
- `@given` declares the strategy (input generator). Keep ranges physically sensible — `allow_nan=False`, `allow_infinity=False`, positive lower bounds.
- `@settings(max_examples=500)` raises the trial count from the default (100). Use 200-1000 for numerical code.
- Hypothesis uses **integrated shrinking**: when a test fails, it automatically reduces the input to a minimal counterexample before reporting it. You don't write a shrink function.
- The assertion message should state: the property name, the inputs, the expected relation, and the actual values. This helps an agent self-correct.

Full template: `templates/property_test_hypothesis.py`

### Python — no library (hand-rolled)

Use this when you can't install Hypothesis, or to understand the mechanism:

```python
import random
for _ in range(2000):
    n, T, V = rand_pos(), rand_pos(), rand_pos()
    p1 = pressure(n, T, V)
    p2 = pressure(2 * n, T, V)
    ratio = p2 / p1
    assert abs(ratio - 2.0) < 1e-9, f"Scaling MR: ratio={ratio:.6f}"
```

You lose automatic shrinking, but the generate-and-check loop is the same idea. You can add a manual shrink loop (see `templates/property_test_plain.py`).

Full template: `templates/property_test_plain.py`

### Julia — Test stdlib (hand-rolled)

Avoid downloading new libraries

```julia
using Test
N = 1000
@testset "Monotonic efficiency (MR)" begin
    for _ in 1:N
        r1 = rand_r(1.1, 20.0)
        r2 = rand_r(r1 + 0.1, 40.0)   # r2 > r1
        γ  = rand_γ()
        @test brayton_efficiency(r2, γ) > brayton_efficiency(r1, γ)
    end
end
```

Use `isapprox(a, b; rtol=1e-10)` or `≈` (typed `\approx`) for float comparisons. Tests live in `test/runtests.jl`. Run with `julia --project test/runtests.jl` or `Pkg.test()`.

For a full PBT library in Julia: **Supposition.jl** (active, Hypothesis-inspired, integrated shrinking) at https://github.com/Seelengrab/Supposition.jl. Check with user before adding to the codebase.

Full template: `templates/property_test_julia.jl`

---

## Assertion design for agent self-correction

A failing property test is only useful if the message tells you what went wrong. Include:

1. The property name (what invariant was being checked)
2. The exact inputs that triggered failure
3. The expected relationship
4. The actual values

Bad: `assert p2 > p1`

Good:
```python
assert p2 > p1, (
    f"Monotonicity MR: higher pressure ratio should give higher efficiency. "
    f"r1={r1:.4f}, r2={r2:.4f}, γ={γ:.4f} → η1={p1:.6f}, η2={p2:.6f}"
)
```

When Hypothesis shrinks, it will present this message with the minimal failing inputs already substituted in.

---

## Workflow: adding property tests to a codebase

1. **Look at the existing test style.** What framework is in use? What test patterns already exist? Copy the style — agents will imitate it.
2. **Pick 2-4 functions** that are core to the codebase's domain logic, especially numerical/scientific functions.
3. **For each function, ask:** "What must always be true about the output?" List 1-3 candidates. If you can't think of one, reach for a metamorphic relation from `reference/property-catalog.md`.
4. **Prefer a metamorphic relation when there's no oracle.** You don't need to know the right answer — just that two related runs must agree.
5. **Set physically sensible strategy bounds.** Avoid inputs that are mathematically valid but physically meaningless (negative temperatures, zero volumes). Constrain with `min_value`/`max_value` in Hypothesis or explicit bounds in hand-rolled loops.
6. **Run the tests.** Read the minimal counterexample carefully. If the property fires on every run, the property is wrong (too strict) or the implementation is wrong — distinguish these.
7. **Fix the implementation or refine the property.** Commit with a comment per property: what invariant it checks and why.

---

## Common pitfalls

| Pitfall | Fix |
|---|---|
| `assert a == b` on floats | Use `abs(a - b) < tol` or `isapprox`. Tolerance must be physically motivated, not arbitrary. |
| Test re-encodes the implementation | The test calls `compute(x)` and asserts `compute(x) == compute(x)`. Write a *relation*, not a value check. |
| Over-broad strategies hit unphysical inputs | Negative Kelvin, zero volume, division by zero. Constrain ranges from the start. |
| Property is trivially true | `assert len(x) >= 0` always passes. Push the property: check a relationship that could fail if the implementation has a sign error or wrong branch. |
| Tolerance too tight for float arithmetic | 1e-15 will flake on any non-trivial computation. Use 1e-9 to 1e-10 for double-precision physics. |
| Only one property per function | Write at least 2: one absolute invariant (positivity, bounds) and one metamorphic relation. |

---

## Files in this skill

- `SKILL.md` — this file
- `reference/property-catalog.md` — full metamorphic relation catalog with examples and "how to spot" guidance
- `reference/sources.md` — verified citations and links
- `templates/property_test_hypothesis.py` — Hypothesis template (copy and adapt)
- `templates/property_test_plain.py` — no-library hand-rolled template
- `templates/property_test_julia.jl` — Julia Test stdlib template

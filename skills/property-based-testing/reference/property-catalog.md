# Metamorphic Relation Catalog

A metamorphic relation (MR) is a property that holds across two or more calls to the same function, when inputs are related by a known transformation. Use MRs when you have no oracle — you don't know the right answer, but you know what must be consistent.

**How to spot one:** ask "if I change the input in this specific way, how must the output change?" The answer is the MR.

---

## Invariance

The output does not change when the input is transformed in a way that should be irrelevant.

- **Permutation invariance:** `sort(shuffle(x)) == sort(x)` — shuffling before sorting gives the same result
- **Attribute permutation (ML):** classifier output must not change if you reorder feature columns that carry the same information
- **Volume invariance (speech-to-text):** transcription must be the same at 50% and 100% volume

**How to spot:** "the transformation I'm applying should not matter to the result." If it does matter, that's a bug.

---

## Scaling / Linearity

Scaling the input by a constant scales the output by a predictable factor.

- `pressure(2n, T, V) / pressure(n, T, V) ≈ 2.0` — doubling moles doubles pressure (ideal gas)
- `f(k * x) == k * f(x)` — any linear function
- `classifier(scale * image) == classifier(image)` — pixel scaling should not change a class prediction

**How to spot:** "if I multiply this input by k, does the output multiply by k (or k^n, or stay the same)?"

---

## Symmetry

Swapping or reflecting inputs leaves the output unchanged (or predictably changed).

- `sin(π - x) == sin(x)` — the canonical textbook MR for trigonometric functions
- `distance(A, B) == distance(B, A)` — distance is symmetric
- `correlation(x, y) == correlation(y, x)` — statistical correlation is symmetric

**How to spot:** "does the mathematical definition treat two inputs identically?" If so, swapping them is an MR.

---

## Idempotence

Applying the function twice gives the same result as applying it once.

- `sort(sort(x)) == sort(x)` — sorting an already-sorted list is a no-op
- `normalize(normalize(v)) ≈ normalize(v)` — normalizing a unit vector leaves it unchanged
- `unique(unique(x)) == unique(x)` — deduplication is idempotent

**How to spot:** "does this operation reach a fixed point?" If running it again should not change anything, idempotence is the MR.

---

## Inverse / Round-trip

Applying a function and its inverse recovers the original input.

- `kelvin_to_celsius(celsius_to_kelvin(C)) ≈ C` — temperature unit conversion round-trip
- `decode(encode(x)) == x` — serialization round-trip
- `decompress(compress(data)) == data` — lossless compression round-trip
- `isentropic_ratio(r, γ) * isentropic_ratio(1/r, γ) ≈ 1.0` — compress then expand returns to start

**How to spot:** "does this function have an inverse?" If yes, the composition should be the identity.

---

## Conservation

A quantity that must be preserved across transformations.

- `sum(softmax(x)) ≈ 1.0` — probability distribution sums to 1
- `total_mass_before == total_mass_after` — mass conservation in a physics simulation
- `P1 * V1 ≈ P2 * V2` at fixed n, T — Boyle's law (the product nRT is conserved)
- `sum(portfolio_weights) == 1.0` — portfolio allocations sum to 100%

**How to spot:** "what physical or mathematical quantity is conserved in this domain?" That's the MR.

---

## Monotonicity

Increasing one input variable should increase (or decrease) the output, never reverse direction.

- `brayton_efficiency(r2, γ) > brayton_efficiency(r1, γ)` when `r2 > r1` — Brayton cycle efficiency increases with pressure ratio
- `classifier_confidence(more_signal) >= classifier_confidence(less_signal)` — adding relevant signal should not hurt confidence
- `area(larger_rectangle) >= area(smaller_rectangle)` — area increases with dimensions

**How to spot:** "does a domain invariant say 'more of X always gives more (or less) of Y'?" That ordering constraint is the MR. Generate pairs `(x1, x2)` where `x1 < x2` and check that `f(x1) < f(x2)` (or `>=`, depending on the direction).

---

## Subset / Filter consistency

After filtering or restricting, the result must be a subset of the unfiltered result.

- `len(search(query, filters=["cheap"])) <= len(search(query))` — adding a filter cannot increase results
- `all(x in original_set for x in filtered_set)` — every filtered item appeared in the full set
- `len(results_with_date_range) <= len(all_results)` — date-range filter returns a subset

**How to spot:** "does this operation restrict or filter?" The output must be contained in the input.

---

## Scientific / Physics examples

These appear in scientific computing where oracles are unavailable:

| Domain | MR | What to check |
|---|---|---|
| Ideal gas | Scaling | `P(2n,T,V) / P(n,T,V) ≈ 2` |
| Ideal gas | Boyle's law | `P1*V1 ≈ P2*V2` at fixed n, T |
| Adiabatic compression | Monotonicity | Compressing gas (V2 < V1) must raise T |
| Brayton cycle | Monotonicity | Higher pressure ratio → higher thermal efficiency |
| Temperature conversion | Round-trip | `K→C→K` and `C→K→C` recover original |
| Isentropic process | Inverse | Compress by r, expand by r → back to start |
| PDE heat equation | Symmetry | Symmetric boundary conditions → symmetric solution |
| Graph / shortest path | Symmetry | `dist(A,B) == dist(B,A)` in undirected graphs |
| Graph / shortest path | Monotonicity | Adding an edge cannot increase shortest path |

---

## How to generate input pairs for an MR

Most MRs require a "source" input and a "follow-up" input derived from it:

```python
# Monotonicity: generate the pair (r1, r2) together so r2 > r1 holds in the SAME trial.
# Returning two separate strategies and using @given(r1=..., r2=...) would draw them
# independently, and the r2 > r1 link would be lost.
r_pair = st.floats(min_value=1.1, max_value=20.0).flatmap(
    lambda r1: st.tuples(st.just(r1), st.floats(min_value=r1 + 0.01, max_value=40.0))
)
# usage: @given(pair=r_pair)  then  r1, r2 = pair  in the test body

# Scaling: generate x, derive 2x
x = st.floats(min_value=0.01, max_value=1000.0)
# then in the test body: x2 = 2 * x

# Round-trip: generate x, apply f, apply f_inverse
C = st.floats(min_value=-200.0, max_value=2000.0)
# then: K = celsius_to_kelvin(C); C2 = kelvin_to_celsius(K)
```

For hand-rolled loops, just generate x and compute x2 inside the loop body.

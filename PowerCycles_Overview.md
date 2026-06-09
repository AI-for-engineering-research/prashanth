# PowerCycles.jl — Project Overview

A v0.1 Julia package (`PowerCycles`) for advanced propulsion system
analysis, currently targeting a single-spool turbojet.

---

## Why a new tool

Gas-turbine cycle analysis today is dominated by two main tools: NPSS and pyCycle[^othertools].
Unfortunately, neither is fully satisfying. NPSS has a long history and is maintained by a consortium, but it cannot leverage the latest computational advances. pyCycle is more modern, built on the OpenMDAO framework, but it has its own set of problems. It is significantly slower due to Python and OpenMDAO overhead, and the learning curve is steep—you need deep knowledge of NPSS or OpenMDAO to use it effectively.

[^othertools]: There are a scattering of other tools that have been developed over the years. GasTurb is a very popular GUI based tool. That was actually the first tool I used in my masters for something like this. There's also other tools that are used in-house by the OEMs etc.

I ran a [benchmark study](baseline_performance_report.html) comparing the two tools, and performance depends heavily on the use case. pyCycle benefits from **analytical gradients** (requiring only ~4 Newton iterations to converge) but incurs heavy **per-iteration overhead** from OpenMDAO/Python, making each solve slow. NPSS requires many more iterations (~19–24) but each iteration is much cheaper.

It is also really hard to do non-traditional components like electric machines in an effective way. I've done it before, people have done it but it is not nice. We need to think about how to integrate these systems together in a more efficient manner

The motivation for PowerCycles.jl is therefore a cycle tool that might solve this gap - enabling faster and more robust evaluation of novel propulsion system architectures by leveraging ideas like autodiff and symbolics.

## What

I want to evaluate if there is a space to build a new Engine modeling framework that (a) is Permissibly licensed, (b) delegates thermodynamics to a single, consistent
package (`IdealGasThermo.jl`) to remove that aspect of ambiguity, and
(c) exploits Julia's solver ecosystem (`NonlinearSolve`, maybe `ModelingToolkit`) to
get both fast iterations *and* good convergence (potentially via autodiff). Initially, I considered whether Julia is the right tool for this, but after a long discussion with AI, I am convinced that it might actually be the perfect use case.
I also want this to be AI conducive or Agent compatible from the start[^agent].

[^agent]: Tbh I don't exactly know what this means yet. I've noticed that the Frontier LLMs can really discover new tools and use them quite effectively, even if they've never seen the tool before in their training. So this might mean something like helpful documentation, tests and command line `--help` arguments perhaps. 

## How

- **Thermo is not reliant on CEA type calculations that are mostly not relevant for the lower temperatures of gas type in combustion compared to rocket engines..** All properties come from
  `IdealGasThermo.jl` (no local polynomial core)
- Do a test case for a simple **Off-design closure** for the turbojet is a 4-unknown / 4-residual nonlinear
  system:
  - unknowns: $$\beta_c$$, $$\beta_t$$, $$\hat{N}$$, $$T_{t4}$$
  - residuals: compressor corrected-flow map match, turbine corrected-flow map
    match, shaft power balance, thrust closure
  - synthetic maps are scaled to a realistic operating region before the
    off-design solve.
- **Two solve paths:** a direct `NonlinearSolve.jl` Newton solve, plus a
  black-box MTK `NonlinearSystem` wrapping the identical residual equations
  (cross-check today, foundation for the future component graph). MTK needs to prove its worth.
- **Validation:** a property-style test suite (`test/`) with randomized tests and 
  invariants across thermo, components, maps, cycles, and solver.

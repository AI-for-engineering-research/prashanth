# PowerCycles.jl — Weekly Log

## Week 1

### Scoping and critical thinking (LLM-assisted)

I started by having a long discussion with Claude to
understand the problem space and refine my own thinking (some of this was more than a month ago). I used a structured
"grill me" interview process to pressure-test the idea rather than just collect
agreement. This pushed me to nail down several things:

- **Why this is a worthwhile project** — what the genuine gaps are in existing
  tooling, and whether a new package is actually justified.
- **Julia** is actually the right tool for this. Potentially. Some early tests need to be
  done to establish this.
- **Scope** — what the *first steps* should be versus the *final goal*, and how
  to keep v0.1 deliberately narrow (single-spool turbojet, delegated thermo) so
  the prototype stays simple.
- **Decision-gating** — how to systematically gate the process so I commit to a
  direction only after a prototype answers a specific question, rather than
  building everything speculatively.
- **Tool choice** — how to build initial prototypes that test whether
  ModelingToolkit (a large Julia package) is the right backbone here, or whether
  a lighter-weight approach to the nonlinear solve is more appropriate.

The discussion in particular forced me to think critically about scope
discipline and about how to evidence the tooling decision instead of assuming
it.

### Profiling NPSS and pyCycle

June 7th 2026

The next thing I did was systematically profile both **NPSS** and **pyCycle** on
an identical single-spool turbojet (sea-level static, component performance and
design drivers pinned identically across both tools) to isolate the
thermodynamic package and the solver behavior.[^configs] Full details are in
`baseline_performance_report.html`. Two interesting things were
revealed:

[^configs]: Six (tool, thermo package) configurations were tested: pyCycle in CEA and TABULAR;
    NPSS in GasTbl, Janaf, CEA, and allFuel. The cycle and design point are
    pinned identically — every remaining difference isolates the thermodynamic
    property package.

1. **pyCycle's analytical gradients give excellent convergence.** It reaches the
   design point in only **~4 Newton iterations**, versus **~19–24 iterations**
   for the NPSS packages.
2. **But OpenMDAO/Python overhead makes each pyCycle iteration very slow.** Per
   iteration, pyCycle is far more expensive than NPSS, so the iteration-count
   advantage is more than erased by per-iteration cost.

This immediately tells me that there is a gap that we can satisfy. If we had analytical derivatives or AD, we can get the iteration speed of NPSS and the convergence speed of pyCycle.

#### Selected numbers from the benchmark

Design-point convergence (identical pinned cycle):

| Configuration   | Design-pt runtime | Design-pt iters |
|-----------------|-------------------|-----------------|
| pyCycle CEA     | 4.65 s            | 4               |
| pyCycle TABULAR | 1.22 s            | 4               |
| NPSS CEA        | 2.05 s            | 22              |
| NPSS GasTbl     | 0.36 s            | 24              |
| NPSS Janaf      | 1.65 s            | 19              |
| NPSS allFuel    | 0.34 s            | 22              |


::figure{id="timing" caption="Per-solve median time on a log scale. Green = NPSS allFuel (fast equilibrium); red = pyCycle. The dashed marker is the 256× gap between pyCycle-CEA and NPSS-allFuel at equivalent thermodynamic accuracy."}

:::aside
**Key takeaway** — package choice *within* NPSS spans a ~178× per-iteration
range. This is expected because something like allFuel or GasTbl is effectively some form of look-up vs
an equilibrium solver like CEA.
:::

Off-design (12-point timed throttle line, all configs 12/12 converged):

- Per off-design solve, **NPSS-allFuel is ~599–2527x faster than pyCycle-CEA**
  (sub-ms vs ~1–2 s).

Robustness:

- Every NPSS configuration converged at every design and off-design point.
- **pyCycle-CEA failed to converge** at the envelope corner (alt = 25,000 ft,
  MN = 0.8), hitting maxiter.


**Takeaway:** the convergence-vs-throughput tradeoff (analytical gradients -
fewer iterations, but heavy per-iteration overhead) is exactly the gap a
Julia-native implementation should be able to close — cheap iterations *and*
good gradients/convergence — which directly motivates the PowerCycles.jl design.


## Week 2
### Building the website

I had practiced building a simple website for the class and wanted to demo it 
during the class but didn't really have time to do that. So instead I started looking into how I would really want to maintain my log. And one of the things I wanted to do is really use this as an opportunity to do both continuous documentation as well as interactive visualization that shows the progression of a project. And this is somewhat related to an idea I've been throwing around recently about how the way in which we communicate science can be improved right now. It might even have to change the role that journals play is an important piece, but is the format of how we actually present this research still the best way to do so.

:::aside
Tbh for something like this even a plain html write would be fine but, hey! This is fun with AI right?
:::

One tool that I've used in the past that is pretty cool is called Quarto ([example project](https://www.mit.edu/~prash/cs2a/)). Quarto has this really nice feature of how you can basically have code in-line that then gets executed and figures generated as the page is built or you can have the code along with what you're actually doing as well. This makes things very reproducible. It doesn't natively make it easy to insert Javascript interactive elements and things like that though. You also have to fight a lot with some of the style sheets to have fine grained control. I think that's the better tool to maintain something like this log tbh, but this is also an opportunity for me to learn new things. So I'm going to try building a custom workflow based on this tool that Ian told me about called Astro.

### Initial design choices
*2026-06-10 (Wed, 10th Jun)*

After a series of discussions, I decided to experiment and try something quickly that I definitely wouldn't have done if I was writing all the code myself.  I decided that I was going to let Claude build for me a very minimal, but ground up[^mtk], version of the system that can then be given to a nonlinear solver. The key question here is how do you go from an individual component to composing many of them into the residual matrix of Jacobians (which ends up being sparse for the typical engine solves).  
[^mtk]: I was very hesitant initially because people have done things like this. Julia has a whole framework called ModelingToolkit,  which is a generalizable package that uses symbolics to do a lot of smart things like reduce the system symbolically before actually computing the Jacobians using auto diff or symbolic differentiation as well.  However, the problem with something like this is that because it needs to fit everybody's use case, it actually ends up having a lot of machinery behind it.  This resonated with an idea that I've been playing around with in my head about how we could have hyper-specialized code now for individual projects because the cost of writing new code is come down dramatically.  So I decided to run with it here. 

 I decided to use a test-driven development approach via a skill I modified from [Matt Pocock's typecript](https://github.com/mattpocock/skills/tree/main/skills/engineering/tdd) focused skill to something more relevant to Julia and Python.  the model did pretty well actually. It did follow the test-driven development approach of creating the tests first, making sure they fail and then writing only the minimal amount of code that is required to make those tests pass. Doing this sequentially means that you actually build up nicely without a lot of code bloat.  Some of the tests are a bit iffy and... yes, they're technically tests, but they don't actually have very high quality. One example was where it built and solved a "nonlinear system" that just had an flow-start and a flow-end and the mass flows had to be matched. 

#### Showcasing work
One of the things I've realized by experimenting with the AI models is that it very quickly becomes quite fatiguing to review the amount of code that these models write.  After some initial frustration a while back, I realized that I just need to change the way I am thinking about this - the analogy came from thinking about how I interact with students. Typically when I meet with students to discuss research progress, they show me the work that they've done packaged in some easy-to-parse-way - graphs, flow-charts, diagrams, slides etc.  Only rarely when we are actually actively trying to debug something together are we really looking into the raw code. So why not ask the models to show their work! 

They love writing .md files but even better is to ask them to use html files. You can see the skill in my repo [visual-walkthrough](https://github.com/AI-for-engineering-research/prashanth/tree/main/skills/visual-walkthrough) and the full html page [here](../assets/evaluation_presentation.html).

![[20260610_flowchart.svg|Example of the flow chart Claude made for me.|wide|697]]

After some initial massaging it came up with something interesting that seems encouraging!  
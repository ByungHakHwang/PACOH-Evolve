# Discoveries Section - What Actually Evolves

Date: 2026-07-08

Purpose: revise the `Discoveries` section so that each example makes explicit
what object/code is evolved, what the evaluator checks, and what mathematical
result comes out. This is a planning note only; `main.tex` is not edited here.

Audience assumption: combinatorialists with little exposure to AI, shown before
a hands-on tutorial on Evolve-style coding agents. The section should be
concrete enough to make the mechanism believable, but not turn into a technical
seminar on any one discovery. Bruhat should remain a short closing example.

## Global Structure

Use the same three-line schema in every discovery:

```text
What evolves: ...
Evaluator: ...
Output / discovery: ...
```

This makes the section serve the tutorial goal: the audience should leave with
the idea that these systems do not evolve "mathematics" in the abstract. They
evolve executable code, and a mathematical evaluator selects the survivors.

Proposed order:

1. Overview slide: "Discoveries: what evolves?"
2. Cap set: priority function inside a greedy constructor.
3. Ramsey: graph-search programs for lower-bound witnesses.
4. Matrix multiplication: tensor-decomposition solver code.
5. Bruhat: short structural example, kept to one slide.

## Overview Slide

Add or repurpose a short table before the examples:

| Example | What evolves | Evaluator | Output |
|---|---|---|---|
| Cap set | A `priority` function used by a greedy constructor | Build a set and check the cap-set condition | A 512-cap in `(\mathbb{Z}/3\mathbb{Z})^8`, plus interpretable symmetry |
| Ramsey | Search algorithms that build graphs | Check no `K_r` and no independent `s`-set; score size and near misses | New lower-bound witness graphs |
| Matrix multiplication | Solver code for low-rank tensor decomposition | Run solver on matmul tensors; score lowest rank and reliability | Rank-48 algorithm for `4 x 4` complex matrix multiplication |
| Bruhat | Program generating pairs of permutations | Compute `d`-invariant across many `n` | Pattern leading to large Bruhat hypercubes |

This table should not replace the examples. It should give a mental index.

## Example 1 - Cap Set / FunSearch

Verified facts:

- FunSearch searches in function space: it pairs an LLM with an evaluator and
  evolves programs, not raw mathematical objects.
- For the cap-set experiment, the evolved code is the `priority` function in a
  fixed greedy skeleton.
- The greedy skeleton starts with an empty set and repeatedly adds the
  highest-priority vector that does not violate the cap-set constraint.
- Starting from a trivial constant function, FunSearch found a priority
  function that yields a cap set of size 512 in dimension 8.
- Inspecting the discovered code revealed a reflection pattern involving
  coordinates `i` and `-i`, which helped humans write a clearer explicit
  construction.

Recommended slide development:

1. Keep the problem slide, but make it brief.
2. Rename the current record slide to something like:
   `Example 1: Cap Set - from code to construction`
3. Keep the seed function slide:

   ```python
   def priority(v: tuple[int, ...], n: int) -> float:
       return 0.0
   ```

4. Keep or slightly improve the evolved-function slide, but add a top caption:

   ```text
   What evolves: only this priority function.
   The solver and the cap-set checker are human-written.
   ```

5. Add the evaluator line directly on the same or next slide:

   ```text
   Evaluator: run the greedy constructor, verify no 3-term AP, return set size.
   ```

What to avoid:

- Do not say FunSearch "proved" anything about optimality.
- Do not imply the LLM directly listed the 512 vectors.
- Do not overfocus on the admissible-set asymptotic result unless there is a
  separate slide for it. For this talk, the dimension-8 cap is the cleanest
  mechanism demo.

## Example 2 - Ramsey / AlphaEvolve

Verified facts:

- The Ramsey paper uses the graph formulation: to prove `R(r,s) > N`, exhibit a
  graph on `N` vertices with no `K_r` and no independent set of size `s`.
- AlphaEvolve is used as a meta-search procedure. It evolves search algorithms,
  not just adjacency matrices.
- The maintained population consists of search programs. An LLM mutation
  creates a new program `p_new`.
- Each program returns a primary graph `G1` and a larger "prospect" graph `G2`.
- `G1` must be valid. It is scored by size, with extra weight when it reaches or
  exceeds the previous state of the art.
- `G2` gives a near-miss signal: fewer forbidden cliques/independent sets gives
  a bonus, so the system can learn from almost-valid larger graphs.
- The paper reports nine improved lower bounds:
  `R(3,13)`, `R(3,18)`, `R(4,13)`, `R(4,14)`, `R(4,15)`,
  `R(4,16)`, `R(4,18)`, `R(4,19)`, `R(4,20)`.
- The discovered search algorithms are cell-specific and fall into families
  such as random/stochastic initialization, Paley/algebraic seeding,
  circulant/cyclic bootstrap, and hybrid/fractal/spectral seeding.

Recommended slide development:

1. Keep the basic Ramsey definition and small table.
2. Add one mechanism slide before the lower-bound table:

   ```text
   What evolves: a graph-search program p.

   p.run() returns:
     G1 = valid candidate graph
     G2 = larger near-miss graph

   Evaluator:
     - reject if G1 has a forbidden K_r or independent s-set
     - score |V(G1)|, with a boost past the previous bound
     - add a near-miss bonus from violations in G2
   ```

3. Keep the nine-result table, but label it explicitly as lower bounds:

   ```text
   Lower-bound witness size N, meaning R(r,s) > N.
   ```

4. Add one sentence after the table:

   ```text
   The surprise is not a single graph: it is one meta-algorithm producing many
   specialized graph-search programs.
   ```

What to avoid:

- Do not say AlphaEvolve improved the exact Ramsey numbers. These are lower
  bounds.
- Do not imply one universal search algorithm solved all cells. The paper says
  the resulting algorithms are specific to the corresponding cells.
- Do not spend time on the full taxonomy table unless the audience asks; one
  sentence is enough.

## Example 3 - Matrix Multiplication / AlphaEvolve

Verified facts:

- Matrix multiplication algorithms can be represented as low-rank tensor
  decompositions. The tensor rank is the number of scalar multiplications.
- AlphaEvolve started from a standard gradient-based tensor-decomposition
  algorithm, including initializer, reconstruction loss, and Adam optimizer.
- The evolved object was the solver code, not simply the final 48-term formula.
- Evaluation ran the evolved solver on matrix multiplication targets with
  multiple random seeds. Scores included the best lowest rank reached and the
  fraction of seeds reaching that rank.
- To avoid numerical false positives, the evaluation rounded decomposition
  entries to nearby integer or half-integer values and checked exactness.
- For `4 x 4` matrix multiplication, AlphaEvolve found a rank-48 algorithm for
  complex-valued matrices. The paper also reports state-of-the-art improvements
  for 14 matrix multiplication targets.
- The paper's example diff shows substantial code changes such as Adam to
  AdamW, modified complex initialization, gradient noise, parameter noise, and
  clipping schedules.

Recommended slide development:

1. Keep the callback to the opening hook:

   ```text
   Strassen x Strassen: 49 multiplications.
   AlphaEvolve: 48 multiplications for 4 x 4 complex matrix multiplication.
   ```

2. Replace the current "how was it found?" slide with a more precise version:

   ```text
   What evolves: the tensor-decomposition solver.
     - initializer
     - loss / optimization details
     - optimizer and hyperparameter sweep

   Evaluator:
     - run the solver on matmul tensors
     - score the lowest rank found and how reliably it is found
     - verify the rounded decomposition exactly

   Output:
     a rank-48 decomposition for the 4 x 4 complex matmul tensor.
   ```

3. If space allows, show a tiny diff rather than only prose:

   ```diff
   - return optax.adam(...)
   + return optax.adamw(..., weight_decay=...)
   ```

What to avoid:

- Do not say the result works over every field of characteristic 0. The verified
  AlphaEvolve result is a complex-valued rank-48 algorithm.
- Do not make "complex coefficients with magic cancellations" the main
  explanation. It is rhetorically useful but too vague; the mechanism is solver
  evolution plus exact verification.

## Example 4 - Bruhat / Keep Short

Verified facts:

- The paper studies large boolean intervals, or hypercubes, in Bruhat order of
  the symmetric group.
- The AlphaEvolve experiment did not simply optimize "hypercube size" directly.
  The authors searched for programs producing pairs of permutations with large
  Kazhdan-Lusztig `d`-invariant.
- Programs were evaluated across `n = 10` to `50`, averaging the resulting
  `d`-invariants.
- AlphaEvolve produced a highly interpretable pattern; the authors recognized
  the bit-reversal / dyadically well-distributed structure and proved the
  general theorem.
- For `n = 2^m`, the set of dyadically well-distributed permutations forms a
  Bruhat interval isomorphic to a hypercube of dimension `m 2^{m-1}`.

Recommended slide treatment:

Keep one slide only. Use it as a "beyond optimization" moral, but make the
mechanism accurate:

```text
What evolved: programs generating pairs of permutations.
Evaluator: compute the d-invariant for many n.
Output: a pattern that humans recognized as dyadically well-distributed
permutations and proved to give large Bruhat hypercubes.
```

Suggested closing line:

```text
AI suggested the pattern. Mathematicians turned it into a theorem.
```

What to avoid:

- Do not imply AlphaEvolve proved the theorem.
- Do not imply the original objective was directly "find a hypercube"; the paper
  explicitly notes that the large hypercube was found while optimizing the
  `d`-invariant.
- Do not add more Bruhat technical detail in the main talk. The current
  audience will benefit more from keeping this as a sharp structural example.

## Proposed Time Allocation Inside Discoveries

For a 40-minute pre-tutorial talk:

| Block | Slides | Time |
|---|---:|---:|
| Overview: what evolves? | 1 | 1 min |
| Cap set | 4 | 5-6 min |
| Ramsey | 3 | 4-5 min |
| Matrix multiplication | 2 | 3-4 min |
| Bruhat | 1 | 1-2 min |

Total: about 14-18 minutes, depending on pauses. This is enough detail to make
the examples concrete while preserving time for the mechanism and tutorial
bridge.

## Source Checklist

Primary sources checked:

- FunSearch Nature article:
  <https://www.nature.com/articles/s41586-023-06924-6>
- FunSearch paper PDF hosted by Google DeepMind:
  <https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/Mathematical-discoveries-from-program-search-with-large-language-models.pdf>
- Google DeepMind FunSearch blog:
  <https://deepmind.google/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/>
- AlphaEvolve arXiv paper:
  <https://arxiv.org/abs/2506.13131>
- AlphaEvolve PDF:
  <https://arxiv.org/pdf/2506.13131>
- Ramsey AlphaEvolve paper:
  <https://arxiv.org/abs/2603.09172>
- Ramsey AlphaEvolve PDF:
  <https://arxiv.org/pdf/2603.09172>
- Bruhat hypercubes paper:
  <https://arxiv.org/abs/2601.01235>
- Bruhat hypercubes PDF:
  <https://arxiv.org/pdf/2601.01235>


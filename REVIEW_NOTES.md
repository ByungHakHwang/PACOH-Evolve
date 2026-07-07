# Presentation Review Notes

## Audience assumption

The relevant audience is **mathematicians**, especially people already familiar
with AI and combinatorics. Earlier notes assuming middle/high-school math
teachers belong to a previous talk and should not guide this version.

Consequence: the talk does not need a long pedagogical ramp-up. It should be
clear, but not elementary.

## Working thesis

AlphaEvolve-style agents are not theorem provers. They are scalable
program-search systems for discovering constructions, heuristics, and sometimes
closed-form formulas when the mathematics admits a fast evaluator.

The core message should be:

> Do not trust the LLM. Trust the evaluator.

More precisely:

> The LLM proposes executable programs; the evaluator decides which programs
> survive.

## Main structural concern

The current deck contains several possible talks at once:

1. A talk about the architecture of evolutionary coding agents.
2. A talk about mathematical discoveries by AlphaEvolve/FunSearch.
3. A hands-on / educational OpenEvolve-style tutorial.

For this audience, the deck should prioritize (1) and (2). The hands-on angle
should be present only if it supports research formulation.

## Recommended emphasis

### Keep

- The Strassen hook. It is strong and gives a concrete mystery.
- The evaluator principle. This is the conceptual backbone.
- The cap set example. It is the cleanest FunSearch-style example.
- The Ramsey example. It is directly relevant to combinatorics and shows
  meta-search power.
- The matrix multiplication callback to the Strassen hook.

### Reduce

- Basic explanations of genetic algorithms.
- General toy examples such as TSP and circle packing, unless they are used only
  as quick intuition.
- Broad AI-for-math taxonomy if it takes time away from the main story.
- "LLMs hallucinate" as a generic warning. For this audience, the point should
  be why hallucination is controlled by executable evaluation.

### Compress Kakeya

Kakeya should not become a technical centerpiece. It is enough to say:

- AlphaEvolve was applied to the finite-field Kakeya problem.
- It found new explicit constructions / formulas.
- In one case the pipeline continued to proof generation and formal checking.
- This shows that the method can touch famous, serious mathematical problems.

Avoid spending much time on Dvir, Bukh--Chao constants, lower-order terms,
Nikodym sets, or arithmetic Kakeya unless the audience asks.

## Specific slide-level concerns

### AI for mathematics table

The table is useful, but the third column should not blur "LLM proof generator"
and "formal theorem prover." A better distinction:

- Pattern recognizer: finds patterns/conjectures from data.
- Coding agent: searches over programs/constructions using an evaluator.
- Proof agent: generates proof attempts / proof strategies.

The middle column is the talk.

### Genetic algorithms for mathematics

The slide should move faster. For this audience, the main point is not "what is
a GA?" but:

> Many combinatorial problems can be turned into a search over generators,
> ranked by a fast evaluator.

If examples remain, they should support the later examples rather than feel like
unrelated toy problems.

### What is actually being evolved?

This slide should probably use the same examples as the main discovery section:

- Cap set: priority function / greedy constructor.
- Ramsey: graph construction or search heuristic.
- Matrix multiplication: solver code for tensor decomposition.
- Kakeya: formula-generating program.

This would align the architecture section with the rest of the talk.

### LLM hallucination slide

The current intuition is fine, but the message should be sharpened:

> Natural-language proof attempts are fragile; executable programs can be
> tested.

Then immediately transition to the evaluator. Do not dwell on general ChatGPT
failure stories.

### Limitations

Be careful to distinguish:

- AlphaEvolve alone: finds programs/constructions, not proofs.
- Other AI proof systems: may generate or check proofs after a discovery.

Otherwise "No proofs" conflicts with the Kakeya proof-pipeline slide.

### Try it yourself

For this audience, this should be reframed as "how to formulate your own
problem" rather than education/outreach. Useful checklist:

- Candidate representation.
- Fast deterministic evaluator.
- Meaningful baseline-to-SOTA gap.
- Generalization tests to avoid overfitting to one instance.
- Reward hacking / evaluator design.

## Possible revised flow

1. Strassen hook: 49 to 48.
2. Why direct LLM math is not enough.
3. Evolutionary coding agents: LLM mutation + evaluator selection.
4. What is evolved: programs, not objects.
5. Discoveries:
   - Cap set.
   - Ramsey.
   - Matrix multiplication.
   - Kakeya as a short "famous problem" highlight, not a technical section.
6. Limitations and formulation principles.
7. Takeaways.

## Final takeaways to aim for

1. These systems discover constructions by evolving code.
2. The evaluator is the source of reliability.
3. The right mathematical skill is problem formulation: designing the search
   space and evaluator.
4. This is most promising for combinatorial / constructive problems with fast
   verification.

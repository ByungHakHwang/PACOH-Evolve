# Presentation Review Notes

## Audience assumption

The relevant audience is **combinatorialists who have had little exposure to
AI**. This deck is the conceptual lead-in before a hands-on PACOH tutorial.

Earlier notes assuming middle/high-school math teachers belong to a previous
talk and should not guide this version. At the same time, the audience should
not be assumed to know LLM agents, genetic algorithms, or evaluator-based
program search.

Consequence: the talk should be mathematically serious, but the mechanism
build-up in §2 is valuable. The GA ramp-up is not wasted time; it is the bridge
from familiar combinatorial search to AlphaEvolve-style coding agents.

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

For this audience and setting, the deck should prioritize (1) and (2), while
ending with enough formulation guidance to make the hands-on tutorial feel
natural.

## Recommended emphasis

### Keep

- The Strassen hook. It is strong and gives a concrete mystery.
- The GA-to-LLM build-up. For AI newcomers, this is useful pedagogy.
- The evaluator principle. This is the conceptual backbone.
- The prompt template in "Four components, one iteration." It demystifies the
  mechanism quickly.
- The cap set example. It is the cleanest FunSearch-style example.
- The Ramsey example. It is directly relevant to combinatorics and shows
  meta-search power.
- The matrix multiplication callback to the Strassen hook.

### Reduce

- General toy examples such as TSP and circle packing, unless they are used only
  as quick intuition.
- "LLMs hallucinate" as a generic warning. For this audience, the point should
  be why hallucination is controlled by executable evaluation.
- CS / ML systems jargon around compute-stack examples, unless glossed quickly.

### Compress Kakeya

Kakeya should not become a technical centerpiece. It is enough to say:

- AlphaEvolve was applied to the finite-field Kakeya problem.
- It found new explicit constructions / formulas.
- In one case the pipeline continued to proof generation and formal checking.
- This shows that the method can touch famous, serious mathematical problems.

Avoid spending much time on Dvir, Bukh--Chao constants, lower-order terms,
Nikodym sets, or arithmetic Kakeya unless the audience asks.

The detailed review suggests compressing Kakeya from 6 frames to 3--4 frames
and using the saved space for a concrete LLM-mutation example. That is the
highest-value structural change.

## Specific slide-level concerns

### AI for mathematics table

The table is useful, but the third column should not blur "LLM proof generator"
and "formal theorem prover." A better distinction:

- Pattern recognizer: finds patterns/conjectures from data.
- Coding agent: searches over programs/constructions using an evaluator.
- Proof agent: generates proof attempts / proof strategies.

The middle column is the talk.

Also restore the explicit orientation line after the table:

> Today we focus on the middle column.

For AI newcomers, this kind of signpost matters.

### Genetic algorithms for mathematics

The slide can stay, because the audience is not assumed to know AI methods. The
main point should be:

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

There is a trade-off: TSP and circle packing are classic GA examples and useful
for intuition, but they do not return in the discovery section. If they stay,
they should be explicitly framed as toy / tutorial examples.

### Missing mechanism demo

The biggest gap is that the deck says the LLM rewrites code but never shows a
real mutation. Add one slide after the cap-set seed function:

- parent seed function,
- short evolved priority function or parent-to-child diff,
- evaluator score improves.

This would make "smart mutation" concrete before the hands-on tutorial.

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

For this audience, this should serve as the bridge into the hands-on tutorial.
Frame it as "how to formulate your own combinatorial problem." Useful checklist:

- Candidate representation.
- Fast deterministic evaluator.
- Meaningful baseline-to-SOTA gap.
- Generalization tests to avoid overfitting to one instance.
- Reward hacking / evaluator design.

## Possible revised flow

1. Strassen hook: 49 to 48.
2. GA intuition for combinatorial search.
3. LLM as smart mutation, controlled by an evaluator.
4. Inside the loop: database, prompt sampler, LLM, evaluator.
5. What is evolved: programs, not objects.
6. Discoveries:
   - Cap set.
   - Ramsey.
   - Matrix multiplication.
   - Kakeya as a short "famous problem" highlight, not a technical section.
7. Limitations and formulation principles.
8. Tutorial bridge / starter problems.
9. Takeaways.

## Immediate factual/polish fixes from the detailed review

1. Ramsey table:
   - \(R(4,6)\): use \([36,40]\), not \([36,41]\).
   - \(R(5,5)\): use \([43,46]\), not \([43,48]\).
2. "Repeat \(\sim 10^5\) times" should probably be
   "\(\sim 10^5\)--\(10^6\) times."
3. Differentiate the two consecutive "Example 1: the Cap Set problem" frame
   titles.
4. Add "lower bounds" to the Nagda Ramsey table header or caption.

## Final takeaways to aim for

1. These systems discover constructions by evolving code.
2. The evaluator is the source of reliability.
3. The right mathematical skill is problem formulation: designing the search
   space and evaluator.
4. This is most promising for combinatorial / constructive problems with fast
   verification.

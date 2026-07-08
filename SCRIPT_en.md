# English Presentation Script

This script follows `main.tex` as of 2026-07-08.

Notes:

- Text in brackets, such as `[Click]`, is a cue. Do not read it aloud.
- The language is intentionally simple.
- The main script is written for about 38 to 42 minutes at a calm pace.
- The supplementary slides at the end are for questions.

## Title

Good afternoon. My name is Byung-Hak Hwang.

Let me start with a small disclaimer.
This is a mixed audience.
Some of you know much more about coding agents than I do.
But I think many of you are new to this area.
So I will start from very simple examples.
For the experts, some parts may feel basic.
But I hope this will give us a common starting point.

Today I will talk about evolutionary coding agents.

The goal is not to give a technical survey of AI.
The goal is more basic.
I want to explain what these systems are.
I want to explain why they can be useful in mathematics.
And I want to prepare the ground for the hands-on session.

The main idea is simple.
These systems do not just ask an LLM for an answer.
They ask an LLM to write code.
Then they run the code.
Then they keep the code only if it works well.

That is the whole theme of this talk.

## A Puzzle To Start With

Let me start with a small puzzle.

How many multiplications do we need to multiply two by two matrices?

[Click]

Here are the two input matrices.
The output matrix has four entries.

[Click]

The usual formula is completely familiar.
Each entry is a sum of two products.
So we have four entries, and each uses two multiplications.

[Click]

That gives eight multiplications.

[Click]

The question is: can we do better?

At first sight, eight looks very natural.
There are eight products in the formula.
But the formula we write first is not always the best algorithm.

## Strassen's Surprising Answer

Strassen gave a surprising answer in 1969.

Two by two matrices can be multiplied using only seven multiplications.

[Click]

Here are the seven products.

I do not want you to check every term now.
The important point is this.
These products look strange.
They mix different entries of the two matrices.
They are not the products that appear in the standard formula.

[Click]

But if we combine them in the right way, the unwanted terms cancel.
The four entries of the product matrix come out correctly.

So we have saved one multiplication.
Eight becomes seven.

This example is a good warning.
The best construction may not look natural to us.
It may use a hidden pattern.
And it may be hard to find by hand.

## A 56-Year Mystery

Now let us move from two by two to four by four.

A four by four matrix can be seen as a two by two block matrix.
Each block is itself two by two.
So if we use Strassen twice, we get seven times seven.
That is forty-nine multiplications.

[Click]

For fifty-six years, nobody beat forty-nine for four by four complex matrix multiplication.

[Click]

Then AlphaEvolve found an algorithm using forty-eight multiplications.

[Click]

This was found by an AI system.
The system is called AlphaEvolve.

[Click]

So the natural question is:
how is this possible?

This is the question for the talk.
Not only for matrix multiplication.
More generally:
how can an AI system discover new mathematical constructions?

## AI For Mathematics

Before we discuss AlphaEvolve, let me place it in a bigger picture.

[Click]

There are many kinds of AI for mathematics.
This table gives three broad types.

The first type is a pattern recognizer.
It looks at data.
It finds patterns.
It may suggest conjectures.

The second type is a coding agent.
This is today's topic.
It searches for algorithms.
These algorithms build mathematical objects.

The third type is a proof agent.
It tries to generate proof ideas, proof strategies, or formal proofs.

[Click]

Today we focus on the middle column.

That is important.
AlphaEvolve is not mainly a theorem prover.
It is a system for searching over code.
The code builds objects.
Then an evaluator scores the objects.

## The Lineage Of Coding Agents

Here is the short history.

FunSearch appeared first.
It was published in Nature.
It was one of the first clear examples where an LLM-based search system made a new mathematical discovery.

[Click]

AlphaEvolve came later.
It used large language models.
It worked at a larger scale.
It could evolve not only one small function, but larger pieces of code.
It was applied both to mathematics and to engineering problems inside Google.

[Click]

Then, in 2025 and 2026, we started to see more examples.
Researchers used AlphaEvolve-style systems as research tools.
Some examples led to new constructions.
Some examples led to patterns that humans later proved.

So we should not think of this as one isolated system.
It is becoming a method.

## Borrowing From Evolution

To understand the method, let us go back to a classical idea:
the genetic algorithm.

A genetic algorithm is an optimization method inspired by biological evolution.

[Click]

We keep a population of candidate solutions.

[Click]

We mutate them, or recombine them, to produce children.

[Click]

We score each child by a fitness function.

[Click]

Then we keep the good ones and repeat.

[Click]

After many generations, the population can drift toward good solutions.
This does not require deep mathematical insight at each step.
It only requires a way to create variants and a way to score them.

[Click]

The video link is just an illustration of this idea.
You can see simple agents improve over generations.
That is the basic metaphor.

## Genetic Algorithms For Mathematics

Many problems in mathematics have this shape.
We want to construct the best object of a given kind.

[Click]

For example, a cap set.
We want a large subset with no three points on a line.

Or the traveling salesman problem.
We want the shortest tour through given cities.

Or circle packing.
We want to place circles inside a square and maximize the total radius.

[Click]

In each case, a candidate can be scored automatically.

For a cap set, we can score by size.
For traveling salesman, by tour length.
For circle packing, by total radius.

So a genetic algorithm can search for better candidates.

[Click]

But there is a problem.
In the systems we care about, the candidate is not just the object.
The candidate is often a program that builds the object.

Classical genetic algorithms mutate at random.
Random mutation is often hopeless for code.
Most random changes break the program.

[Click]

So the key question is:
what if mutation could be smart?

## LLMs As A Smart Mutation Operator

This is where LLMs enter.

Modern language models can read code.
They can understand the rough intent.
They can propose changes that are syntactically valid.
Sometimes the changes are also useful.

[Click]

So the key idea is simple.
Replace random mutation by an LLM that rewrites the code.

[Click]

Now mutation is no longer a random change in characters.

The model reads the parent program.
It tries to understand what the program is doing.
Then it proposes a thoughtful change.

Of course, the model is not always right.
But this is already much better than random mutation.
It gives us a way to explore code space.

## LLMs Hallucinate

But there is an obvious problem.

[Click]

LLMs hallucinate.

If we ask an LLM for a proof, the answer may look like mathematics.

[Click]

It may use correct terminology.

[Click]

It may follow a familiar proof structure.

[Click]

But it may contain one wrong logical step.

[Click]

And one wrong step is enough to break the whole proof.

[Click]

So how can we build a trustworthy discovery system on top of this?

[Click]

The answer is:
do not trust the LLM.

[Click]

Trust an evaluator.

This is the central principle of the talk.

## The Role Of The Evaluator

A natural-language proof is hard to check automatically.
At least, it is hard in full generality.

But a program can be run.

[Click]

The LLM writes a piece of code.
Then the code is run.
It is scored.
And it is verified by a deterministic evaluator.

[Click]

If the code is nonsense, it fails.

[Click]

If the code runs but performs badly, it gets a bad score.

[Click]

Only evaluator-certified programs survive.

[Click]

So the mathematical guarantee does not come from the LLM.
It comes from the evaluator.

This is the key difference from simply asking an LLM for a solution.
The LLM proposes executable programs.
The evaluator decides which programs survive.

## One Sentence Summary

[Click]

Here is the whole idea in one line.

An evolutionary coding agent is an LLM used as mutation,
plus an evaluator used as selection,
plus an evolution loop.

That is the mechanism behind FunSearch and AlphaEvolve.

The rest of the talk is about what this mechanism looks like in practice.

## The FunSearch / AlphaEvolve Loop

This diagram shows the loop.

There is a database of programs.
Some programs are good.
Some programs are diverse.
The system samples from this database.

Then it builds a prompt for the LLM.
The prompt shows examples of previous programs and their scores.

The LLM writes a new child program.
The evaluator runs the child.
If the child is useful, it goes back into the database.

Then the system repeats.

The important point is that this is not one prompt.
It is not one answer.
It is a large search process.
The LLM is used many times.
The evaluator is used many times.

## One Iteration Of The Loop

Let us spell out one iteration.

[Click]

First, the system picks a few parent programs.
They should be strong.
They should also be diverse.
This keeps the search from becoming too narrow.

[Click]

Second, an LLM writes a child program.
The child is meant to improve on the parents.

[Click]

Third, the evaluator runs the child.
It scores the output.
If the child is good, or if it adds useful diversity, the system keeps it.

[Click]

The prompt can be very simple:
Here are programs and scores.
Write a better one.

[Click]

Then the loop repeats many times.
Small improvements can accumulate.

## What Is Actually Being Evolved?

[Click]

This is the question I want to make very clear.

The system usually does not evolve the mathematical object directly.
It evolves the program that constructs the object.

[Click]

For a cap set, it can evolve a priority function.
The function decides which vector to add next.

[Click]

For Ramsey problems, it can evolve a search heuristic.
The heuristic builds large graphs that avoid forbidden cliques.

[Click]

For matrix multiplication, it can evolve the solver code.
The solver searches for low-rank tensor decompositions.

[Click]

This is also why the results can be useful to humans.
The output is often readable code.
Humans can inspect it.
Sometimes they can understand the pattern.
Sometimes they can turn the pattern into a theorem.

## Example 1: Cap Set Problem

Let us start with the cap set problem.

We work in the vector space over the field with three elements.
The problem is to find a large subset with no three elements on a line.

[Click]

Equivalently, we want no three-term arithmetic progression.

[Click]

The exact size is known only in small dimensions.
The search space grows very fast.

[Click]

In dimension eight, the previous record was four hundred ninety-six.
It had stood for about twenty years.

[Click]

FunSearch found a cap set of size five hundred twelve in dimension eight.

This is a good first example because the mechanism is very clean.
The LLM did not prove an optimal bound.
It found code that constructs a better object.

## Example 1: Where The Evolved Code Enters

Now let me show where the evolved code enters.

The main constructor is human-written.
It is a greedy algorithm.

It starts with the empty set A.
It lists all vectors in the space. 
Then it sorts the vectors by a priority score.

After that, it tries the vectors one by one.
If adding the next vector does not create a three-term progression,
the algorithm keeps it.
Otherwise, it skips it.

At the end, it returns the set A.

[Click]

Here is the key point.
The greedy loop is not evolved.
The cap-set checker is not evolved.
Only this small priority function is evolved.

The seed version is trivial.
It returns zero for every vector.
So at the beginning, every vector has the same priority.

[Click]

The evaluator is also simple.
It runs the greedy constructor with the proposed priority function.
Then it returns the size of the final set.

So the LLM is not trusted.
The LLM only proposes a new priority rule.
The evaluator decides whether it is useful.

## Example 1: What FunSearch Evolved

This is an abridged version of the evolved priority function.

Do not worry about every line.
Look at the shape.

The code counts zeros.
It checks relations between coordinates.
It changes the score depending on those relations.

[Click]

The important part is that this is real Python code.
No human wrote this exact function.

And it was readable.
In particular, it used a symmetry between coordinate i and coordinate minus i.
That symmetry gave humans a clue.

So the discovery was not just a list of points.
It was a readable construction.
The code helped humans understand why the set of size five hundred twelve existed.

This is one of the most attractive features of these systems.
They can produce artifacts that are not only useful, but also interpretable.

## Example 2: Ramsey Numbers

The second example is Ramsey numbers.

Let us start with the party problem.
The smallest number N such that any group of N people contains either three mutual friends or three mutual strangers is six.

[Click]

In general, R of s and t is the smallest N such that every two-coloring of the edges of K_N contains a red K_s or a blue K_t.

Equivalently, in graph language, to prove a lower bound we need to build a graph with no K_s and no independent set of size t.

[Click]

The table shows how hard this becomes.
Even small entries are not all known exactly.
For example, R(4,6) is still only known within a range.
And R(5,5) is also known only within a range.

These are classical combinatorial search problems.

## Example 2: One System, Many Better Bounds

For many entries in the Ramsey table, progress needs a special search.
Often, each entry is its own project.

Nagda, Raghavan, and Thakurta used AlphaEvolve in several Ramsey cases.
The goal was simple:
build larger graphs that avoid the forbidden structures.

[Click]

This table shows nine improvements.

Please note what these numbers mean.
They are lower-bound witness sizes.
For example, if the entry goes from 170 to 174, it means the system found a larger graph avoiding the forbidden structure.

It does not mean the exact Ramsey number is now known.
It means the known lower bound improved.

[Click]

The striking point is not only one improved graph.
The striking point is that one system improved nine lower bounds.

Here the evolved objects are graph-search programs.
The evaluator is a graph checker.
It checks whether the output avoids the forbidden clique or independent set.

Again, the evaluator is the source of trust.
The LLM proposes code.
The graph checker decides whether the output is valid.

## Example 3: Remember The 49?

Now let us return to the opening puzzle.

[Click]

For four by four matrices, the classical Strassen construction gives forty-nine multiplications.

[Click]

AlphaEvolve found forty-eight.

[Click]

This was the first improvement over Strassen after fifty-six years, for complex matrix multiplication.

This is a good example because it connects the whole story back to a familiar object.

Matrix multiplication looks elementary.
But the search space for better algorithms is enormous.
That is exactly where this kind of automated search can help.

## Example 3: How Was It Found?

How did AlphaEvolve find it?

The input was a generic gradient-based solver for low-rank tensor decomposition.
This is the same problem class as Strassen.
A matrix multiplication algorithm corresponds to a tensor decomposition.
The rank is the number of scalar multiplications.

[Click]

What evolves is the solver's code.
For example, how the solver starts.
What loss it uses.
How it improves the candidate.

[Click]

The evaluator runs the solver on the four by four matrix multiplication tensor.
It returns the rank achieved.
And importantly, it verifies the result exactly.
The numerical coefficients are rounded.
Then the identity is checked.

[Click]

The discovered algorithm uses complex coefficients with special cancellations.

[Click]

The same approach also gave state-of-the-art results for thirteen other matrix multiplication targets.

Again, the pattern is the same.
The LLM writes code.
The evaluator tests it.
The search loop selects better code.

## Example 4: Beyond Optimization

So far, all examples optimized a number.

Cap set: maximize size.
Ramsey: maximize graph size.
Matrix multiplication: minimize rank.

[Click]

But we can also ask about structural questions.

[Click]

Here is one example from Ellenberg, Libedinsky, Plaza, Simental, and Williamson.

The problem is about large boolean intervals inside the Bruhat order of the symmetric group.
You can think of a boolean interval as a poset hypercube.

I will not go into the technical details.
The important point is the role of the AI system.

[Click]

AlphaEvolve returned a recipe.
The recipe pointed to dyadically well-distributed permutations.

[Click]

Then the authors proved that these permutations form a hypercube of dimension m times two to the m minus one in S_{2^m}.

[Click]

This is the collaboration model I want to emphasize.

AI suggests the pattern.
Mathematicians prove the theorem.

## What AlphaEvolve Cannot Yet Do

Now let me be clear about limitations.

[Click]

First, AlphaEvolve itself does not produce proofs.
It outputs constructions and heuristics.
The proof, if there is one, is a separate step.

[Click]

Second, it needs an evaluator.
If there is no automatic score, there is nothing to evolve.
This is a serious restriction.

[Click]

Third, some mathematical tasks are still hard for these systems.
For example, recent work suggests that combinatorial bijections are difficult.
The search space is subtle.
The evaluator signal can be weak.

[Click]

Fourth, there is compute cost.
Large runs may require many LLM calls.
That cost matters.

So this is not magic.
It is a useful method under the right conditions.

## The Message

[Click]

The main message is not that coding agents replace mathematicians.

[Click]

The message is that they can become a new kind of collaborator in the loop.

[Click]

The Bruhat example is a good prototype.

The AI found a recipe for large hypercube intervals in S_n.

[Click]

Humans recognized the structure.
Humans proved the theorem.

This division of labor is important.
The machine is good at large-scale search.
The human is good at meaning, structure, and proof.

## The Evolve Ecosystem

AlphaEvolve itself runs only inside DeepMind.
But the general paradigm is now open.

[Click]

Ellenberg and collaborators developed a FunSearch-style tool for working mathematicians.
It can use a commercial LLM API.
It can be organized around one Python file with a priority function and an evaluator.

OpenEvolve is a community open-source clone.

[Click]

ShinkaEvolve is another recent system.
It is more sample-efficient.
For example, it found a new state of the art for twenty-six-circle packing with only one hundred fifty LLM samples.

[Click]

The point is that this is no longer only a giant-lab idea.
There are versions that we can run and modify.
That leads directly to the hands-on part.

## Two Starter Problems

Here are two starter problems.

The first is circle packing in a square.
We place n circles inside the unit square.
They cannot overlap.
We want to maximize the sum of their radii.

[Click]

The evaluator is clear.
Check the boundary.
Check overlaps.
If the candidate is valid, return the total radius.
If not, penalize it or reject it.

[Click]

The second problem is a no-isosceles subset of a small grid.
We want many points in an n by n grid.
No three points should form an isosceles triangle.

[Click]

Again, the evaluator is clear.
For each triple, compute the three pairwise distances.
If two distances are equal, we have an isosceles triangle.

Both problems are good for practice because the scoring rule is simple.
The search space is still interesting.

## Designing Your Own Problem

So what makes a problem ready for an evolutionary coding agent?

[Click]

First, candidates should be expressible as Python code.
The system needs something it can edit.

[Click]

Second, the evaluator should be deterministic.
It should return a real-valued score in seconds.
Fast evaluation is crucial because the loop runs many times.

[Click]

Third, there should be a meaningful gap.
There should be a trivial baseline.
There should also be a known good target, or at least room to improve.

This is a mathematical skill.
We need to design the representation.
We need to design the evaluator.
And we need to make sure the score really reflects the object we care about.

## Four Takeaways

Let me end with four takeaways.

[Click]

First, these systems discover by evolving code.
They find constructions and heuristics.
They do not, by themselves, give proofs.

[Click]

Second, trust comes from the evaluator, not from the LLM.
This is the most important point.

[Click]

Third, the sweet spot is combinatorial or constructive problems with a fast deterministic evaluator.

[Click]

Fourth, the best model is collaboration.
The AI suggests a pattern.
Humans recognize the structure and prove the theorem.

This is not a replacement for mathematics.
It is a new tool for mathematical exploration.

## Thank You

Thank you very much.

In the hands-on session, we will now move from the idea to practice.
We will try to design an evaluator.
Then we will see how an evolve-style loop can use it.

## References

These are the main papers behind the talk.

For FunSearch, the key reference is the Nature paper by Romera-Paredes and collaborators.

For AlphaEvolve, the key reference is the arXiv paper by Novikov and collaborators.

The other references show later uses and related tools.

I am happy to discuss any of these during questions.

# Supplementary Script For Questions

## Supplement: Hypercubes Inside Bruhat Order

This slide gives a little more detail about the Bruhat example.

The symmetric group has a partial order called the Bruhat order.
It is central in representation theory and geometry.

[Click]

The picture shows a hypercube.
In the Bruhat order, we can ask for intervals that look like this.

[Click]

The goal is to find large boolean intervals.
These intervals are connected to Kazhdan-Lusztig theory and other structures.

For the main talk, the only point was the workflow:
AI finds a pattern, then humans prove it.

## Supplement: The AlphaEvolve Experiment

In the experiment, AlphaEvolve was asked to produce good recipes depending on n.

[Click]

The recipes worked very well for small n.

[Click]

Then the authors noticed something surprising.

[Click]

The permutations picked by AlphaEvolve matched a known type of object:
dyadically well-distributed permutations.

This notion comes from a different area, including Monte Carlo integration and mathematical finance.

So the AI search connected two ideas that were not obviously connected at first.

## Supplement: A Theorem From The Loop

Here is the theorem that came out of the human analysis.

For n equal to two to the m, the dyadically well-distributed permutations form a Bruhat interval.
That interval is a hypercube of dimension m times two to the m minus one.

[Click]

There is also an upper-bound comparison.
No Bruhat hypercube in this group can be larger than a constant factor more.
So the construction is optimal up to a factor of two.

[Click]

This is why the example is interesting.
The AI system did not prove the theorem.
But it found the pattern that led to the theorem.

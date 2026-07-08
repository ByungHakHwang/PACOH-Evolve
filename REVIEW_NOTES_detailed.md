# Presentation Review — Detailed Slide-Level Pass

**Date:** 2026-07-08
**Reviewer:** Claude (working session with B.-H. Hwang)
**Deck:** `main.tex` — *Exploring Evolve-Style Coding Agents* (PACOH tutorial)

## Premise (read this first)

This review assumes the audience stated in this session:

> **Combinatorialists who have had little exposure to AI.** This deck is the
> "how does an AlphaEvolve-style system actually work?" lead-in, shown
> **before the hands-on tutorial.**

> **Note on `REVIEW_NOTES.md`:** the existing `REVIEW_NOTES.md` assumes a
> *different* audience — "mathematicians already familiar with AI," needing
> "no long pedagogical ramp-up." That premise is the opposite of the one above,
> and it flips some recommendations (e.g. that file says *reduce GA basics*;
> under the low-AI-exposure premise, the GA ramp-up is an asset). The two docs
> agree on most structural points (compress Kakeya, align running examples, fix
> the taxonomy table, evaluator-as-backbone). **Reconcile the audience premise
> before acting**, since it decides how much of §2's build-up to keep.

---

## Overall verdict

The narrative spine and pedagogy are strong. Strassen hook → GA → LLM mutation →
evaluator → discoveries → message is a clean arc, and the §2–§3 mechanism
build-up is well-paced for AI newcomers. The "don't trust the LLM, trust an
evaluator" throughline is exactly right for a skeptical mathematical audience.

Two weaknesses dominate:

1. **The mechanism is described but never *shown*.** The audience is told the
   LLM rewrites code, but never sees a single mutation.
2. **Discoveries (15 frames), especially Kakeya (6 frames), is over-weighted**
   for a combinatorics audience — Kakeya is the least combinatorial and most
   technical example, and it is the longest.

---

## What works (keep)

- **Strassen hook → matmul callback.** Concrete, suspenseful, paid off in §4.
- **§2 build-up** (Borrowing from evolution → GA for math → smart mutation →
  hallucinate → evaluator → one-sentence box). Textbook pacing for novices.
- **§3 "Four components" + prompt template** ("Here are k programs with scores
  …; write a higher-scoring one"). The single best mechanism-demystifying slide.
- **Kakeya "generalizer mode"** idea (score = average over many primes ⇒
  surviving code *must* be a formula in p). Deep and elegant.
- **§6 starter problems** (Ramsey K₁₇, no-isosceles grid) are combinatorial and
  make a strong runway into the tutorial.

---

## Biggest opportunities

### 1. Show a real LLM mutation (highest value)

Right now "the LLM reads a parent program and writes a better child" is only
*asserted*. For AI novices this is the least believable and most demystifiable
claim, and it is never made visual.

- The "priority function" slide (`main.tex:562`) shows only the trivial seed
  (`return 0.0`) and stops.
- **Add one slide** with a short *evolved* cap-set priority function, or a
  parent → child diff. The FunSearch (Nature) paper publishes the actual evolved
  function; it can be reused directly.
- Payoff: "smart mutation" turns from an abstract claim into a visible fact —
  the best possible primer immediately before a hands-on tutorial.

### 2. Kakeya weight & audience fit (6 frames → reconsider)

- Kakeya is the only **non-combinatorial** example (harmonic analysis / finite-
  field geometry), the deepest, and the longest (d=3 formula → d=4 elliptic
  curves → d=5 → Nikodym → arithmetic Kakeya). Cap set and Ramsey are this
  audience's home turf.
- Options:
  - **(a) Keep but compress** — collapse the last two frames
    (`main.tex:859`–`936`: d=4/d=5, Nikodym, arithmetic Kakeya) into one, keeping
    only the climax message.
  - **(b) Swap the climax to Bruhat** — the Williamson hypercube result currently
    in the backup (`main.tex:1146`+) is far more combinatorial (symmetric group,
    Bruhat order, posets) and delivers the *same* "AI proposed the pattern,
    humans proved the theorem" message. Likely lands better with this audience.
  - **(c) Leave as is** — best as spectacle, if the time budget allows.
- Recommendation: for a combinatorics audience, default to **(a) compress** (to
  3–4 frames); reinvest the saved space in opportunity #1.

---

## Correctness / rigor fixes

| Location | Issue | Fix |
|---|---|---|
| `main.tex:608–609` (Ramsey table) | R(4,6) shown as [36, **41**]; R(5,5) shown as [43, **48**] — both are outdated upper bounds | **R(4,6) → [36, 40]** (Angeltveit–McKay 2020); **R(5,5) → [43, 46]** (Angeltveit–McKay 2024, arXiv:2409.15709) |
| `main.tex:212` ("AI for mathematics" table) | Row 2 is asymmetric: col 1 gives a *description* ("Train a model for each problem") while cols 2–3 give *system names* (FunSearch/AlphaEvolve; AlphaProof/Deep Think/Aristotle) | Restore the commented-out `(Transformer, GNN, RL, …)` into col 1 so all three columns list representative approaches/systems |
| `main.tex:226–228` | "Today we focus on the middle column" is commented out | **Restore it** — after a 3-way taxonomy, novices need to be told explicitly which column the talk is about (coding agents) |
| `main.tex:904` | "Two follow-up papers *by Tao alone*" | Verify Tao is sole author of both follow-ups (the main paper, arXiv:2511.02864, is 4 authors) |
| `main.tex:490` | "Repeat ∼10⁵ times" | AlphaEvolve/FunSearch run 10⁵–10⁶ evaluations; "10⁵–10⁶" is safer |

Everything else checked out: the Strassen 7-product formulas and c_ij
reconstruction (`main.tex:122–141`) are correct, and 48/49, cap set 496→512,
Dvir, Bukh–Chao, Wang–Zahl (2025), and the compute-stack percentages
(23% / 0.7% / 32%) are all accurate.

---

## Audience fit & clarity

- **CS-systems jargon** (`main.tex:713`, "AlphaEvolve in Google's compute
  stack"): *FlashAttention*, *register-allocation hint*, *matmul kernel* are
  opaque to a math audience. The percentages carry the message; wrap the item
  names in something like "low-level engineering problems."
- **ML jargon** (`main.tex:696`, matmul): *initializer, loss, optimizer* may be
  unfamiliar to combinatorialists — either keep it as "the solver's code" or add
  half a sentence of gloss.
- **Running-example mismatch.** §2/§3 illustrate with **cap set / TSP / circle
  packing**, but §4 discoveries are **cap set / Ramsey / matmul / Kakeya**. TSP
  never returns (circle packing is recovered in §6 via ShinkaEvolve); Ramsey and
  matmul appear with no earlier setup. Using **cap set / Ramsey / matmul** as the
  §2/§3 trio would complete the foreshadowing (all three reappear, all
  combinatorial). Trade-off: TSP and circle packing are better "classic-GA"
  exemplars for §2's specific point, so this is a judgment call.
- **"Missing LLM demo"** is also an audience-fit issue, covered in Opportunity #1.

---

## Minor polish

- `main.tex:531` and `:551` — two consecutive frames share the identical
  frametitle "Example 1: the Cap Set problem." Differentiate the second
  (e.g., "Example 1: Cap Set — the record").
- Cap set "~20 years" appears on both `:543` and `:557` — keep it on one.
- `main.tex:642` (Nagda table) header "previous / AlphaEvolve" — add that these
  are *lower bounds* (the closing line already implies it).

---

## Prioritized action list

1. **(Top) Add one LLM-mutation slide** — evolved priority function or
   parent → child diff, right after the seed slide.
2. **Fix the two Ramsey numbers** — R(4,6) → [36,40], R(5,5) → [43,46].
   Immediate, low-cost, purely factual.
3. **Compress Kakeya** (6 → 3–4 frames), or swap the climax to the Bruhat
   result — decide based on audience premise and time budget.
4. **Fix the "AI for mathematics" table** — restore column-1 examples and the
   "middle column" orientation line.
5. **Soften CS/ML jargon**, align running examples, minor polish.

---

## Sources (for the Ramsey correction)

- R(5,5) ≤ 46 (Angeltveit–McKay, 2024): https://arxiv.org/abs/2409.15709
- R(4,6) current bounds [36, 40]: https://leapsinbounds.org/constants/ramsey-4-6/

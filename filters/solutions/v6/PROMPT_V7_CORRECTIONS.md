# Corrections to carry into the solutions v7 oracle prompt (#84)

**Written 2026-08-06. Applies to the NEXT prompt, not this one.**

`prompt-compressed.md` in this directory is **not to be edited**. It is the
provenance record of what the v6 student was trained on, and its `prompt_hash` is
stamped into every scoring result — a cosmetic edit invalidates that link for
every article already scored. (That is also why the `****VERSION:** 6.0` typo in
its header stays.) This file exists so the fixes are not re-derived from scratch
when v7 is authored by copying v6.

Found by the 2026-07-30 review battery over the DeepSeek-authored commits
(`32c9ac0`), inherited verbatim by v6. The v6 gate still passed (F1 0.739), so
this is a retrain-quality item, not a production incident.

---

## The defect: the router has a destination that does not exist

The prompt has **two** dispositions — pass Step 1 (score normally) or fail Step 1
(`not_a_solution`, all dimensions 0.0). The Step-1-vs-Flag-A router needs a
**third**, and points at Flag A as if Flag A were it. Two contradictions follow.

**1. "Route to Flag A" is not reachable from "does not pass Step 1."**

> STEP-1 vs FLAG-A ROUTER (deterministic): … The following do NOT pass Step 1 on
> their own; route to Flag A instead

but Step 3 opens with

> These catch in-scope-adjacent articles **that passed Step 1** …

Reaching Flag A *requires* passing Step 1. So the token "Step 1" means *passed*
in the tiebreak and *zeroed* in Flag A's parenthetical, in the same document.
A model resolving this either way produces a different label, which is why the
regulation-bleed class is model-mood-dependent.

**2. Flag A's trigger cannot fire on what the router sends it.**

The router sends "parliament passes bill, no implementation evidence" to Flag A.
Flag A fires on

> the only "action" present is vague, hypothetical, or merely called-for

An enacted law is none of those three — it is concrete, actual, and already
taken. Worse, Flag A's carve-out un-flags anything with

> a concrete response with named actor + committed resources

**without requiring outcomes.** A funded, enacted bill has a named actor and
committed resources, so it clears the carve-out and escapes uncapped — which is
exactly the pre-v5 regulation-bleed behaviour v5 set out to remove.

---

## The v7 fix: name the third disposition

Do **not** patch this by widening Flag A's trigger. Flag A's job is
crisis-reporting-with-no-action, and the two classes fail for opposite reasons:
Flag A's articles have *no* action, the router's have an action with *no measured
effect*. Merging them makes both triggers vaguer.

Add a distinct Step-3 flag and point the router at it:

> **A2) ACTION WITHOUT OUTCOMES?** A concrete action has been taken — a law
> enacted, rules issued, a ruling handed down, an enforcement penalty imposed —
> but the article evidences only the action's EXISTENCE, not its EFFECT.
>   - If YES and NOT (the article reports measured outcomes OF THE MECHANISM:
>     people served, emissions reduced, cases resolved, behaviour changed):
>   - → FLAG `action_without_outcomes` → **max_score = 3.0**
>   - *Test:* the article names something that happened. Can you state a number
>     that changed BECAUSE it happened? If NO, flag.
>   - *Contrastive pair:* "Parliament passes single-use plastics ban" = FLAGGED
>     (existence only). "One year after the ban, single-use plastic in municipal
>     waste is down 34%" = NOT flagged (measured effect of the mechanism).

Then make three edits so the routing is consistent:

1. **Router wording.** Replace "do NOT pass Step 1 on their own; route to Flag A
   instead" with: *"pass Step 1 (an action exists) but MUST carry Flag A2 unless
   the article reports measured outcomes of the mechanism."* This removes the
   impossible route and keeps the intended cap.
2. **The carve-out must require outcomes, not resources.** In A2 (and only A2),
   "named actor + committed resources" does **not** lift the flag; only measured
   outcomes do. Flag A keeps its existing resources-based carve-out, because for
   crisis reporting the presence of a funded response genuinely is the news.
3. **Flag A's parenthetical.** "(If NO action of any kind is mentioned, that is
   Step 1, not this flag — see the router above.)" is the sentence that overloads
   the token. Make it explicit: *"If NO action of any kind is mentioned, the
   article fails Step 1 and scores `not_a_solution` (all dimensions 0.0). This
   flag is for articles that PASSED Step 1."*

The existing tiebreak already states the right rule and should be left alone — it
is the one place the prompt gets this correct:

> "Does this article contain evidence of the action's EFFECT, or only evidence of
> its EXISTENCE?"

A2 is that tiebreak given a destination.

---

## Before the v7 oracle run

- **Re-label the affected class, do not reuse v6 labels for it.** The defect
  produces label *noise* on regulation/enforcement articles specifically. Any v7
  training set that inherits v6 oracle labels inherits the noise.
- **Watch the interaction with the noise floor.** A2's cap (3.0) sits above
  solutions' 2.25 op-point by design, so flagged articles stay visible. That is
  the same shape as the inert `concreteness_gatekeeper` (#94) — if A2 is meant to
  affect *visibility* rather than rank, the cap has to go below 2.25, and that
  needs a measured recall check first (ADR-021).

## Related

- #84 — the issue
- #94 — the gatekeeper whose cap sits above the op-point for the same reason
- ADR-010 — oracle consistency over data volume; this is a consistency defect

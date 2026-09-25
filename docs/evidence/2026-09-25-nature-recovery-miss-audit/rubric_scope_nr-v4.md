# Nature recovery scope rubric — nature_recovery v4 prompt, STEP 1 + §4 Pre-Classification, VERBATIM

*Extracted 2026-09-25 from `filters/nature_recovery/v4/prompt-compressed.md` (lines 13–57 and 218–252). Only the SCOPE question is used here; the dimension scoring is not.*

## STEP 1: SCOPE CHECK (Do This FIRST)

**Before scoring any dimension, determine: Does this article document ecosystem recovery?**

Ask yourself:
1. What is the PRIMARY TOPIC? (ecology, climate tech, policy, doom, fundraising, etc.)
2. Does it describe ANY of: species returning, populations growing, habitats regenerating, pollution declining, ecosystems restoring?
3. Is there EVIDENCE of recovery — EITHER (a) observed ecological change (data, observations, measurements), OR (b) **DELIVERED structural protection**: enacted, in-force legal protection or demonstrable removal of the pressure (an active fishing ban, a gazetted-and-patrolled marine protected area, a signed-and-effective moratorium, a dam removed) — NOT merely plans, pledges, targets, or drafts?

**If the answer to BOTH #2 and #3 is NO -> score ALL dimensions 0-2. Stop.**
*(Delivered protection alone can satisfy #3 even when #2 rebound is not yet measured — see IN SCOPE and Recovery Evidence dimension. Pledges/targets/drafts satisfy neither.)*

**IN SCOPE (proceed to Step 2):**
- Species populations recovering (bald eagles, wolves, whales, fish returning)
- Habitats regenerating (forests regrowing, wetlands restoring, coral recovering)
- Pollution declining with ecological impact (air quality improving, rivers cleaning, soil recovering)
- Rewilding outcomes (keystone species reintroduced, trophic cascades observed)
- Policy-driven environmental wins with documented outcomes (Montreal Protocol, Clean Air Act results)
- Community-led conservation with measured ecological results
- **Delivered protection (#70)** — enacted, enforced protection or demonstrable pressure-removal (an active MPA with enforcement, an in-force fishing/logging ban, an effective moratorium, land legally designated with the harmful use actually stopped), counted as recovery-in-progress EVEN BEFORE biological rebound is measured. NOTE: pledges, "30% by 2030" targets, drafts, signed-but-not-in-force treaties, and unenforced "paper parks" are NOT delivered protection — they are OUT OF SCOPE policy announcements.

**OUT OF SCOPE (score 0-2 on ALL dimensions):**
- **Climate doom** — extinction crisis, habitat destruction, "we're running out of time" without recovery
- **Climate tech** — solar panels, EVs, carbon capture, battery technology, grid modernization
- **Greenwashing** — corporate ESG reports, "net zero by 2050" pledges, carbon offset marketing
- **Conservation appeals** — "donate to save the rainforest", fundraising without documented outcomes
- **Policy announcements** — government pledges without implementation evidence or ecological results
- **Symbolic gestures** — Earth Day cleanups, "plant a tree for every purchase", token actions
- **Academic proposals** — "our model predicts that if we..." without observed results
- **Technology performance** — efficiency metrics, cost curves, deployment numbers without ecological data

**NOISE Detection Checklist:**
- Species extinction / habitat destruction reporting -> NOISE (all dimensions 0-2)
- Solar / wind / EV / hydrogen technology -> NOISE (all dimensions 0-2)
- Corporate sustainability report / ESG score -> NOISE (all dimensions 0-2)
- "Donate to protect..." fundraising appeal -> NOISE (all dimensions 0-2)
- "Government pledges to..." without outcomes -> NOISE (all dimensions 0-2)
- "We planted 1,000 trees on Earth Day" -> NOISE (all dimensions 0-2)

**DO NOT hallucinate recovery that isn't there.** If an article is about climate doom, it's about climate doom — not nature recovery.

**ANTI-HALLUCINATION RULE:** Every evidence field MUST contain an EXACT QUOTE from the article, or "No evidence in article." Do not paraphrase, infer, or fabricate evidence.

---


## 4. Pre-Classification Step

Before scoring, classify the content type and apply its adjustment. There are TWO kinds of adjustment:
- **HARD CAP (max_score):** clamp EVERY dimension at the cap value. For content that is out-of-scope or purely a pledge.
- **SOFT PENALTY (−value):** subtract the penalty from EACH dimension, then floor at 0. This preserves dim-to-dim ranking while lowering the weighted average (ADR-015 — avoids the cliff-shaped labels a hard cap creates when the content still has real gradient).

**MULTI-FLAG RULE:** If several flags fire, apply the HARD CAP(s) FIRST (lowest cap wins), THEN subtract the single HIGHEST soft penalty. Delivered protection (Recovery Evidence path b) is NOT a flag — never cap or penalize genuine enacted-and-in-force protection.

**A) CLIMATE DOOM?** Extinction, collapse, habitat destruction as main topic, "point of no return"?
   - If YES -> FLAG "climate_doom" -> **HARD CAP max_score = 2.0**

**B) CLIMATE TECH?** Solar, wind, EVs, batteries, carbon capture, hydrogen, clean energy?
   - If YES -> FLAG "climate_tech" -> **HARD CAP max_score = 3.0**
   - Exception: Technology enabling specific ecological outcome with ecological data reported

**C) GREENWASHING?** Corporate ESG, carbon offsets, "net zero" pledges, sustainability rankings?
   - If YES -> FLAG "greenwashing" -> **HARD CAP max_score = 2.0**
   - Exception: Corporate-funded restoration with documented ecological outcomes

**D) CONSERVATION APPEAL?** "Donate to save...", fundraising, awareness campaigns, endangered-species profiles without recovery data?
   - If YES and no documented outcomes -> FLAG "conservation_appeal" -> **SOFT PENALTY = −2.5** (subtract 2.5 from each dimension, floor at 0). *[PROVISIONAL value — to be calibrated on the DeepSeek pilot; DeepSeek under-fires this flag vs Gemini, so a Gemini-tuned value would be wrong. See config content_type_caps.]*
   - Why a penalty, not a cap: ~69% of conservation-appeal articles carry real ecological substance that a hard 2.0 cap would flatten into cliff labels. The penalty demotes a borderline appeal (honest weighted ~5-6) to just below the 4.0 surfacing threshold while keeping dim-to-dim ranking intact.
   - Exception: Appeal that includes documented outcomes of previous donations -> no penalty.

**E) POLICY ANNOUNCEMENT?** Government PLEDGES, proposed/draft regulations, international commitments NOT yet in force?
   - If YES and no implementation evidence -> FLAG "policy_announcement" -> **HARD CAP max_score = 3.0**
   - **NOT this flag:** protection that is ENACTED AND IN FORCE (a signed-and-effective ban, a gazetted-and-enforced MPA, a completed dam removal) — that is DELIVERED protection, scored via Recovery Evidence path b and NOT capped. The line is enacted-and-in-force (recovery) vs pledged/drafted/target (capped).
   - Exception: Policy retrospective showing measured ecological outcomes

**F) SYMBOLIC GESTURE?** Earth Day cleanup, token tree planting, celebrity environmental event?
   - If YES -> FLAG "symbolic_gesture" -> **HARD CAP max_score = 3.0**
   - Exception: Community restoration project with measurable multi-year outcomes

---


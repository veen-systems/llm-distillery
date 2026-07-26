# Violence Promotion Detection

## Purpose

Classify whether an article **promotes, normalizes, or presents as desirable** any form of mass violence — including active armed conflict, weapons manufacturing, military force as a solution, defense industry framed as progress, or instruments of violence in any positive context.

This is a **stamp-only** prefilter per ADR-004 (no universal drop). ovr.news will exclude stamped articles at selection; other consumers (investment_risk, resilience) keep them.

## Definition

**Violence Promotion (positive class):** stories whose primary subject promotes or normalises mass violence. This includes:

- **Active combat / warfare** — military strikes, bombing, shelling, battlefield casualties, offensives, drone strikes, armed attacks, troop movements in combat context, war crimes (active)
- **Weapons as progress** — weapons manufacturing, arms industry, military technology R&D, defense contractor profiles, domestically-produced armaments, "self-reliance" in arms production — when framed as achievement, growth, innovation, or strategic success
- **Military force as solution** — articles presenting military action, arms build-up, or weapons deployment as desirable, effective, or necessary
- **Normalising instruments of violence** — any article whose framing treats weapons systems, military hardware, or killing technology as normal economic activity, legitimate progress, or a source of national pride
- **Armed groups in action** — insurgency, terrorism operations, armed attacks by non-state actors, when reported as the primary subject (not as background to prevention/arrests)
- **State violence against citizens** — police brutality, political repression, lethal force against protesters or civilians by state actors, militarized law enforcement, border militarization — when framed as necessary, acceptable, or routine, or when the violence is the primary subject rather than background

**NOT Violence Promotion (negative class) — INCLUDING THE BOUNDARY CASES THAT MUST NOT BE FLAGGED:**

- **Post-conflict recovery** — reconstruction, de-mining, returning refugees, rebuilding infrastructure, trauma healing
- **Peace processes** — ceasefires, peace deals, negotiations, disarmament agreements, diplomacy, conflict resolution
- **Weapons restriction / disarmament** — arms control treaties, weapons bans, decommissioning programs, non-proliferation efforts
- **Historical** — war anniversaries, historical analysis, museum exhibitions about past conflicts, archaeology of battlefields (past wars are history, not promotion)
- **Justice/accountability** — war crimes tribunals, ICC proceedings, truth commissions, human rights investigations (these hold violence to account, not promote it)
- **Refugee stories** — displacement consequences, resettlement, asylum (victims of violence, not promoters)
- **Crime / terrorism prevention** — law enforcement arrests of terror suspects, disrupted plots, enhanced security measures (prevention, not promotion)
- **Natural disaster / accident** — explosions, fires, infrastructure failures NOT caused by combat or weapons
- **Military-adjacent but civilian** — veteran healthcare, military base environmental cleanup, defence budget oversight (not the weapons themselves)
- **Violence-prevention technology** — demining equipment, early-warning systems that save civilian lives, de-escalation tools, post-conflict clearance, civilian protection systems, cyber defense of critical infrastructure — technology whose primary purpose is preventing, reducing, or cleaning up after violence

## Scoring Guide (0–10)

| Score | Classification | Description |
|-------|---------------|-------------|
| 0–2 | **No Violence Promotion** | No mention of armed conflict, weapons, military operations, or violence. OR mentions them only as past/background context, or to describe their reduction, restriction, or aftermath. |
| 3–4 | **Peripheral** | Mentions violence-related content in passing (e.g., "the factory also produces components for defence systems") but the subject is NOT violence or weapons. |
| 5–6 | **Mixed/Ambiguous** | Contains both violence-promoting and non-violence elements; violence is a significant presence but not the primary framing. |
| 7–8 | **Mostly Violence Promotion** | Primary subject involves weapons, military force, or combat, but framed through a specific operational/economic lens (e.g., defence industry quarterly results, arms export deals without combat context). |
| 9–10 | **Violence Promotion** | Primary subject is active combat, military strikes, battlefield operations, armed attacks, weapons deployed as instruments of violence, or weapons manufacturing/industry framed explicitly as achievement, innovation, or progress. |

## Key Signals

**Strong Violence Promotion Signals (push score higher):**
- Active combat verbs: "struck," "bombed," "shelled," "launched an offensive," "engaged in firefight"
- Battlefield casualty counts: "X killed in airstrike," "Y wounded in shelling"
- Weapons deployment: "missile attack," "drone strike," "artillery barrage"
- Armed groups in combat: "insurgents attacked," "military operation killed"
- Territorial control through combat: "captured the town," "seized the base"
- War crime descriptions (active): "massacre of civilians," "execution of prisoners"
- Weapons manufacturing framed as progress: "new missile factory opens," "domestically-produced bombs reduce reliance on imports," "defense sector drives economic growth," "next-generation combat system unveiled"
- Military build-up as achievement: "navy commissions new warship," "air force debuts fighter jet," "defense budget increase strengthens military"
- Arms industry as innovation: "breakthrough in drone technology," "AI-powered combat system," "advanced missile guidance"
- Defense exports as success: "record arms sales," "weapons deal signed," "military equipment export growth"
- State violence as order: "police dispersed protesters," "security forces restored calm," "border patrol expanded," "militarized police," "lethal force against demonstrators"

**Strong NOT-Violence Signals (push score lower):**
- Recovery/reconstruction language: "rebuilt," "restored," "returned home," "cleared mines"
- Peace/diplomacy language: "ceasefire," "peace talks," "negotiations," "agreement signed," "diplomatic solution," "reconciliation"
- Disarmament language: "weapons ban," "non-proliferation," "decommissioning," "arms reduction," "treaty limits"
- Historical framing: "X years since," "commemorated," "anniversary," "archaeological discovery of," "museum exhibit on"
- Policy/legal framing (accountability): "budget allocated for oversight," "parliament voted to restrict," "court ruled," "tribunal indicted," "investigation found"
- Prevention/security (non-combat): "arrested suspects," "disrupted plot," "enhanced security," "counter-terrorism operation"
- Humanitarian/victim framing: "refugees resettled," "survivors supported," "trauma care," "civilian protection"
- Scientific/research framing: "study finds," "researchers analyzed," "data shows" (unless the research is about improving weapons)

## Anti-Hallucination Rule

Every key signal cited in `key_signals` **must** be an exact quote from the article text, or state `"No evidence in article"`. Never invent violence details the article does not contain.

## Discriminator

The decisive test: **does this article, as a whole, make violence or instruments of violence seem normal, acceptable, desirable, or a source of progress?**

If the article is ABOUT stopping, reducing, healing from, or accounting for violence → NOT violence promotion.
If the article is ABOUT the violence itself, or about the tools of violence as achievement → VIOLENCE PROMOTION.

## Examples

### Example 1: Active Combat (Score: 9)
**Headline:** "Russian Missile Strike Kills 12 in Kharkiv Apartment Block"
**Key terms:** "missile strike," "killed," "S-300," "emergency services pulled bodies from rubble"
**Reasoning:** Primary subject is an active military strike with casualties. All verbs are combat verbs. The article normalises violence by centering the attack itself.

### Example 2: Post-Conflict Recovery (Score: 1)
**Headline:** "Kharkiv Residents Return to Rebuilt Apartment Block Two Years After Strike"
**Key terms:** "returned," "rebuilt," "two years after," "new windows," "community center reopened"
**Reasoning:** Subject is recovery and reconstruction. The conflict is historical context, not the primary subject. The article is about healing from violence, not promoting it.

### Example 3: Ceasefire/Peace (Score: 1)
**Headline:** "Government and Rebels Sign Landmark Ceasefire Agreement After Months of Talks"
**Key terms:** "ceasefire," "sign," "talks," "agreement," "mediators"
**Reasoning:** Subject is peace process. The action is diplomacy — stopping violence, not promoting it.

### Example 4: Weapons Manufacturing as Progress (Score: 9)
**Headline:** "Israel Opens Domestically-Produced Bomb Line, Reducing Reliance on US Imports"
**Key terms:** "domestically-produced bombs," "reducing reliance," "new production line," "strategic independence," "defense manufacturing milestone"
**Reasoning:** Primary subject is weapons manufacturing framed as achievement and strategic success. The article promotes instruments of mass violence as progress. No active combat is described, but the normalization of weapons production as a desirable industrial capability makes this violence promotion.

### Example 5: Defense Policy Oversight (Score: 2)
**Headline:** "Parliamentary Committee Questions $40B Defense Budget, Demands Transparency on Procurement"
**Key terms:** "committee questions," "budget oversight," "transparency," "procurement review," "parliamentary hearing"
**Reasoning:** Subject is democratic oversight of defense spending. The framing is accountability, not promotion. The weapons spending is being scrutinized, not celebrated.

### Example 6: War Crimes Tribunal (Score: 1)
**Headline:** "ICC Issues Arrest Warrant for Former Commander Over 2010 Atrocities"
**Key terms:** "arrest warrant," "ICC," "tribunal," "2010," "former commander," "charged with"
**Reasoning:** Subject is international justice for PAST violence. The article holds violence to account — it does not promote it.

### Example 7: Drone Strike (Score: 10)
**Headline:** "US Drone Strike Targets Al-Shabaab Commander in Somalia, 8 Killed"
**Key terms:** "drone strike," "targets," "killed," "commander," "operation"
**Reasoning:** Active military strike operation. Combat verb, battlefield casualties. The violence IS the story.

### Example 8: Terrorism Arrest (Score: 1)
**Headline:** "Police Arrest 5 Suspected ISIS Members in Coordinated European Raids"
**Key terms:** "arrest," "suspected," "raids," "police," "preventive operation"
**Reasoning:** Subject is law enforcement preventing terrorism. No active combat, no promotion of violence. Arrests and raids by police stopping violence.

### Example 9: Arms Industry as Innovation (Score: 8)
**Headline:** "Next-Generation Combat Drone with AI Targeting Completes First Flight Test"
**Key terms:** "combat drone," "AI targeting," "flight test," "next-generation," "autonomous capabilities," "defense contractor"
**Reasoning:** Subject is military technology R&D framed as technological achievement. While no active combat is described, the article promotes an instrument of violence as innovation and progress.

### Example 10: Disarmament Agreement (Score: 0)
**Headline:** "120 Nations Sign Treaty Banning Autonomous Weapons Systems"
**Key terms:** "banning," "treaty," "autonomous weapons," "sign," "landmark agreement," "humanitarian"
**Reasoning:** Subject is restricting weapons, not promoting them. The article is about stopping violence, making it the clearest possible negative case.

### Example 11: Demining Technology (Score: 1)
**Headline:** "AI-Powered Demining Robot Clears 500 Landmines Per Day in Ukraine"
**Key terms:** "demining," "clears landmines," "saves civilian lives," "post-conflict clearance," "humanitarian technology"
**Reasoning:** Subject is technology for removing instruments of violence and protecting civilians. The robot is a military-derived technology, but its purpose is cleaning up after violence, not promoting it. Violence-prevention technology.

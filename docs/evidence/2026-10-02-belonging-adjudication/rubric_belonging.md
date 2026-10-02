# Belonging adjudication rubric (2026-10-02; Q1–Q3 ruled by the owner the same day)

Judges read this before any article. It replaces the oracle's breadth with the owner's rulings; the oracle only
supplies dimension scores for rows judged `in_scope` (`docs/TODO.md` ▶ START HERE item 0).

**Sources of the rules** (owner, 2026-10-02, recorded in
`docs/evidence/2026-10-01-belonging-v2-test-set/README.md` § *Owner rulings*):
- the MIDDLE definition (`H-BV6`)
- the "doing" test (ovr.news `docs/BRAND.md:84`, adopted)
- the #130 ruling (belonging = cohesion that is holding or growing; harm-answered cohesion counts only when the
  response is the story)

- **Q1–Q3 below** (owner, 2026-10-02). Each was asked as a multiple-choice question, and the owner chose the
  recommended option. What the owner saw was the option's label plus its IN/OUT example lists. Those are quoted here
  as the ruling.
  - Wording the owner did NOT see is marked *(Claude's gloss)*. It entered the rubric before the pilot judges ran.
  - The owner ruled the line, not each row of `exemplars.tsv`.

## The question

**Is this article about ordinary people acting together, where the shared action does something with a concrete
result?**

`in_scope` needs all three:
1. **Ordinary people, together.** Residents, volunteers, members, a congregation, a village, pupils, a group of peers.
   Not a single person or one family; not an official, company or institution acting on people.
2. **Doing.** The group builds, restores, cleans, teaches, protects, cares for someone, or keeps a practice alive.
3. **The doing is the story.** The article is about the shared action, not about a harm, a ceremony, a person's
   biography, or a topic with a community in the background.

A harm in the background does not disqualify: the response can be the story (Robinvale: owners protecting a massacre
site; a seed bank keeping farming going in Gaza).

## Out of scope: one verdict per class

| verdict | the shape | example (from `exemplars.tsv`) |
|---|---|---|
| `out_gift_official` | a one-off gift, donation, award or grant from a person, company, official or foundation; an official ceremony, inauguration, campaign or state commemoration | a chief donates learning materials; officials reopen a restored mosque |
| `out_event_crowd` | a crowd at an event (festival audience, parade, race, charity run); a gathering only to celebrate or grieve | a car festival with 700 entrants; a charity run opened by a mayor and sponsors |
| `out_one_person` | one person or one family is the subject, however kind | one barber gives free haircuts; one family keeps a pottery craft for 465 years |
| `out_harm_is_story` | the harm, grievance, conflict or demand is the story; a protest FOR DEMANDS | a synagogue shooting; communities demand self-determination |
| `out_culture_topic` | culture, heritage, identity or history as a topic (museum, book, film, artist, cuisine), with nobody acting together now | a museum's metalwork collection; a wedding-feast photo essay |
| `out_other` | anything else off-lens: sport results, animals, business, policy, public services run by staff | a shelter dog finds a home; a karate medal |
| `cannot_judge` | the text is too short or broken to judge | |

`in_scope` is not the default. If you cannot name the group, the action and its result, it is not `in_scope`.

## Q1 (ruled): a festival or tradition kept alive

Does keeping a festival or tradition going count as "keeping a practice alive"?

**Ruling** (option label: "Only when people carry it"). It counts when the community itself carries the practice.
*(Claude's gloss, not shown to the owner: "and the article shows them doing it, with a stake beyond the show.")*
The owner's IN list:
- a ritual that maintains the village springs
- a divided people staging their own yearly kingdom
- schools running a swim event in te reo

The owner's OUT list (the framing "a spectacle or an anniversary" is Claude's):
- a royal reed dance told through one debutante
- a list of mid-autumn celebrations
- a band's 45th year

## Q2 (ruled): gatherings after a harm, under the "doing" test

Ruling (c) made a march after a harm count when the gathering is the story (Morwell → P). The later "doing" test
excludes a gathering only to grieve. The two collide.

**Ruling: the doing test wins for training.** Ruling (c) stands for Morwell, which stays P in the v2 test set.
In training, remembering or mourning alone is `out_event_crowd`:
- a march remembering a 1942 raid
- a diaspora vigil for flood victims
- boarding-school remembrance marches

A gathering that acts toward others is `in_scope`: 100+ mosques opening their doors to neighbours after attacks.

## Q3 (ruled): programmes, services, clubs and a group's gift

The middle ruling names "ordinary people acting together". Many stories (including several curator picks) are
programmes run by an organisation.

**Ruling: participants build it.**
- **In:** participants build something together. Inmates co-creating a prison theatre company; women leaving shelters
  writing songs together.
- **Out (`out_other`):** a service delivered by staff (a city's unarmed response teams), or a programme told through
  one participant.
- **Out (`out_other`):** a social club or networking group with no shared result. It is a bond, but it does nothing.
- **Out (`out_gift_official`):** a group's one-off gift (a women's cooperative donating soap). The ruling excluded
  one-off gifts by who gives them; this extends it to groups.

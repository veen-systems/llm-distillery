"""FROZEN DATA: the 37 `crime_violence` patterns of the deleted uplifting v7 prefilter.

`filters/uplifting/v7/prefilter.py` was deleted 2026-10-01 with every per-lens prefilter
(NexusMind#284, decision 0). `draw_v8_corpus.class_a_instrument` used these patterns as the
2026-08-28 census's class-A instrument, so they are kept here VERBATIM, as data, so the draw
stays reproducible. Source: `git show fe6c018:filters/uplifting/v7/prefilter.py`
(`UpliftingPreFilterV7()._compiled_exclusions["crime_violence"]`), compiled there with
re.IGNORECASE exactly as below. Do not edit: a change here changes which population the
v8 corpus ruling describes.
"""
import re

SOURCE = "fe6c018:filters/uplifting/v7/prefilter.py UpliftingPreFilterV7 crime_violence"

PATTERNS = [
    '\\b(murder|murdered|murderer|homicide|manslaughter)\\b',
    '\\b(rape|raped|rapist|sexual assault|sexually assaulted|molest|molestation)\\b',
    '\\b(assault|assaulted|stabbing|stabbed|shot dead)\\b',
    '\\b(child abuse|domestic violence|human trafficking)\\b',
    '\\b(sentenced to|guilty verdict|prison sentence)\\b',
    '\\b(convicted of|charged with murder|charged with rape|charged with assault)\\b',
    '\\b(perpetrator|sex offender|violent offender)\\b',
    '\\b(life sentence|death penalty|death row)\\b',
    '\\b(tbs met|terbeschikkingstelling)\\b',
    '\\b(armed robbery|violent robbery|kidnapping|abduction)\\b',
    '\\b(terrorist attack|terrorism|mass shooting|massacre)\\b',
    '\\b(verkracht|verkrachting|mishandeling|doodslag)\\b',
    '\\b(gevangenisstraf|levenslang)\\b',
    '\\b(moord|vermoord|doodslag|levensdelict)\\b',
    '\\b(verkracht|verkrachting|aanranding|zedendelict)\\b',
    '\\b(mishandeling|steekpartij|neergeschoten)\\b',
    '\\b(kindermishandeling|huiselijk geweld|mensenhandel)\\b',
    '\\b(veroordeeld tot|gevangenisstraf|levenslang)\\b',
    '\\b(tbs met|terbeschikkingstelling|dader|zedendelinquent)\\b',
    '\\b(gewapende overval|gijzeling|ontvoering)\\b',
    '\\b(terroristische aanslag|schietpartij|bloedbad)\\b',
    '\\b(mord|ermordet|totschlag|tötungsdelikt)\\b',
    '\\b(vergewaltigung|vergewaltigt|sexuelle nötigung)\\b',
    '\\b(körperverletzung|messerstecherei|erschossen)\\b',
    '\\b(kindesmisshandlung|häusliche gewalt|menschenhandel)\\b',
    '\\b(verurteilt zu|gefängnisstrafe|lebenslänglich)\\b',
    '\\b(täter|sexualstraftäter|gewalttäter)\\b',
    '\\b(bewaffneter überfall|entführung|geiselnahme)\\b',
    '\\b(terroranschlag|amoklauf|massaker)\\b',
    '\\b(meurtre|assassinat|homicide|tué)\\b',
    '\\b(viol|violée|agression sexuelle)\\b',
    '\\b(agression|poignardé|abattu)\\b',
    '\\b(maltraitance|violence domestique|traite des êtres humains)\\b',
    '\\b(condamné à|peine de prison|perpétuité)\\b',
    '\\b(auteur|agresseur sexuel|délinquant violent)\\b',
    "\\b(braquage|enlèvement|prise d'otage)\\b",
    '\\b(attentat terroriste|fusillade|massacre)\\b',
]

COMPILED = [re.compile(p, re.IGNORECASE) for p in PATTERNS]

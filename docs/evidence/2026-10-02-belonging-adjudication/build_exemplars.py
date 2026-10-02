"""Belonging adjudication, phase 1: the exemplar list the owner reviews.

    python3 docs/evidence/2026-10-02-belonging-adjudication/build_exemplars.py ex_rows.jsonl

`ex_rows.jsonl` is `fetch_exemplar_rows.py`'s output (run on sadalsuud). Writes:
  docs/evidence/2026-10-02-belonging-adjudication/exemplars.tsv   ids + titles only (public repo)
  datasets/belonging_adjudication/exemplars_full.jsonl             full text, gitignored (for the judges)

Raises on an exemplar without a fetched row, a duplicate id, an unknown code, or any overlap with
the belonging v2 test set (exemplars stay out of every evaluation set: the v2 leakage lesson).
Every verdict below is Claude's reading. The `Q*` boundaries were ruled by the owner on 2026-10-02
(rubric_belonging.md); the owner ruled the line, not each row."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CODES = {'P', 'B', 'Q1', 'Q2', 'Q3', 'out_gift_official', 'out_event_crowd', 'out_one_person',
         'out_harm_is_story', 'out_culture_topic', 'out_other'}

# (code, verdict, article id, reason). Q codes name the ruled boundary the row illustrates. B = borderline: kept for
# the record, never a teaching example (moved out of P after review, 2026-10-02).
EX = [
    ('P', 'in_scope', 'british_irish_guardian_uk_3243001d4d87', 'volunteers plant and keep station platforms: building, a lasting result'),
    ('P', 'in_scope', 'pan_african_alwihda_info_4f54e2c1d59c', 'former pupils re-roof and fence their old school'),
    ('P', 'in_scope', 'positive_news_upworthy_59a8c7bcb616', 'five residents assemble furniture for neighbours in need'),
    ('P', 'in_scope', 'pan_african_alwihda_info_001ee450862f', 'youth and women\'s networks clean the provincial hospital'),
    ('P', 'in_scope', 'new_zealand_rnz_27443af4a058', 'iwi-led project removes predators to restore the island'),
    ('P', 'in_scope', 'new_zealand_rnz_ea40d98aca4b', 'mana whenua and volunteers (with scientists, council) plant resistant kauri'),
    ('B', 'borderline', 'australian_abc_au_62f89804707d', 'a police sergeant\'s idea, residents collaborate; the centre is also a service'),
    ('B', 'borderline', 'positive_news_good_good_good_b7018371df8b', 'a non-profit conservation programme, told through one fisher (the Q3 shape)'),
    ('B', 'borderline', 'south_asian_kathmandu_post_b174b0718f3f', 'researchers\' opinion column on what communities do in general'),
    ('B', 'borderline', 'positive_news_the_better_india_ad0d12b375d0', 'volunteers removed 500+ tonnes of waste, but told as a founder\'s foundation'),
    ('out_one_person', 'out_one_person', 'british_irish_guardian_world_4fd06b1ecec8', 'one founder and his daughter run a seed bank; ~200 farmers receive'),
    ('B', 'borderline', 'british_irish_guardian_global_development_b1f393447e12', 'a 754-char teaser: thousands gather for debate tournaments (crowd or revived practice?)'),
    ('Q3', 'out_other', 'belgian_dh_les_sports_7b211d4e274c', 'a non-profit programme; communes pay the student tutors: a staff-delivered service'),
    ('B', 'borderline', 'canadian_global_news_4a972b8d4973', 'residents mend clothes together at a one-off event'),

    ('Q1', 'in_scope', 'indonesian_mongabay_id_df1256862239', 'a village ritual that maintains seven springs: the practice has a concrete result'),
    ('Q1', 'in_scope', 'vietnamese_vnexpress_vn_adc0f4200ce3', 'a border-divided people stage their own one-day kingdom every year'),
    ('Q1', 'in_scope', 'new_zealand_rnz_ee2a0e342301', 'schools run a swim event entirely in te reo: teaching the language'),
    ('Q1', 'out_event_crowd', 'southeast_asian_free_malaysia_4a48f131f94f', 'a horse race returns: jockeys race, spectators cheer'),
    ('Q1', 'out_event_crowd', 'belgian_gazet_van_antwerpen_c8ce317be3c6', 'a street band marks its 45th year: an anniversary, told by one member'),
    ('Q1', 'out_event_crowd', 'south_african_the_citizen_41a1e118ea3d', 'a royal ceremony with 30,000 participants, told through one debutante'),
    ('Q1', 'out_event_crowd', 'new_zealand_rnz_5fff0c2b0765', 'communities celebrate a festival: a listing of celebrations'),

    ('Q2', 'out_event_crowd', 'belgian_bruzz_158fc4479141', '300 residents march to remember the 1942 raid: remembering only'),
    ('Q2', 'out_event_crowd', 'belgian_vrt_nieuws_en_44ea7f8f1042', 'a diaspora community gathers to mourn flood victims'),
    ('Q2', 'out_gift_official', 'positive_news_indian_country_today_702c427322a1', 'remembrance marches; the government sponsored the events (state commemoration)'),
    ('Q2', 'in_scope', 'british_irish_guardian_society_f638847b2ce9', '100+ mosques answer attacks by opening their doors to neighbours'),

    ('Q3', 'in_scope', 'positive_news_upworthy_7475185b4e12', 'inmates co-create the productions of a prison theatre company'),
    ('Q3', 'in_scope', 'australian_abc_au_3e493327e09f', 'women leaving shelters write and sing together in a 12-month program'),
    ('Q3', 'out_other', 'us_news_npr_a1ebc2062563', 'a city\'s unarmed response teams: a public service run by staff'),
    ('Q3', 'out_other', 'positive_news_reasons_to_be_cheerful_e4a08299c3bb', 'a sailing program for disabled people, told through one participant'),
    ('Q3', 'out_gift_official', 'west_african_aib_burkina_568a2c586e0f', 'a women\'s cooperative donates soap to a health centre: a group\'s one-off gift'),
    ('Q3', 'out_other', 'arabic_khaleej_times_96980715085f', 'a seniors\' social club: bonds, but nothing done with them'),
    ('Q3', 'out_other', 'australian_abc_au_620918255c16', 'a young professionals\' networking group meeting at a pub'),

    ('out_gift_official', 'out_gift_official', 'pan_african_ghanaian_chronicle_43da82a4c491', 'a chief donates learning materials'),
    ('out_gift_official', 'out_gift_official', 'west_african_punch_ng_09d36ee26016', 'the navy inaugurates a water project'),
    ('out_gift_official', 'out_gift_official', 'industry_intelligence_fast_company_3563f570db8e', 'a celebrity foundation\'s free-book program expands'),
    ('out_gift_official', 'out_gift_official', 'balkan_klix_ba_bd27573beaeb', 'officials and clergy reopen a restored mosque (Claude\'s "fits" in the reader snapshot)'),
    ('out_event_crowd', 'out_event_crowd', 'australian_abc_au_fb9f91573d7b', 'a car festival with 700 entrants'),
    ('out_event_crowd', 'out_event_crowd', 'balkan_klix_ba_9293dc1e3839', 'a charity run opened by a mayor, a minister and sponsors (Claude\'s "fits" in the reader snapshot)'),
    ('out_event_crowd', 'out_event_crowd', 'east_african_lexpress_madagascar_b156bebd2863', 'crowds watch traditional wrestling'),
    ('out_one_person', 'out_one_person', 'portuguese_sonoticiaboa_7b16a6d053ec', 'a mother graduates at 45'),
    ('out_one_person', 'out_one_person', 'south_american_cuba_headlines_d8011b247ea7', 'one barber gives free haircuts: kind, but one person'),
    ('out_one_person', 'out_one_person', 'spanish_eldiario_1292add7258e', 'one family keeps a pottery craft for 465 years'),
    ('out_harm_is_story', 'out_harm_is_story', 'canadian_globe_mail_25d28179bec7', 'a synagogue shooting'),
    ('out_harm_is_story', 'out_harm_is_story', 'mexican_la_jornada_4e91608fec09', 'communities demand self-determination: a protest for demands'),
    ('out_one_person', 'out_one_person', 'arabic_aljazeera_en_58e9bf65540b', 'one farmer defends her land against settler attacks: one person, not a group'),
    ('out_culture_topic', 'out_culture_topic', 'caucasus_hetq_91f3097815a3', 'a museum\'s metalwork collection'),
    ('out_culture_topic', 'out_culture_topic', 'arabic_aljazeera_en_112f5841e86c', 'a wedding feast tradition, as a photo essay'),
    ('out_culture_topic', 'out_culture_topic', 'balkan_vecernji_945ff97a63eb', 'a theologian\'s new book'),
    ('out_other', 'out_other', 'baltic_err_ee_965fde51649d', 'a shelter dog finds a home'),
    ('out_other', 'out_other', 'south_asian_kathmandu_post_b576b8c2d153', 'a karate bronze medal'),
    ('out_other', 'out_other', 'us_news_npr_786c48d8cebc', 'one family farm switches from pigs to mushrooms'),
]

ids = [e[2] for e in EX]
if len(set(ids)) != len(ids):
    raise SystemExit('duplicate exemplar id')
for code, *_ in EX:
    if code not in CODES:
        raise SystemExit(f'unknown code {code!r}')
rows = {}
for line in open(sys.argv[1]):
    r = json.loads(line)
    rows[r['id']] = r
missing = [i for i in ids if i not in rows]
if missing:
    raise SystemExit(f'no fetched row for {missing}')
def norm(u):
    # Keep the query (some sites address articles by ?p=<id>); drop only tracking parameters and the fragment.
    base, _, query = (u or '').split('#')[0].partition('?')
    query = '&'.join(q for q in query.split('&') if q and not re.match(r'(utm_|fbclid|gclid)', q))
    base = re.sub(r'\.amp$', '', re.sub(r'^https?://(www\.)?', '', base).rstrip('/').lower())
    return base + ('?' + query if query else '')
test = [json.loads(l) for l in open(os.path.join(ROOT, 'docs/evidence/2026-10-01-belonging-v2-test-set/test_set.jsonl'))]
if any(not t.get('id') for t in test):
    raise SystemExit('a v2 test-set row has no id: the overlap guard would degrade to urls only')
test_ids, test_urls = {t['id'] for t in test}, {norm(t['url']) for t in test}
clash = [i for i in ids if i in test_ids or norm(rows[i]['url']) in test_urls]
if clash:
    raise SystemExit(f'exemplars in the v2 test set: {clash}')
titles = {}  # ovr's English title for reader-sample rows
for line in list(open(os.path.join(ROOT, 'docs/evidence/2026-10-02-belonging-reader-snapshot/reader_sample_200.tsv')))[1:]:
    c = line.rstrip('\n').split('\t')
    titles[c[2]] = c[7]

out_dir = os.path.join(ROOT, 'datasets', 'belonging_adjudication')
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(HERE, 'exemplars.tsv'), 'w') as pub, \
        open(os.path.join(out_dir, 'exemplars_full.jsonl'), 'w') as full:
    pub.write('code\tclaude_verdict\tarticle_id\tfrom\tlanguage\traw\ttitle\treason\n')
    for code, verdict, i, reason in EX:
        r = rows[i]
        frm = 'reader_sample' if r['src'] == 'reader' else 'curator_pick'
        title = titles.get(i) or r['title']
        pub.write(f"{code}\t{verdict}\t{i}\t{frm}\t{r['lang']}\t{r['raw']:.2f}\t{title}\t{reason}\n")
        full.write(json.dumps({'id': i, 'code': code, 'claude_verdict': verdict, 'reason': reason,
                               'url': r['url'], 'title': r['title'], 'source': r['source'],
                               'content': r['content']}, ensure_ascii=False) + '\n')
print(f'{len(EX)} exemplars -> exemplars.tsv and {out_dir}/exemplars_full.jsonl')

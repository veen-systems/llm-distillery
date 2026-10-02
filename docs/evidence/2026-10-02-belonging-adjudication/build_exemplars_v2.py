"""Belonging adjudication, phase 1R: the exemplar list under rubric_belonging_v2.md.

    python3 docs/evidence/2026-10-02-belonging-adjudication/build_exemplars_v2.py ex_rows.jsonl

`ex_rows.jsonl` is `fetch_exemplar_rows.py`'s output (run on sadalsuud). Writes:
  docs/evidence/2026-10-02-belonging-adjudication/exemplars_v2.tsv   ids + titles only (public repo)
  datasets/belonging_adjudication/exemplars_v2_full.jsonl          full text, gitignored (for the judges)

Raises on an exemplar without a fetched row, a duplicate id, an unknown code, or any overlap with
the belonging v2 test set (exemplars stay out of every evaluation set: the v2 leakage lesson).
Every verdict below is Claude's reading of rubric_belonging_v2.md; the owner rules the lines, and reviews this list
(B rows carry an open question). Also raises on overlap with the first pilot's sample or the dev-check rows."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CODES = {'P', 'B', 'out_gift_official', 'out_one_moment', 'out_harm_is_story', 'out_culture_topic',
         'out_event_spectated', 'out_other'}

# (code, verdict, article id, reason). Q codes name the ruled boundary the row illustrates. B = borderline: kept for
# the record, never a teaching example (moved out of P after review, 2026-10-02).
EX = [
    ('P', 'in_scope', 'british_irish_guardian_uk_3243001d4d87', 'volunteer groups keep their stations planted: ongoing bonds around a shared place'),
    ('P', 'in_scope', 'pan_african_alwihda_info_4f54e2c1d59c', 'former pupils re-roof and fence their old school: place attachment, contribution'),
    ('P', 'in_scope', 'positive_news_upworthy_59a8c7bcb616', 'residents of a retirement home keep helping neighbours assemble furniture'),
    ('P', 'in_scope', 'pan_african_alwihda_info_001ee450862f', 'youth and women\'s networks clean their hospital together (a community event people take part in)'),
    ('P', 'in_scope', 'new_zealand_rnz_27443af4a058', 'iwi-led restoration of their island; "protecting native species and healing whanau"'),
    ('P', 'in_scope', 'new_zealand_rnz_ea40d98aca4b', 'mana whenua and volunteers plant kauri on their ranges'),
    ('P', 'in_scope', 'indonesian_mongabay_id_df1256862239', 'a village ritual the people carry that maintains their springs (Q1 IN list)'),
    ('P', 'in_scope', 'vietnamese_vnexpress_vn_adc0f4200ce3', 'a border-divided people stage their own yearly kingdom and re-meet (Q1 IN list)'),
    ('P', 'in_scope', 'new_zealand_rnz_ee2a0e342301', 'schools run a swim event in te reo: a language carried by the community (Q1 IN list)'),
    ('P', 'in_scope', 'positive_news_upworthy_7475185b4e12', 'inmates co-create a prison theatre company over decades (Q3 IN)'),
    ('P', 'in_scope', 'australian_abc_au_3e493327e09f', 'women leaving shelters write and sing together (Q3 IN)'),

    ('P', 'in_scope', 'arabic_khaleej_times_96980715085f', 'a seniors\' club meeting every other Saturday: ongoing bonds (ruled IN)'),
    ('P', 'in_scope', 'spanish_eldiario_1292add7258e', 'one family passes a pottery craft down for 465 years: intergenerational (ruled IN)'),
    ('B', 'borderline', 'australian_abc_au_62f89804707d', 'a police sergeant\'s idea, residents collaborate; the centre is also a service'),
    ('B', 'borderline', 'positive_news_good_good_good_b7018371df8b', 'a non-profit conservation programme, told through one fisher'),
    ('B', 'borderline', 'south_asian_kathmandu_post_b174b0718f3f', 'researchers\' opinion column on what communities do in general'),
    ('B', 'borderline', 'positive_news_the_better_india_ad0d12b375d0', 'volunteers removed 500+ tonnes of waste, told as a founder\'s foundation (founder-told ruling)'),
    ('B', 'borderline', 'british_irish_guardian_global_development_b1f393447e12', 'a 754-char teaser: thousands gather for debate tournaments'),
    ('B', 'borderline', 'canadian_global_news_4a972b8d4973', 'residents mend clothes together at a one-off event'),
    ('B', 'borderline', 'british_irish_guardian_society_f638847b2ce9', 'mosques open doors to neighbours after attacks; an 838-char teaser, institutions as actors'),
    ('B', 'borderline', 'balkan_klix_ba_9293dc1e3839', 'citizens walk for children with cancer (taking part), opened by a mayor, a minister and sponsors'),
    ('B', 'borderline', 'british_irish_guardian_world_4fd06b1ecec8', 'a community seed bank told through its founder and his daughter (founder-told ruling)'),

    ('out_gift_official', 'out_gift_official', 'pan_african_ghanaian_chronicle_43da82a4c491', 'a chief donates learning materials'),
    ('out_gift_official', 'out_gift_official', 'west_african_punch_ng_09d36ee26016', 'the navy inaugurates a water project'),
    ('out_gift_official', 'out_gift_official', 'industry_intelligence_fast_company_3563f570db8e', 'a celebrity foundation\'s free-book program expands'),
    ('out_gift_official', 'out_gift_official', 'balkan_klix_ba_bd27573beaeb', 'officials and clergy reopen a restored mosque'),
    ('out_gift_official', 'out_gift_official', 'west_african_aib_burkina_568a2c586e0f', 'a women\'s cooperative donates soap: a group\'s one-off gift (Q3)'),
    ('out_gift_official', 'out_gift_official', 'positive_news_indian_country_today_702c427322a1', 'government-sponsored remembrance events (state commemoration)'),
    ('out_one_moment', 'out_one_moment', 'portuguese_sonoticiaboa_7b16a6d053ec', 'a mother graduates at 45: an achievement'),
    ('out_one_moment', 'out_one_moment', 'south_american_cuba_headlines_d8011b247ea7', 'one barber gives free haircuts: a viral kindness'),
    ('out_one_moment', 'out_one_moment', 'south_african_the_citizen_41a1e118ea3d', 'a royal reed dance told through one debutante (Q1 OUT list)'),
    ('out_harm_is_story', 'out_harm_is_story', 'canadian_globe_mail_25d28179bec7', 'a synagogue shooting'),
    ('out_harm_is_story', 'out_harm_is_story', 'mexican_la_jornada_4e91608fec09', 'communities demand self-determination: the political fight'),
    ('out_harm_is_story', 'out_harm_is_story', 'arabic_aljazeera_en_58e9bf65540b', 'one farmer endures settler attacks: the harm is the story'),
    ('out_harm_is_story', 'out_harm_is_story', 'belgian_bruzz_158fc4479141', 'residents march to remember a 1942 raid: remembering only (Q2)'),
    ('out_harm_is_story', 'out_harm_is_story', 'belgian_vrt_nieuws_en_44ea7f8f1042', 'a diaspora community gathers to mourn flood victims: grieving only (Q2)'),
    ('out_culture_topic', 'out_culture_topic', 'caucasus_hetq_91f3097815a3', 'a museum\'s metalwork collection'),
    ('out_culture_topic', 'out_culture_topic', 'arabic_aljazeera_en_112f5841e86c', 'a wedding feast tradition, as a photo essay'),
    ('out_culture_topic', 'out_culture_topic', 'balkan_vecernji_945ff97a63eb', 'a theologian\'s new book'),
    ('out_event_spectated', 'out_event_spectated', 'australian_abc_au_fb9f91573d7b', 'a car festival: drag races and burnouts watched by crowds'),
    ('out_event_spectated', 'out_event_spectated', 'east_african_lexpress_madagascar_b156bebd2863', 'crowds watch traditional wrestling'),
    ('out_event_spectated', 'out_event_spectated', 'southeast_asian_free_malaysia_4a48f131f94f', 'a horse race returns: jockeys race, spectators cheer'),
    ('out_event_spectated', 'out_event_spectated', 'new_zealand_rnz_5fff0c2b0765', 'a listing of mid-autumn celebrations (Q1 OUT list)'),
    ('out_event_spectated', 'out_event_spectated', 'belgian_gazet_van_antwerpen_c8ce317be3c6', 'a street band marks its 45th year (Q1 OUT list)'),
    ('out_other', 'out_other', 'us_news_npr_a1ebc2062563', 'a city\'s unarmed response teams: a service run by staff (Q3)'),
    ('out_other', 'out_other', 'positive_news_reasons_to_be_cheerful_e4a08299c3bb', 'a sailing programme told through one participant (Q3)'),
    ('out_other', 'out_other', 'belgian_dh_les_sports_7b211d4e274c', 'a non-profit tutoring programme with paid student tutors (Q3)'),
    ('out_other', 'out_other', 'australian_abc_au_620918255c16', 'a young professionals\' networking group (v1 OUT: professional networking)'),
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
# The first pilot's 96 sample rows (its 4 controls ARE exemplars) and the 10 dev-check rows are never exemplars.
key = [json.loads(l) for l in open(os.path.join(HERE, 'key.jsonl'))]
pilot = {k['id'] for k in key if k['stratum'] != 'control'}
if len(pilot) != 96:
    raise SystemExit(f'key.jsonl has {len(pilot)} sample ids, expected 96')
dev = {l.split('\t')[1] for l in list(open(os.path.join(HERE, 'spot_check_key.tsv')))[1:]}
if len(dev) != 10:
    raise SystemExit(f'spot_check_key.tsv has {len(dev)} ids, expected 10')
if set(ids) & (pilot | dev):
    raise SystemExit(f'exemplars in the first pilot or the dev check: {sorted(set(ids) & (pilot | dev))}')
titles = {}  # ovr's English title for reader-sample rows
for line in list(open(os.path.join(ROOT, 'docs/evidence/2026-10-02-belonging-reader-snapshot/reader_sample_200.tsv')))[1:]:
    c = line.rstrip('\n').split('\t')
    titles[c[2]] = c[7]

out_dir = os.path.join(ROOT, 'datasets', 'belonging_adjudication')
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(HERE, 'exemplars_v2.tsv'), 'w') as pub, \
        open(os.path.join(out_dir, 'exemplars_v2_full.jsonl'), 'w') as full:
    pub.write('code\tclaude_verdict\tarticle_id\tfrom\tlanguage\traw\ttitle\treason\n')
    for code, verdict, i, reason in EX:
        r = rows[i]
        frm = 'reader_sample' if r['src'] == 'reader' else 'curator_pick'
        title = titles.get(i) or r['title']
        pub.write(f"{code}\t{verdict}\t{i}\t{frm}\t{r['lang']}\t{r['raw']:.2f}\t{title}\t{reason}\n")
        full.write(json.dumps({'id': i, 'code': code, 'claude_verdict': verdict, 'reason': reason,
                               'url': r['url'], 'title': r['title'], 'source': r['source'],
                               'content': r['content']}, ensure_ascii=False) + '\n')
print(f'{len(EX)} exemplars -> exemplars_v2.tsv and {out_dir}/exemplars_v2_full.jsonl')

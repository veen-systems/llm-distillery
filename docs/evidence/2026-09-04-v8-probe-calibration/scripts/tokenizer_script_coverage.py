"""Does multilingual-e5-small actually READ every script in the v8 corpus?

Answers the encoder layer of "is the probe multilingual" — not by citing the model card,
but by tokenising a sentence in each of the nine scripts the corpus contains and checking
for UNK tokens and lossless round-trip. A model that silently maps a script to UNK would
still produce embeddings, and they would be noise.

Run on b650-gpu with venv-prodparity (sentence-transformers is not in the repo .venv):
    venv-prodparity/bin/python tokenizer_script_coverage.py
Result 2026-09-04: vocab 250,002, ZERO UNK in all 9 scripts, all round-trip.
"""
from transformers import AutoTokenizer
tk = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small")
samples = {
 "LATIN":"Community garden feeds 500 families",
 "GREEK":"Η κοινότητα δημιούργησε έναν κήπο",
 "ARABIC":"حديقة المجتمع تطعم خمسمائة أسرة",
 "CYRILLIC":"Общественный сад кормит пятьсот семей",
 "HANGUL":"공동체 정원이 오백 가구를 먹여 살린다",
 "CJK":"社区花园养活了五百个家庭",
 "DEVANAGARI":"सामुदायिक उद्यान पाँच सौ परिवारों को खिलाता है",
 "HEBREW":"גן קהילתי מאכיל חמש מאות משפחות",
 "ARMENIAN":"Համայնքային այգին կերակրում է հինգ հարյուր ընտանիք",
}
unk = tk.unk_token_id
print("vocab %d, tokenizer %s" % (tk.vocab_size, type(tk).__name__))
print("  %-12s %7s %5s  round-trips?" % ("script","tokens","UNK"))
for s,t in samples.items():
    ids = tk(t, add_special_tokens=False)["input_ids"]
    n_unk = sum(1 for i in ids if i == unk)
    back = tk.decode(ids)
    ok = "yes" if back.strip()==t.strip() else "LOSSY"
    print("  %-12s %7d %5d  %s" % (s, len(ids), n_unk, ok))

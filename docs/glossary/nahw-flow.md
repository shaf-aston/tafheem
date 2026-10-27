# Nahw flow: typed sentence → iʿrāb cards and tree

The map of the tahleel engine, stage by stage, with the file that owns each step.
Read this first, then open the file named. Picture version, with a worked example:
https://claude.ai/artifact/KiAJ7Wo9Y7pW4w3R3ATDHt

**Kept true by `tests/nahw/test_nahw_flow_doc.py`.** Every path below must exist, and every
list between `<!-- list:NAME -->` markers must match the code's own registry, in order.
Change a stage, add a rule or reorder one → that test fails until this page says so.

## 0. Entry

`backend/routers/analyze.py` → `backend/services/nahw/iraab.py` `analyze`:

1. Split words (`split_words`), keep typed vowels.
2. One reading per word: `backend/services/sarf/morphology.py` `pick` (BERT ranks, then the reading that fits the most typed vowels; a line of nouns alone, a pronoun counted as one, with a منصوب in it reads its first possible past verb as that verb: زيد نصر بكرا، هُوَ أَكْرَمَ ضَيْفًا; a word the dictionary cannot read is read off sarf's table (`backend/services/sarf/verb_reader.py` `reading_of`), a verb the dictionary has winning over one no text uses, a command with its object pronoun written on too: اِهْدِنَا is هَدَى + نا, not a dual of هَدَنَ). Cards and parser share it.
3. Recorded Qurʾān ayah → `backend/services/nahw/tarkeeb_store.py`, skip to cards.
4. Else `backend/services/nahw/syntax/__init__.py` `read`: stages 1–7 below. Any error → every word unnamed.

## 1. Parse

`backend/services/nahw/syntax/catib_onnx.py` `parse`: cut attached pieces (ال stays on the word), record each token's typed case, score every head and label, then `backend/services/nahw/syntax/decode.py` picks one clean tree.
Before labels are chosen, the book's masks rule labels out (`backend/services/nahw/syntax/mask.py` `book_mask`):

<!-- list:vetoes -->
- verb_subject_follows: a noun before its verb is never its subject (a fatha noun stays open: fronted object)
<!-- /list -->

## 2. Repair (tokens corrected in place)

`backend/services/nahw/syntax/repair/__init__.py` `correct`, in this order. Typed words ≠ tokens → only the first runs.

<!-- list:repair -->
- book_links: fixed structures written over the parser (`backend/services/nahw/syntax/mask.py`)
- typed_words: retag by what was typed, command shapes (bare letters too where the sentence vouches for a verb: no dictionary reading, or an object on an elative: اكتبي درسك، ارفعي صوتك; never on a noun with a sign of the noun: called, or in jarr as مضاف إليه or a jarr noun's صفة: يَا رَبِّ، لِلَّهِ رَبِّ الْعَالَمِينَ; a command to one woman takes the ي split off as "my" as its doer: قُومِي; the plural's alef, dropped before a pronoun, comes back: اُكْتُبُوهُ), muḍāf flag (`backend/services/nahw/syntax/repair/typed.py`)
- since_jarr: a built time word that is also a preposition (مُنْذُ أَمْسِ، مُذْ شَهْرٍ) before a noun → the preposition, the noun its majrur (`backend/services/nahw/syntax/repair/typed.py`)
- jarr_after_mudaf: a noun typed in jarr with no جار, hung elsewhere, straight after a noun typed with its case but no tanween and no ال (زَيْدٌ أَكْرَمُ رِجَالٍ) → that noun's مضاف إليه; never after a name (بِسْمِ اللَّهِ الرَّحْمَنِ), nor after a diptote put in jarr, whose fatha has no tanween to drop (بِمَسَاجِدَ كَثِيرَةٍ) (`backend/services/nahw/syntax/repair/typed.py`)
- emphasis_lam_opener: a لام typed with a fatha onto a noun (لَزَيْدٌ قَائِمٌ، وَلَلْآخِرَةُ خَيْرٌ) hung as a جار → لام الابتداء: the noun takes its place, the لام hangs on it; hung on a word after it, as its صفة or its doer (لَأَنْتُمْ أَشَدُّ، لَزَيْدٌ يَقُومُ) → its مبتدأ, as that لام heads the sentence and comes onto no فاعل (`backend/services/nahw/syntax/repair/typed.py`)
- asked_man: an opening مَنْ with no verb in the sentence → the question word, not the relative (`backend/services/nahw/syntax/repair/asked.py`)
- man_before_verb: an opening مَنْ the parser hung on the verb after it → the مبتدأ, the verb its khabar (مَنْ أَكْرَمَ ضَيْفًا); when the verb holds its own doer (مَنْ أَكْرَمْتَ) → its fronted object (`backend/services/nahw/syntax/repair/asked.py`)
- subject_clash: a raf' noun the parser made the object of a verb with no doer → its doer (أَحَبَّ زَيْدٌ عَمْرًا; a command already holds its doer, the hidden أنت (قُلْ هُوَ اللَّهُ أَحَدٌ)); second noun after a raf' subject → the verb's object (`backend/services/nahw/syntax/repair/subject_clash.py`)
- kana_subject: a raf' noun right after كان/ليس, with a later predicate → كان's subject, not its khabar; a خبر the parser hung on the subject → كان's khabar; a باء hung on لست as a modifier → the باء of ليس's khabar (لَسْتُ بِغَافِلٍ) (`backend/services/nahw/syntax/repair/subject_clash.py`)
- inna_object: a noun in nasb (or ـات with its kasra: لَآيَاتٍ) the parser hung as إنّ's object (إِنَّ فِي ذَلِكَ لَآيَةً) → its اسم (`backend/services/nahw/syntax/repair/subject_clash.py`)
- zanna_pair: under ظن and its sisters, a nasb noun the parser kept as the subject of the nasb word after it → the verb's first object, that word its second (`backend/services/nahw/syntax/repair/subject_clash.py`)
- praise_specified: after نعم/بئس, an indefinite nasb noun → the verb's تمييز (its doer a hidden pronoun), the raf' noun after → the one praised (`backend/services/nahw/syntax/repair/subject_clash.py`)
- doer_first: two names after a verb that show no case (ضرب موسى عيسى) → the first the doer, the second the object (`backend/services/nahw/syntax/repair/subject_clash.py`)
- doer_after_object: a subject typed in nasb with a raf' word hung on it → the object, that word the doer (`backend/services/nahw/syntax/repair/subject_clash.py`)
- verb_under_fronted_object: a verb with its doer, after it or in it (زَيْدًا ضَرَبْتُ، زَيْدًا اضْرِبْ، زَيْدًا ضَرَبُوا: the ا، و، ن of two or many is the doer), hung as the صفة of a nasb noun before it → the verb heads, the noun its fronted object; with a pronoun back to the noun (زَيْدًا ضَرَبْتُهُ) the same, its governor then a verb like it, left out (`backend/services/nahw/syntax/repair/subject_clash.py`)
- object_after_tanween: a nasb word hung as مضاف إليه on a participle with tanween → its object (`backend/services/nahw/syntax/repair/subject_clash.py`)
- object_past_verb: a nasb word hung past a verb onto the noun the verb hangs on (زَيْدٌ نَصَرَ بَكْرًا) → the verb's, named object, hal or tamyeez by verb_place (`backend/services/nahw/syntax/repair/subject_clash.py`)
- called: a verb the parser hung on يا → a sentence of its own, not a second منادى (`backend/services/nahw/syntax/repair/called.py`)
- dua_clause: a praying noun (ويل، سلام) in raf' with a لِ phrase after it → a mubtada of its own with that khabar, not the verb's doer (`backend/services/nahw/syntax/repair/dua.py`)
- counted_times: مرة/مرتين hung on a jar-majrur → the verb's (`backend/services/nahw/syntax/repair/dua.py`)
- object_of_noun: a raf' word the parser hung as the object of a plain raf' noun opening the sentence → its khabar; a nasb noun after an elative khabar → the elative's تمييز (`backend/services/nahw/syntax/repair/khabar.py`)
- elative_specified: an indefinite noun written in nasb that the parser hung on an elative as its مضاف إليه → its تمييز, since a مضاف إليه is in jarr (أَشَدُّ رَهْبَةً; a diptote's fatha stays jarr: أَفْضَلُ مَسَاجِدَ) (`backend/services/nahw/syntax/repair/khabar.py`)
- after_pointer: an indefinite word (or a مضاف to one: زَيْدٌ صَاحِبُ مَالٍ) hung as the صفة of a definite opener (هذا، زيد، ال), or a describing word hung as its subject, or as the subject of the ظرف or جار ومجرور of its صلة (وَمَا عِنْدَ اللَّهِ خَيْرٌ وَأَبْقَى) → the khabar (`backend/services/nahw/syntax/repair/khabar.py`)
- told_of_jar: a noun hung as the subject of a preposition's majrur (لِزَيْدٍ هَذَا الْكِتَابُ، لِمَنْ هَذَا) → the مبتدأ of the fronted جار ومجرور (`backend/services/nahw/syntax/repair/khabar.py`)
- second_khabar: an adjective hung on an adjective khabar → a second khabar, not its صفة (`backend/services/nahw/syntax/repair/khabar.py`)
- before_la: a noun hung on لا from before it → the mubtada, the لا clause its khabar (`backend/services/nahw/syntax/repair/khabar.py`)
- hasr_khabar: a noun after إلا in a negated verbless clause → the khabar of the mubtada before it (`backend/services/nahw/syntax/repair/khabar.py`)
- described_doer: a singular وصف after a negation or question word, then a raf' noun → the وصف heads the clause (مبتدأ), the noun its doer (`backend/services/nahw/syntax/repair/khabar.py`)
- hal_clause: و + a raf' pronoun + a verb → a hal clause, the pronoun its mubtada (`backend/services/nahw/syntax/repair/hal.py`)
- nasab: name + ابن/بن + noun → صفة and مضاف chain; next noun = خبر in a verbless sentence (`backend/services/nahw/syntax/repair/nasab.py`)
- untied_command: a command read as a jazm condition's answer (إن تضربْ أضربْ) with no فاء on it → jussive present, جواب الشرط (`backend/services/nahw/syntax/repair/answer.py`)
- stamp: particle families from the particle decision tree; a place the parser gave the لام of emphasis → the word it is written onto (إِنَّ هَذَا لَسِحْرٌ) (`backend/services/nahw/syntax/particles.py`, `backend/data/nahw_rules/particle_tree.json`)
<!-- /list -->

Book links, in order (switches in `backend/data/nahw_rules/closed_words.json` → `vetoes`):

<!-- list:links -->
- pointer_heads_its_noun: هذا الكتابُ → the pointer takes the pair's place
- ma_cancels_inna: إنّما → ما stops إنّ working
- listed_preposition_takes_majrur: رُبَّ رجلٍ → listed word becomes حرف جر
- preposition_over_its_noun: أليس اللهُ بكافٍ → a حرف جر the parser hung under its jarr noun heads it
- topic_carries_its_verb: الولدُ يكتبُ → noun is mubtadaʾ, verb clause its khabar
- exception_word_by_case: خلا/عدا/حاشا read by the next noun's vowel
- inner_sentence: زيدٌ أبوه عالمٌ → a mini sentence as khabar or ṣila
<!-- /list -->

## 3. Naming (read only)

`backend/services/nahw/syntax/naming.py` `roles`. Each word answers five questions (`backend/services/nahw/syntax/facts/__init__.py` `AXES`), in order:

<!-- list:axes -->
- kind: particle / verb / noun (`backend/services/nahw/syntax/facts/kind.py`)
- follows: ṣifa / maʿṭūf / tawkīd / badal / none (`backend/services/nahw/syntax/facts/follows.py`)
- governor: what works its case; a call with يا left off (رَبَّنَا اغْفِرْ: a مضاف opening the sentence, nasb or untyped, a command after it; اللَّهُمَّ) has none, the card says يا is left off; nor has an object put before a verb busied with its pronoun (الاشتغال: زَيْدًا ضَرَبْتُهُ، زَيْدًا مَرَرْتُ بِهِ), the card says a verb like it, left out, governs it (`backend/services/nahw/syntax/facts/governor.py`)
- slot: its place: subject, khabar, object… (`backend/services/nahw/syntax/facts/slot.py`)
- voice: active / passive (`backend/services/nahw/syntax/facts/voice.py`)
<!-- /list -->

The answers walk the book tree (`backend/services/nahw/syntax/walker.py`, `backend/data/nahw_rules/naming_tree.json`); the leaf is the role. Then: particle with a مجرور → حرف جر; case per word (typed vowel first, else the role's case from `backend/data/nahw_rules/teacher.json` `case_of_role`); followers copy their head's case; pair names (اسم لا); conditions (`backend/services/nahw/syntax/condition.py`).

Roles the tree can give:

<!-- list:roles -->
- اسم إن
- اسم كاد
- اسم كان
- بدل
- تمييز
- توكيد
- حال
- حرف
- خبر
- خبر إن
- خبر كاد
- خبر كان
- صفة
- فاعل
- فعل
- مبتدأ
- مجرور
- مستثنى
- مضاف إليه
- معطوف
- مفعول به
- مفعول فيه
- مفعول لأجله
- مفعول مطلق
- مفعول معه
- منادى
- نائب فاعل
<!-- /list -->

## 4. Teacher check

`backend/services/nahw/syntax/teacher.py` `review`, in order; a caught word is dashed and later checks see it gone. Switches and reasons: `backend/data/nahw_rules/teacher.json` → `checks`.

<!-- list:checks -->
- one_subject: one verb, one doer
- passive_has_no_doer: a passive verb has no فاعل
- typed_case_fits_role: the typed vowel must fit the role
- khabar_needs_mubtada: no mubtadaʾ-type word → every خبر dashed
- ism_inna_needs_inna: no إنّ-family word → every اسم إن dashed
- follower_needs_noun: a follower needs a noun before it, or the doer of the verb right before it (ذَهَبْتُ أَنَا، قُمْ أَنْتَ)
- tamyeez_needs_number: a تمييز needs a number or measure
<!-- /list -->

## 5. Tree

`backend/services/nahw/syntax/tree.py` `build`: columns, hidden words (ثابت, فعل محذوف over a nasb noun no word governs, its nasb shown by tanween, a follower or a مضاف إليه: شكرًا، سبحانَ اللهِ, ضمير مستتر), clauses (صلة, خبر, مصدر مؤول, مقول القول), unit labels from `backend/data/nahw_rules/roles.json`, sentence label (شرطية → تعجبية → استفهامية → فعلية → اسمية). A root word with no role → a phrase: no sentence wrap, no summary.

## 6. Cards

`backend/services/nahw/iraab.py` `cards`: what the word is (`backend/services/nahw/rule_engine.py`), the tree's role pasted on, the sign (`backend/services/nahw/signs.py`), then pair names, غير/سوى, the "also" line, attached pieces, condition wording. Summary = top label only when it names a sentence (`backend/services/nahw/syntax/tree.py` `names_a_sentence`).

## Checking a change

- Unit tests: `tests/nahw/test_naming.py`, `tests/nahw/test_syntax_tree.py`, `tests/nahw/test_teacher.py`.
- Live: `python -m backend.scripts.nahw.score_iraab --set probe --api URL --show 50` (50 keyed sentences, `backend/data/nahw_rules/probe_sentences.json`).

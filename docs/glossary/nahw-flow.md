# Nahw flow: typed sentence → iʿrāb cards and tree

The map of the tahleel engine, stage by stage, with the file that owns each step.
Read this first, then open the file named. Picture version, with a worked example:
https://claude.ai/artifact/KiAJ7Wo9Y7pW4w3R3ATDHt

**Kept true by `tests/nahw/test_nahw_flow_doc.py`.** Every path below must exist, and every
list between `<!-- list:NAME -->` markers must match the code's own registry, in order.
Change a stage, add a rule or reorder one → that test fails until this page says so.

## 0. Entry

`backend/routers/analyze.py` → `backend/services/nahw/iraab.py` `analyze`:

1. Split words (`words`, `backend/services/text/arabic_text.py`), keep typed vowels.
2. One reading per word: `backend/services/sarf/morphology.py` `pick` (BERT ranks, then the reading that fits the most typed vowels (a ى with a mark on it counts as a ياء, `harakat._spelled`: إِلَىَّ is إِلَيَّ, إِلَى and my ي); a name in nasb the dictionary files without its alif is read so where no reading fits the vowels (by the reading its vowels fit: وَعَمْرًا is عَمْرو, its و that tells it from عُمَر written only out of nasb, `closed_words.json` `farqa_waw`), or, typed bare, where the ranked verb adds a shadda the name does not: زيدا is زَيْدًا, not the verb زَيَّدَا, while a particle stays: bare الا is إِلَّا; a مضاف typed bare with only its مضاف إليه after it tells no thought, so it is the past verb it reads as (أكل الطعام، شرب الماء: الكلام ... من فعل واسم, Ibn Aqil V1 p14; typed vowels still choose: أَكْلُ الطَّعَامِ); a word shaped like the elative, read as a verb, straight before a preposition with a مِنْ phrase after it and no verb before the مِنْ, is the elative (أَوْعَى لَهُ مِنْهُ، أَحَبَّ إِلَيْهِ مِنْ وَالِدِهِ; Tashil V1 p132: its مفضول follows it or what it governs); a line of nouns alone, a pronoun counted as one, with a منصوب in it reads its first possible past verb as that verb: زيد نصر بكرا، هُوَ أَكْرَمَ ضَيْفًا, unless a participle with tanween before it is its عامل already: أَنَا ضَارِبٌ زَيْدًا; with no reading agreeing with the typed vowels, one spelled with the typed letters wins, a typed ة never read as the pronoun ه: حِجَارَةٌ is حِجَارَة, not حَجّارُهُ; a word the dictionary cannot read is read off sarf's table (`backend/services/sarf/verb_reader.py` `reading_of`, with the spellings the table does not print: يَقْرَءُونَ's hamza on the line, and a present's nasb fatha for its damma: أَنْ تَحْبَطَ is حَبِطَ's present, not a past of a four-letter تحبط, `backend/data/sarf/reading.json` `spellings`), a noun it lacks off its shape too, a sound plural's or dual's ending peeled for its number and case (`backend/services/sarf/noun_reader.py`: مُسْرِعِينَ is مسرع, plural, nasb or jarr), a verb the dictionary has winning over one no text uses, a command typed with its hamzat al-wasl, opening the word or after a joined وَ/فَ, is that command, not the أَفْعَلَ its letters also spell, its joined letter kept as a piece of its own: وَاشْرَبُوا، فَاقْبَلْهَا (`backend/services/text/harakat.py` `vowel_agreement`); a command with its object pronoun written on too: اِهْدِنَا is هَدَى + نا, not a dual of هَدَنَ (a doer written as a long letter ends that verb on the vowel before it: اُكْتُبِيهِ is اُكْتُبِي + هِ, ضَرَبُوهُ is ضَرَبُوا + هُ); a past verb's doer is the one sarf's table reads off its ending, and its verb too where the dictionary's reading contradicts the typed vowels, as for the passives it lacks: ضُرِبْتُ is أنا, not ضَرَبَتْ; كُسِيتُ is كَسَا's, not كَسِيَ). A foreign name in a verb's shape (Sharh al-Tasrih V2 p708: أعجمي على وزن فاعل كآزر) is that name where the reader's vowels fit it, the dictionary has no name so spelled, and the Qur'an says those letters alone only as a name (`backend/services/quran/corpus.py` `name_of`: كَانَ اسْمُ أَبِيهِ آزَرَ; عاد, a people and a verb, is none); typed bare it stays the dictionary's, and a typed past verb opening the sentence stays the verb (آزَرَ زَيْدٌ عَمْرًا). Typed bare, it is that name where no noun comes next to be the verb's doer or object (the sentence ends, or a new one opens): قال إبراهيم لأبيه آزر is the name, آزر الجيش الشعب the verb. A lemma whose sure letters the word lacks is no lemma of it: CAMeL files every رأى under راوند (rhubarb), so the word takes the Qur'an's lemma of its root and kind holding most of its letters, رأى (`backend/services/dictionary/roots.py` `lemma_of`), which ظن وأخواتها is known by. Cards and parser share it; a card takes sarf's command over a noun its letters spell, never over one called (`verb_reader.called`: يَا رَبِّ، رَبِّ اغْفِرْ لِي، رَبِّ زِدْنِي are رَبّ, not رَبَّى's command), nor over one with a sign of the noun on it: typed in jarr after a preposition, or listed only as a ظرف (`verb_reader.noun_marked`: عَلَى مَالِ is مال, دُونَ is a ظرف, Ibn Aqil V1 p15). Cells of sarf's table that differ only in voice read as the active (تُضَارُّونَ: a doubled letter spells both alike; `verb_reader.reading_of`); a command with a joined letter or an object pronoun on it is split off the table too (`morphology._table_verb`: فَاعْزِمُوا, اِهْدِنَا), and so is the verb after the question hamza when no reading of the dictionary holds its vowels (أَيَعْجِزُ: the dictionary has يَعْجَزُ, `morphology._asked_reading`). A فاء written before the oath's واو (فَوَاللَّهِ، فَوَالَّذِي) is a piece of its own, the dictionary's guessed name "والله" split back to وَ + the sworn-by (Ibn Aqil vol 4 p42; `morphology._fa_before_oath`).
3. Recorded Qurʾān ayah → `backend/services/nahw/tarkeeb_store.py`, skip to cards. The build (`backend/scripts/nahw/build_tarkeeb.py`) names a question word a خبر hangs on its مبتدأ (وَمَا أَدْرَاكَ، مَا مَنَعَكَ; tarkeeb.json `question_nouns`, never هل/أ/متى…). On the card the vowelled name is read bare: a question word or relative becomes built in its place, a declined word whose vowel CAMeL did not read takes the name's case (ٱلدِّينِ), a noun the treebank names a particle (لَعَلَّهُ) is that particle, and a particle the book has no reason for says «مبني لا محل له من الإعراب» (`backend/services/nahw/iraab.py` `_named`, `backend/services/nahw/book.py` `reason`, teacher.json `case_said.particle`).
4. Else `backend/services/nahw/syntax/__init__.py` `read`: stages 1–5 below (Parse to Tree); stage 6, Cards, is `iraab.cards`. Any error → every word unnamed. A word typed with no vowel on it may read another way (`morphology._rival`: the verb's other voice off sarf's table, else a close-ranked reading of another kind): the sentence is then read once more with those rivals swapped in (`iraab._rivalled`, at most settings `rivals_read`), and a word whose job is another in that reading says so on its card (`assumed`: its other job, and the word whose other reading makes it so).

## 1. Parse

`backend/services/nahw/syntax/catib_onnx.py` `parse`: cut attached pieces (ال stays on the word), record each token's typed case, score every head and label, then `backend/services/nahw/syntax/decode.py` picks one clean tree.
Before labels are chosen, the book's masks rule labels out (`backend/services/nahw/syntax/mask.py` `book_mask`):

<!-- list:vetoes -->
- verb_subject_follows: a noun before its verb is never its subject (a fatha noun stays open: fronted object)
<!-- /list -->

## 2. Repair (tokens corrected in place)

`backend/services/nahw/syntax/repair/__init__.py` `correct`, in this order. Typed words ≠ tokens → only the first and the last run.

<!-- list:repair -->
- book_links: fixed structures written over the parser (`backend/services/nahw/syntax/mask.py`)
- typed_words: retag a word by what was typed on it: command shapes, a noun's sign, a verb's vowels (`backend/services/nahw/syntax/repair/typed.py`)
- adverb_only: قط, عوض and a built قبل/بعد typed with the damma stay the zarf (`backend/services/nahw/syntax/repair/typed.py`)
- compound_number: a unit with عشر typed after it → one built number (`backend/services/nahw/syntax/repair/number.py`)
- since_jarr: a built time word that is also a preposition (مُنْذُ أَمْسِ، مُذْ شَهْرٍ) before a noun → the preposition, the noun its majrur (`backend/services/nahw/syntax/repair/typed.py`)
- jarr_after_mudaf: a jarr noun with no جار, straight after a case-typed noun with no tanween or ال → its مضاف إليه (`backend/services/nahw/syntax/repair/typed.py`)
- nunless_mudaf: a nunless sound plural before a noun showing no case → that noun's مضاف إليه (`backend/services/nahw/syntax/repair/typed.py`)
- emphasis_lam_opener: a لام typed with a fatha onto a noun, hung as a جار → لام الابتداء, the noun its مبتدأ (`backend/services/nahw/syntax/repair/typed.py`)
- asked_man: an opening مَنْ with no verb in the sentence → the question word, not the relative (`backend/services/nahw/syntax/repair/asked.py`)
- man_before_verb: an opening مَنْ hung on the verb after it → the مبتدأ, or the fronted object if the verb holds its doer (`backend/services/nahw/syntax/repair/asked.py`)
- asked_anna: أنّى tagged a particle by the analyser → the question noun (`adv_interrog`), as أين (`backend/services/nahw/syntax/repair/asked.py`)
- asked_before_verb: كم/ماذا before a verb → the مبتدأ, or the fronted object if the verb has its doer (`backend/services/nahw/syntax/repair/asked.py`)
- asked_of_kana: a question noun before a كان-sister with no khabar → its khabar, brought to the front (`backend/services/nahw/syntax/repair/asked.py`)
- added_to_verb: a noun hung on a verb as مضاف إليه → its doer, or its object when typed in nasb (`backend/services/nahw/syntax/repair/subject_clash.py`)
- excepted_after_doer: a noun before غير/سوى hung as a verb's object → its doer, the excepting word the excepted (`backend/services/nahw/syntax/repair/subject_clash.py`)
- first_object_owed: under a verb of two objects with one object, a caseless noun hung on the doer → the first object (`backend/services/nahw/syntax/repair/subject_clash.py`)
- subject_clash: a raf' noun hung as the object of a doer-less verb → its doer; a second noun after a raf' subject → its object (`backend/services/nahw/syntax/repair/subject_clash.py`)
- described_known: a describing word with ال after a known noun in its case → its صفة, not a second object (`backend/services/nahw/syntax/repair/typed.py`)
- name_told_to: a name taken as a saying verb's object, straight after a jarr noun → that noun's بدل (`backend/services/nahw/syntax/repair/subject_clash.py`)
- repeated_doer: a raf' pronoun of the verb's own person right after it → the doer said again (توكيد) (`backend/services/nahw/syntax/repair/subject_clash.py`)
- kana_subject: a raf' noun right after كان/ليس, a predicate after it → كان's اسم, not its khabar (`backend/services/nahw/syntax/repair/subject_clash.py`)
- kana_fronted_khabar: a nasb noun right after كان made its اسم by the parser → its khabar (`backend/services/nahw/syntax/repair/subject_clash.py`)
- kana_nasb_khabar: a nasb noun after كان's اسم, hung as an object or modifier, while it has no khabar → that khabar (`backend/services/nahw/syntax/repair/subject_clash.py`)
- inna_object: a noun in nasb (or ـات with its kasra: لَآيَاتٍ) the parser hung as إنّ's object (إِنَّ فِي ذَلِكَ لَآيَةً) → its اسم (`backend/services/nahw/syntax/repair/subject_clash.py`)
- inna_second_khabar: a noun hung as a second subject after إنّ's or لا's khabar, or ending a pair with no khabar → a khabar (`backend/services/nahw/syntax/repair/subject_clash.py`)
- zanna_pair: under ظن, a nasb noun kept as subject of the nasb word after it → first object, that word the second (`backend/services/nahw/syntax/repair/subject_clash.py`)
- praise_specified: after نعم/بئس, an indefinite nasb noun → its تمييز, the raf' noun after → the one praised (`backend/services/nahw/syntax/repair/subject_clash.py`)
- doer_first: a caseless name after a doer-less verb, then a second name → the first its doer, the second its object (`backend/services/nahw/syntax/repair/subject_clash.py`)
- doer_after_object: a subject typed in nasb with a raf' word hung on it → the object, that word the doer (`backend/services/nahw/syntax/repair/subject_clash.py`)
- late_doer: a raf' noun hung as a نعت or مضاف إليه under a doer-less verb → that verb's doer, which may come last (`backend/services/nahw/syntax/repair/subject_clash.py`)
- outer_doer: a second raf' noun on a verb that has its doer, below a doer-less verb → that verb's doer (`backend/services/nahw/syntax/repair/subject_clash.py`)
- verb_under_fronted_object: a verb with its doer, hung as the صفة of a nasb noun before it → the verb heads, the noun its object (`backend/services/nahw/syntax/repair/subject_clash.py`)
- object_after_tanween: a nasb word hung as مضاف إليه on a participle with tanween → its object (`backend/services/nahw/syntax/repair/subject_clash.py`)
- described_after_tanween: a noun with tanween takes no مضاف إليه, so one hung so → its صفة (`backend/services/nahw/syntax/repair/typed.py`)
- object_past_verb: a nasb word hung past a verb onto the verb's own noun → the verb's object, hal or tamyeez (`backend/services/nahw/syntax/repair/subject_clash.py`)
- relative_owed: a relative hung on the doer, under a verb that owes an object → the verb's object (`backend/services/nahw/syntax/repair/subject_clash.py`)
- called: a verb the parser hung on يا → a sentence of its own, not a second منادى (`backend/services/nahw/syntax/repair/called.py`)
- called_annexes: a noun with no link straight after a called noun that shows no damma or tanween → its مضاف إليه, typed bare (يا عبد الله اجتهد) (`backend/services/nahw/syntax/repair/called.py`)
- dua_clause: a praying noun (ويل، سلام) in raf' with a لِ phrase after it → a mubtada of its own with that khabar, not the verb's doer (`backend/services/nahw/syntax/repair/dua.py`)
- counted_times: مرة/مرتين hung on a jar-majrur → the verb's (`backend/services/nahw/syntax/repair/dua.py`)
- object_of_noun: a raf' word hung as the object of an opening raf' noun → its khabar (`backend/services/nahw/syntax/repair/khabar.py`)
- elative_specified: an indefinite nasb noun hung on an elative as مضاف إليه → its تمييز (`backend/services/nahw/syntax/repair/khabar.py`)
- after_pointer: an indefinite word hung as the صفة of a definite opener (هذا، زيد) → that opener's khabar (`backend/services/nahw/syntax/repair/khabar.py`)
- relative_khabar: a known opener, then مَنْ/ما with its صلة and nothing else said → the relative is its khabar (`backend/services/nahw/syntax/repair/khabar.py`)
- majrur_of_jar: the noun straight after a preposition that the parser hung as a subject (هَلْ مِنْ مُجِيبٍ) → the preposition's majrur (`backend/services/nahw/syntax/repair/khabar.py`)
- told_of_jar: a noun hung as the subject of a preposition's majrur (لِزَيْدٍ هَذَا الْكِتَابُ، لِمَنْ هَذَا) → the مبتدأ of the fronted جار ومجرور (`backend/services/nahw/syntax/repair/khabar.py`)
- zarf_is_no_subject: a place or time word hung as the subject of the indefinite noun after it → that noun's شبه جملة, the khabar said first (`backend/services/nahw/syntax/repair/khabar.py`)
- khabar_said_first: two khabars hung on a pair-governing particle, a place or time word then an indefinite noun → the noun is its name (`backend/services/nahw/syntax/repair/khabar.py`)
- second_khabar: an adjective hung on an adjective khabar → a second khabar, not its صفة (`backend/services/nahw/syntax/repair/khabar.py`)
- naat_after_its_noun: a word with ال hung before the indefinite word that heads a verbless sentence → the mubtada, that word its khabar (`backend/services/nahw/syntax/repair/khabar.py`)
- before_la: a noun hung on لا from before it → the mubtada, the لا clause its khabar (`backend/services/nahw/syntax/repair/khabar.py`)
- la_over_its_khabar: لا hung under the word after its noun → لا heads the pair, the noun its اسم, that word its خبر (`backend/services/nahw/syntax/repair/khabar.py`)
- hasr_khabar: a noun after إلا in a negated verbless clause → the khabar of the mubtada before it (`backend/services/nahw/syntax/repair/khabar.py`)
- described_doer: a singular وصف after a negation or question word, then a raf' noun → the وصف heads the clause (مبتدأ), the noun its doer (`backend/services/nahw/syntax/repair/khabar.py`)
- hal_clause: و + a raf' pronoun or noun + a verb or khabar → a hal clause, the noun its mubtada (`backend/services/nahw/syntax/repair/hal.py`)
- oath_clause: opening و + a relative or jarr noun, the clause answered by a lam, لا, ما, قد or إن → the oath (`backend/services/nahw/syntax/repair/clause.py`)
- amma_clause: أما + one noun + a فاء answer → the noun is the mubtada, the answer its khabar, a verb it was doer of its صلة (`backend/services/nahw/syntax/repair/clause.py`)
- negated_conjunct: و + لا + a known noun hung on the لا → joined to the noun before the و, the لا only stressing the negation (`backend/services/nahw/syntax/repair/clause.py`)
- doer_then_khabar: a verb with a pronoun object, a doer and a second raf' noun → the second is the khabar of a left-out مبتدأ (`backend/services/nahw/syntax/repair/clause.py`)
- no_khabar_on_full_verb: an indefinite nasb word hung as the خبر of a full verb → a modifier, so a hal (`backend/services/nahw/syntax/repair/hal.py`)
- naat_beside_its_noun: an indefinite word right after the verb's own masdar it agrees with → that masdar's صفة (`backend/services/nahw/syntax/repair/hal.py`)
- elative_describes: an elative right after an indefinite nasb or jarr noun → that noun's نعت (`backend/services/nahw/syntax/repair/hal.py`)
- nasab: name + ابن/بن + noun → صفة and مضاف chain; next noun = خبر in a verbless sentence (`backend/services/nahw/syntax/repair/nasab.py`)
- untied_command: a command read as a jazm condition's answer (إن تضربْ أضربْ) with no فاء on it → jussive present, جواب الشرط (`backend/services/nahw/syntax/repair/answer.py`)
- stamp: particle families from the particle decision tree, one reading per small word (`backend/services/nahw/syntax/particles.py`)
- untangle: after book_links and every repair, a word left in a loop → the parser's own link back, or the root (`backend/services/nahw/syntax/repair/__init__.py`)
<!-- /list -->

Book links, in order (switches in `backend/data/nahw_rules/closed_words.json` → `vetoes`):

<!-- list:links -->
- pointer_heads_its_noun: هذا الكتابُ → the pointer takes the pair's place
- ma_cancels_inna: إنّما → ما stops إنّ working
- listed_preposition_takes_majrur: رُبَّ رجلٍ → listed word becomes حرف جر
- particle_over_its_noun: أليس اللهُ بكافٍ، إلا الذين آمنوا → a حرف جر or إلا the parser hung under its noun heads it
- excepting_noun_adds: حضر الضيوف سوى بكر → غير/سوى take the noun after as their مضاف إليه
- topic_carries_its_verb: الولدُ يكتبُ → noun is mubtadaʾ, verb clause its khabar
- exception_word_by_case: خلا/عدا/حاشا read by the next noun's vowel
- inner_sentence: زيدٌ أبوه عالمٌ → a mini sentence as khabar or ṣila
<!-- /list -->

## 3. Naming (read only)

`backend/services/nahw/syntax/naming.py` `roles`. Each word answers five questions (`backend/services/nahw/syntax/facts/__init__.py` `AXES`), in order:

<!-- list:axes -->
- kind: particle / verb / noun, read from the vowels typed and the dictionary (`backend/services/nahw/syntax/facts/kind.py`)
- follows: ṣifa / maʿṭūf / tawkīd / badal / none (`backend/services/nahw/syntax/facts/follows.py`)
- governor: what works its case (`backend/services/nahw/syntax/facts/governor.py`)
- slot: its place: subject, khabar, object… (`backend/services/nahw/syntax/facts/slot.py`)
- voice: active / passive (`backend/services/nahw/syntax/facts/voice.py`)
<!-- /list -->

Whether a noun is definite is asked of one fact only, `facts.is_known` (`backend/services/nahw/syntax/facts/sentence.py`): ال, a name, a pronoun, pointer or relative, or a مضاف to one of these (Tasheel V1 p21); the khabar and typed repairs and the particle tree ask it there, not CAMeL's `stt`. A time or place word is asked of `facts.is_zarf` the same way, over the one list in `closed_words.json` (`book.ADVERB_FAMILIES`).

The answers walk the book tree (`backend/services/nahw/syntax/walker.py`, `backend/data/nahw_rules/naming_tree.json`); the leaf is the role. Then: particle with a مجرور, or a جار whose majrur is أَنْ and its verb (إِلَى أَنْ يُوَفِّرُوا) → حرف جر; case per word (typed vowel first, else the role's case from `backend/data/nahw_rules/teacher.json` `case_of_role`); followers copy their head's case; pair names (اسم لا); conditions (`backend/services/nahw/syntax/condition.py`; a conditional noun before a verb with no doer of its own is the مبتدأ, the verb's hidden doer going back to it: مَنْ ذَبَحَ, and the fronted object where the verb has a doer written and takes an object: مَا تَدَّخِرِ الْأُسْرَةُ, `naming._noun_place`; a conditional noun no relative or question word shares its letters with opens after a clause too, its answer first, and before a verb listed as taking no object, a كان-sister (Tasheel 1.9) or a verb with its object pronoun written on it (فَمَنْ أَخَذَهُ) it is the مبتدأ: لَنْ نَتَرَاجَعَ مَهْمَا طَالَ الزَّمَنُ).

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

`backend/services/nahw/syntax/picture/jobs.py` `give_jobs`: a ما the parser links as the doer or object of a passive verb with no other noun of its own is the deputy; columns, hidden words (ثابت, فعل محذوف over a nasb noun no word governs, its nasb shown by tanween, a follower or a مضاف إليه: شكرًا، سبحانَ اللهِ, ضمير مستتر), clauses (صلة, خبر, مصدر مؤول, مقول القول), unit labels from `backend/data/nahw_rules/roles.json`, sentence label (شرطية → تعجبية → استفهامية → فعلية → اسمية). A noun phrase alone, its head shown in raf' or in no case, with no verb, khabar, فاعل or question word in it, is the khabar of an unwritten هذا (بابُ الفاعلِ، الطالبُ المجتهدُ; roles.json understood `subject`); مِن on an indefinite measure brings its تمييز, so no ثابت is drawn for it (كوبٌ كبيرٌ من القهوة; understood `measured`, closed_words tamyeez_head `measures`). After لولا and لوما the noun's khabar مَوْجُودٌ is drawn hidden, محذوف وجوبًا (condition by_word `khabar`). Any other root word with no role → a phrase: no sentence wrap, no summary. A unit headed by a particle has no job, but أيها, which the parser tags one, is the منادى it heads (`facts.is_particle`). A jar or ظرف hung on the very verb whose told sentence the subject heads is that verb's, so the sentence gets no ثابت (قال لي زيد هو يكتب; Mughni V1 p566). A ت verb's hidden doer goes back to its subject, or, for a صفة or حال sentence, to the noun it describes, which settles أنتَ أو هي as هي (حِجَارَةٌ لَا تَنْطِقُ; Ibn Aqil V3 p197).

## 6. Cards

`backend/services/nahw/iraab.py` `cards`: what the word is (`backend/services/nahw/rule_engine.py`), the tree's role pasted on, the sign (`backend/services/nahw/signs.py`: أَيُّهَا is built on أَيُّ's damma, its ها of attention written on, closed_words nida `attention`; إِنَّهُ on إِنَّ's fatha, not the pronoun's; a long letter with only a reciter's mark, مَآ، عَلَىٰ, on the sukun), then pair names, غير/سوى, the "also" line, attached pieces, the ها of attention, condition wording; a follower names the word it follows, and a built one first says the place of that word's case (يا أيها الذين: مبني في محل رفع, أيّ's built damma; رأيت الرجل الذي قام: في محل نصب) (`backend/services/nahw/card_wording/counting.py`, teacher.json `case_said` `follow_built`). Its notes say what the word is: a pronoun, pointer, name or relative is معرفة with no ال; only a present verb has a mood (`backend/services/sarf/morphology.py` `_build_features`). Summary = top label only when it names a sentence (`backend/services/nahw/syntax/tree.py` `names_a_sentence`).

## Checking a change

- Unit tests: `tests/nahw/test_naming.py`, `tests/nahw/test_syntax_tree.py`, `tests/nahw/test_teacher.py`.
- Live: `python -m backend.scripts.nahw.score_iraab --set probe --api URL --show 50` (50 keyed sentences, `backend/data/nahw_rules/probe_sentences.json`).

/**
 * Deeper levels for the Qur'anic Sciences chart ("04") of pbsData.js.
 * Key "04.<branch>.<kid>"          -> level 3: the same Arabic items as SUB, in the same order, with English.
 * Key "04.<branch>.<kid>.<item>"   -> level 4: named parts of that level-3 item (item = 0-based index in the level-3 list).
 * Entries are [arabic, english]. Source: al-Itqan fi Ulum al-Quran (al-Suyuti) and al-Burhan fi Ulum al-Quran (al-Zarkashi).
 * English glosses and level-4 topics were written by Claude from those books' known chapter contents, not copied from an edition.
 */
export const DEEP = {
  // Branch 0: revelation
  "04.0.0": [["التنزيل الجملي والمنجَّم", "Whole and gradual revelation"], ["حكمة التنجيم", "Wisdom of gradual revelation"], ["أنواع الوحي", "Kinds of revelation"], ["كيفية تلقّيه", "How it was received"]],
  "04.0.0.0": [["الإنزال إلى السماء الدنيا", "Sent down whole to the lowest heaven"], ["التنزيل المنجَّم على النبي", "Sent down in parts to the Prophet"]],
  "04.0.0.2": [["الرؤيا الصادقة", "True dream"], ["صلصلة الجرس", "Sound like a bell"], ["تمثّل الملك رجلًا", "Angel appearing as a man"], ["النفث في الرُّوع", "Inspiration cast into the heart"], ["الكلام بلا واسطة", "Direct speech without intermediary"]],
  "04.0.1": [["صيغ سبب النزول", "Wording that states a cause"], ["العبرة بعموم اللفظ", "Generality of wording governs"], ["تعدد النازل والسبب", "Many verses, many causes"], ["كتب الأسباب", "Books on causes"]],
  "04.0.1.0": [["الصريح", "Explicit statement"], ["المحتمل", "Probable statement"]],
  "04.0.2": [["ضوابط التمييز", "Criteria of distinction"], ["خصائص كلٍّ منهما", "Traits of each"], ["فائدة معرفته", "Benefit of knowing it"], ["ما نزل بمكة وحكمه مدني", "Revealed in Mecca, Medinan in ruling"]],
  "04.0.2.0": [["اعتبار زمن النزول", "By time: before or after the Hijra"], ["اعتبار مكان النزول", "By place of revelation"], ["اعتبار المخاطَب", "By the addressed audience"]],
  "04.0.3": [["أول ما نزل مطلقًا", "First revealed overall"], ["آخر ما نزل", "Last revealed"], ["أوائل الموضوعات", "Firsts by topic"]],
  "04.0.3.0": [["اقرأ باسم ربك", "Iqra, the opening of al-Alaq"], ["يا أيها المدثر", "Ya ayyuha al-muddaththir"], ["الفاتحة", "Al-Fatiha"]],
  "04.0.3.1": [["آية الربا", "Verse of usury"], ["واتقوا يومًا ترجعون فيه", "Guard against a Day you return"], ["آية الدَّين", "Verse of debt"], ["إذا جاء نصر الله", "Surah al-Nasr"]],
  "04.0.4": [["الليلي والنهاري", "Night and day revelation"], ["السفري والحضري", "Travel and residence"], ["الصيفي والشتائي", "Summer and winter"], ["ما نزل مرتين", "Revealed twice"]],

  // Branch 1: collection and writing
  "04.1.0": [["في عهد النبي", "In the Prophet's time"], ["جمع أبي بكر", "Abu Bakr's compilation"], ["جمع عثمان", "Uthman's compilation"], ["حرق المصاحف", "Burning other copies"]],
  "04.1.0.0": [["الحفظ في الصدور", "Memorising in hearts"], ["الكتابة في الرقاع", "Writing on materials"]],
  "04.1.1": [["توقيفية الآي", "Verse order is divinely fixed"], ["ترتيب السور والاجتهاد", "Surah order and ijtihad"], ["مصاحف الصحابة", "Companions' codices"]],
  "04.1.2": [["الرسم العثماني", "Uthmani script"], ["قواعده الست", "Its six rules"], ["الحذف والزيادة", "Omission and addition"], ["حكم الالتزام به", "Ruling on adhering to it"]],
  "04.1.2.1": [["الحذف", "Omission"], ["الزيادة", "Addition"], ["الهمز", "Hamza"], ["البدل", "Substitution"], ["الوصل والفصل", "Joining and separating"], ["ما فيه قراءتان", "Word with two readings"]],
  "04.1.3": [["نقط الإعجام", "Dots distinguishing letters"], ["نقط الإعراب", "Dots marking vowels"], ["أبو الأسود والخليل", "Abu al-Aswad and al-Khalil"], ["علامات الوقف", "Pause marks"]],
  "04.1.4": [["المدني والمكي والكوفي والبصري", "Madinan, Meccan, Kufan, Basran counts"], ["أسباب الاختلاف", "Causes of difference"], ["الأجزاء والأحزاب", "Juz and hizb divisions"], ["التخميس والتعشير", "Marking fives and tens"]],
  "04.1.4.0": [["المدني الأول", "First Madinan count"], ["المدني الأخير", "Last Madinan count"], ["المكي", "Meccan count"], ["الكوفي", "Kufan count"], ["البصري", "Basran count"], ["الشامي", "Syrian count"]],

  // Branch 2: readings
  "04.2.0": [["معناها", "Their meaning"], ["أقوال العلماء فيها", "Scholars' views on them"], ["علاقتها بالقراءات", "Link to the readings"], ["حكمة التيسير", "Wisdom of ease"]],
  "04.2.0.1": [["لغات سبع من لغات العرب", "Seven Arab dialects"], ["سبعة أوجه من الاختلاف", "Seven kinds of variation"], ["التيسير لا العدد المحدد", "Ease, not a fixed count"]],
  "04.2.1": [["القراء السبعة", "The seven reciters"], ["الثلاثة المتمّمة", "The three completing the ten"], ["شروط القراءة الصحيحة", "Conditions of a sound reading"], ["الطرق والروايات", "Routes and transmissions"]],
  "04.2.1.0": [["نافع", "Nafi of Madinah"], ["ابن كثير", "Ibn Kathir of Mecca"], ["أبو عمرو", "Abu Amr of Basra"], ["ابن عامر", "Ibn Amir of Syria"], ["عاصم", "Asim of Kufa"], ["حمزة", "Hamza of Kufa"], ["الكسائي", "al-Kisai of Kufa"]],
  "04.2.1.1": [["أبو جعفر", "Abu Jafar"], ["يعقوب", "Yaqub"], ["خلف", "Khalaf"]],
  "04.2.1.2": [["صحة السند", "Sound chain"], ["موافقة الرسم", "Agreement with the script"], ["موافقة العربية", "Agreement with Arabic"]],
  "04.2.2": [["ضابط الشذوذ", "Rule of the irregular"], ["القراءات الأربع", "The four extra readings"], ["الاحتجاج بها فقهًا ولغةً", "Using them in law and language"], ["التفسير بها", "Explaining through them"]],
  "04.2.2.0": [["المتواتر", "Mass-transmitted"], ["المشهور", "Well known"], ["الآحاد", "Single-chain"], ["الشاذ", "Irregular"], ["الموضوع", "Fabricated"], ["المدرج", "Interpolated"]],
  "04.2.2.1": [["ابن محيصن", "Ibn Muhaysin"], ["اليزيدي", "al-Yazidi"], ["الحسن البصري", "al-Hasan al-Basri"], ["الأعمش", "al-Amash"]],
  "04.2.3": [["الرواة عن كل قارئ", "Narrators from each reciter"], ["الأسانيد المتصلة", "Connected chains"], ["الإجازة والسند", "Licence and chain"], ["طبقات القراء", "Generations of reciters"]],
  "04.2.4": [["مخارج الحروف", "Points of articulation"], ["الصفات", "Letter attributes"], ["أحكام النون والميم", "Rules of noon and meem"], ["المدود", "Prolongations"], ["الإمالة والتفخيم", "Inclination and heaviness"]],
  "04.2.4.0": [["الجوف", "Oral cavity"], ["الحلق", "Throat"], ["اللسان", "Tongue"], ["الشفتان", "Lips"], ["الخيشوم", "Nasal passage"]],
  "04.2.5": [["التامّ والكافي والحسن", "Complete, sufficient, good pause"], ["الوقف القبيح", "Bad pause"], ["السكت والقطع", "Breathless stop and cut-off"], ["علاماته", "Its marks"]],

  // Branch 3: meaning and rulings
  "04.3.0": [["تعريفهما", "Their definition"], ["الحروف المقطَّعة", "Disjointed letters"], ["الراسخون في العلم", "Those firm in knowledge"], ["التأويل والتفويض", "Interpretation and entrusting"]],
  "04.3.1": [["أنواع النسخ", "Kinds of abrogation"], ["نسخ التلاوة والحكم", "Abrogating wording and ruling"], ["شروطه", "Its conditions"], ["المنسوخات المذكورة", "Cited abrogated verses"]],
  "04.3.1.0": [["نسخ الحكم والتلاوة معًا", "Both ruling and wording"], ["نسخ الحكم دون التلاوة", "Ruling only, wording stays"], ["نسخ التلاوة دون الحكم", "Wording only, ruling stays"]],
  "04.3.2": [["صيغ العموم", "Forms of generality"], ["المخصِّصات المتصلة والمنفصلة", "Attached and separate specifiers"], ["العام المراد به الخصوص", "General meant as specific"]],
  "04.3.2.1": [["المتصلة: الاستثناء والشرط والصفة والغاية", "Attached: exception, condition, attribute, limit"], ["المنفصلة: آية أو سنة أو إجماع", "Separate: verse, Sunnah, consensus"]],
  "04.3.3": [["حمل المطلق على المقيَّد", "Reading absolute by restricted"], ["اتحاد الحكم والسبب", "Same ruling and cause"], ["أمثلته", "Its examples"]],
  "04.3.4": [["أسباب الإجمال", "Causes of ambiguity"], ["المبيَّن بالسنة", "Clarified by the Sunnah"], ["تأخير البيان", "Delaying clarification"]],
  "04.3.5": [["مفردات الغريب", "Rare vocabulary"], ["الوجوه والنظائر", "Polysemes and parallels"], ["المعرَّب في القرآن", "Loanwords in the Qur'an"], ["كتب الغريب", "Books on rare words"]],

  // Branch 4: inimitability and style
  "04.4.0": [["البلاغي", "Rhetorical"], ["الغيبي", "Unseen-related"], ["العلمي", "Scientific"], ["التشريعي", "Legislative"], ["الصرفة وردّها", "Sarfa and its refutation"]],
  "04.4.1": [["المصرَّحة والكامنة", "Explicit and implicit"], ["فوائدها", "Their benefits"], ["أمثلتها القرآنية", "Qur'anic examples"]],
  "04.4.2": [["المقسَم به والمقسَم عليه", "Sworn by and sworn upon"], ["حكمة القسم", "Wisdom of oaths"], ["حذف أداة القسم", "Omitting the oath particle"]],
  "04.4.3": [["أنواعه", "Its kinds"], ["تكراره وحكمته", "Repetition and its wisdom"], ["فوائده", "Its benefits"], ["الفرق عن الأساطير", "Difference from legends"]],
  "04.4.4": [["أساليب الحِجاج", "Styles of argument"], ["مناسبة الآيات", "Link between verses"], ["مناسبة السور", "Link between surahs"], ["فواصل الآي", "Verse endings"]],
  "04.4.5": [["أنواعها العشرة", "Its ten kinds"], ["الحروف المقطَّعة", "Disjointed letters"], ["الافتتاح بالحمد والنداء", "Opening with praise and address"]],
  "04.4.5.0": [["الثناء", "Praise"], ["حروف التهجي", "Spelled letters"], ["النداء", "Address"], ["الجمل الخبرية", "Declarative sentences"], ["القسم", "Oath"], ["الشرط", "Condition"], ["الأمر", "Command"], ["الاستفهام", "Question"], ["الدعاء", "Supplication"], ["التعليل", "Giving a reason"]],

  // Branch 5: exegesis
  "04.5.0": [["العلوم المطلوبة", "Required sciences"], ["صحة المعتقد", "Sound belief"], ["التجرّد عن الهوى", "Freedom from desire"], ["آدابه في الترجيح", "Its etiquette in preferring"]],
  "04.5.0.0": [["اللغة", "Language"], ["النحو", "Grammar"], ["التصريف", "Morphology"], ["الاشتقاق", "Derivation"], ["المعاني والبيان والبديع", "Rhetoric: meanings, style, ornament"], ["القراءات", "Readings"], ["أصول الدين", "Foundations of belief"], ["أصول الفقه", "Legal theory"], ["أسباب النزول والقصص", "Causes of revelation and stories"], ["الناسخ والمنسوخ", "Abrogating and abrogated"], ["الفقه", "Jurisprudence"], ["علم الموهبة", "Bestowed knowledge"]],
  "04.5.1": [["القرآن بالقرآن", "Qur'an by the Qur'an"], ["بالسنة", "By the Sunnah"], ["بأقوال الصحابة", "By Companions' sayings"], ["بالتابعين", "By the Followers"], ["أشهر كتبه", "Best-known books"]],
  "04.5.2": [["المحمود والمذموم", "Praised and blamed"], ["شروط جوازه", "Conditions of permissibility"], ["التفسير الإشاري", "Allusive exegesis"], ["الاتجاهات الحديثة", "Modern trends"]],
  "04.5.3": [["أقسامها", "Its categories"], ["موقف العلماء منها", "Scholars' stance"], ["مصادرها", "Its sources"], ["أثرها في كتب التفسير", "Its effect on exegesis books"]],
  "04.5.3.0": [["ما وافق شرعنا", "Agrees with our law"], ["ما خالفه", "Contradicts it"], ["المسكوت عنه", "Left unaddressed"]],
  "04.5.4": [["مفسرو الصحابة", "Companion exegetes"], ["التابعون", "The Followers"], ["مدارس مكة والمدينة والعراق", "Schools of Mecca, Madinah, Iraq"], ["طبقات المتأخرين", "Later generations"]],
  "04.5.4.0": [["أبو بكر", "Abu Bakr"], ["عمر", "Umar"], ["عثمان", "Uthman"], ["علي", "Ali"], ["ابن مسعود", "Ibn Masud"], ["ابن عباس", "Ibn Abbas"], ["أبي بن كعب", "Ubayy ibn Kab"], ["زيد بن ثابت", "Zayd ibn Thabit"], ["أبو موسى الأشعري", "Abu Musa al-Ashari"], ["عبد الله بن الزبير", "Abdullah ibn al-Zubayr"]],
  "04.5.4.2": [["مكة: ابن عباس", "Mecca: Ibn Abbas"], ["المدينة: أبي بن كعب", "Madinah: Ubayy ibn Kab"], ["العراق: ابن مسعود", "Iraq: Ibn Masud"]],
};

/**
 * Curated Sarf presets, grouped by verb form (باب).
 * Each word carries enough pre-loaded morphological data so the UI can render
 * results instantly without an API round-trip for these common examples.
 *
 * No conjugation table is held here; the panel still calls the API for that,
 * but root/wazn/meaning are shown immediately from this data.
 */

export const SARF_PRESETS = [
  {
    id: 'form1-a-u',
    category: 'Form I: فَعَلَ / يَفْعُلُ',
    labelEn: 'Bāb Nasara',
    color: 'purple',
    words: [
      { arabic: 'كَتَبَ',  meaning: 'to write',   root: 'كتب', wazn: 'فَعَلَ', verb_class: 'Form I' },
      { arabic: 'نَصَرَ',  meaning: 'to help',    root: 'نصر', wazn: 'فَعَلَ', verb_class: 'Form I' },
      { arabic: 'ضَرَبَ',  meaning: 'to strike',  root: 'ضرب', wazn: 'فَعَلَ', verb_class: 'Form I' },
      { arabic: 'جَلَسَ',  meaning: 'to sit',     root: 'جلس', wazn: 'فَعَلَ', verb_class: 'Form I' },
      { arabic: 'خَرَجَ',  meaning: 'to exit',    root: 'خرج', wazn: 'فَعَلَ', verb_class: 'Form I' },
      { arabic: 'دَخَلَ',  meaning: 'to enter',   root: 'دخل', wazn: 'فَعَلَ', verb_class: 'Form I' },
    ],
  },
  {
    id: 'form1-a-a',
    category: 'Form I: فَعَلَ / يَفْعَلُ',
    labelEn: 'Bāb Fataha',
    color: 'blue',
    words: [
      { arabic: 'فَتَحَ',  meaning: 'to open',    root: 'فتح', wazn: 'فَعَلَ', verb_class: 'Form I' },
      { arabic: 'ذَهَبَ',  meaning: 'to go',      root: 'ذهب', wazn: 'فَعَلَ', verb_class: 'Form I' },
      { arabic: 'سَأَلَ',  meaning: 'to ask',     root: 'سأل', wazn: 'فَعَلَ', verb_class: 'Form I' },
      { arabic: 'قَرَأَ',  meaning: 'to read',    root: 'قرأ', wazn: 'فَعَلَ', verb_class: 'Form I' },
    ],
  },
  {
    id: 'form1-a-i',
    category: 'Form I: فَعِلَ / يَفْعَلُ',
    labelEn: 'Bāb ʿAlima',
    color: 'teal',
    words: [
      { arabic: 'عَلِمَ',  meaning: 'to know',    root: 'علم', wazn: 'فَعِلَ', verb_class: 'Form I' },
      { arabic: 'سَمِعَ',  meaning: 'to hear',    root: 'سمع', wazn: 'فَعِلَ', verb_class: 'Form I' },
      { arabic: 'شَرِبَ',  meaning: 'to drink',   root: 'شرب', wazn: 'فَعِلَ', verb_class: 'Form I' },
      { arabic: 'حَمِدَ',  meaning: 'to praise',  root: 'حمد', wazn: 'فَعِلَ', verb_class: 'Form I' },
    ],
  },
  {
    id: 'form2',
    category: 'Form II: فَعَّلَ',
    labelEn: 'Taḍʿīf',
    color: 'amber',
    words: [
      { arabic: 'عَلَّمَ',  meaning: 'to teach',      root: 'علم', wazn: 'فَعَّلَ', verb_class: 'Form II' },
      { arabic: 'قَدَّمَ',  meaning: 'to present',    root: 'قدم', wazn: 'فَعَّلَ', verb_class: 'Form II' },
      { arabic: 'نَزَّلَ',  meaning: 'to send down',  root: 'نزل', wazn: 'فَعَّلَ', verb_class: 'Form II' },
      { arabic: 'كَرَّمَ',  meaning: 'to honour',     root: 'كرم', wazn: 'فَعَّلَ', verb_class: 'Form II' },
    ],
  },
  {
    id: 'form3',
    category: 'Form III: فَاعَلَ',
    labelEn: 'Mufāʿalah',
    color: 'orange',
    words: [
      { arabic: 'قَاتَلَ',  meaning: 'to fight',     root: 'قتل', wazn: 'فَاعَلَ', verb_class: 'Form III' },
      { arabic: 'سَافَرَ',  meaning: 'to travel',    root: 'سفر', wazn: 'فَاعَلَ', verb_class: 'Form III' },
      { arabic: 'جَاهَدَ',  meaning: 'to strive',    root: 'جهد', wazn: 'فَاعَلَ', verb_class: 'Form III' },
    ],
  },
  {
    id: 'form4',
    category: 'Form IV: أَفْعَلَ',
    labelEn: 'Ifʿāl',
    color: 'rose',
    words: [
      { arabic: 'أَكْرَمَ',  meaning: 'to honour',    root: 'كرم', wazn: 'أَفْعَلَ', verb_class: 'Form IV' },
      { arabic: 'أَرْسَلَ',  meaning: 'to send',      root: 'رسل', wazn: 'أَفْعَلَ', verb_class: 'Form IV' },
      { arabic: 'أَسْلَمَ',  meaning: 'to submit',    root: 'سلم', wazn: 'أَفْعَلَ', verb_class: 'Form IV' },
      { arabic: 'أَنْزَلَ',  meaning: 'to reveal',    root: 'نزل', wazn: 'أَفْعَلَ', verb_class: 'Form IV' },
    ],
  },
  {
    id: 'form10',
    category: 'Form X: اسْتَفْعَلَ',
    labelEn: 'Istifsāl',
    color: 'green',
    words: [
      { arabic: 'اسْتَغْفَرَ', meaning: 'to seek forgiveness', root: 'غفر', wazn: 'اسْتَفْعَلَ', verb_class: 'Form X' },
      { arabic: 'اسْتَعْمَلَ', meaning: 'to use',              root: 'عمل', wazn: 'اسْتَفْعَلَ', verb_class: 'Form X' },
      { arabic: 'اسْتَقْبَلَ', meaning: 'to receive/welcome',  root: 'قبل', wazn: 'اسْتَفْعَلَ', verb_class: 'Form X' },
    ],
  },
]

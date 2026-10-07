import { describe, expect, it } from 'vitest'

import { buildIraabExportText } from './iraabExport'

describe('buildIraabExportText', () => {
  it('copies the case and sign in Arabic', () => {
    const text = buildIraabExportText({
      sentence: 'ذهب الطالب',
      words: [
        { word: 'الطالب', role: 'فاعل', case: "raf'", sign: 'ضمة', root: 'طلب' },
        { word: 'الدرس', role: 'مفعول به', case: 'nasb', sign: 'فتحة' },
        { word: 'لم', case: 'mabni (سكون على اللام)' },
      ],
    })
    expect(text).toContain('Case: مرفوع (ضمة)')
    expect(text).toContain('Case: منصوب (فتحة)')
    expect(text).toContain('Case: مبني (سكون على اللام)')
    expect(text).not.toMatch(/raf'|nasb|mabni/)
  })

  it('copies the joins the diagram draws: the khabar, the hidden doer, the silah and what a jar-majroor hangs on', () => {
    // إنّ اللهَ حرّمَ من الرضاعةِ ما حرّمَ, the tree as the server returns it
    const leaf = (word, role, parts = []) => ({ word, role, parts, children: [] })
    const verb = (word) => leaf(word, 'فعل', [{ role: 'فعل' }, { role: 'فاعل', detail: 'ضمير مستتر تقديره هو' }])
    const unit = (label, role, children, detail = null) => ({ word: null, label, role, detail, children })
    const tree = unit('جملة اسمية', null, [
      leaf(0, 'حرف ناسخ مشبه بالفعل'),
      leaf(1, 'اسم إن'),
      unit('جملة فعلية', 'خبر إن', [
        verb(2),
        unit('متعلق بـحَرَّمَ', null, [leaf(3, 'حرف جر'), leaf(4, 'مجرور')]),
        unit('اسم موصول وصلته', 'مفعول به', [leaf(5, 'اسم موصول'), unit('جملة فعلية', 'صلة', [verb(6)])]),
      ], 'في محل رفع'),
    ])
    const words = ['إِنَّ', 'اللَّهَ', 'حَرَّمَ', 'مِنَ', 'الرَّضَاعَةِ', 'مَا', 'حَرَّمَ']
    const text = buildIraabExportText({ sentence: words.join(' '), words: [], tree: { words, tree } })
    expect(text).toContain('  حَرَّمَ مِنَ الرَّضَاعَةِ مَا حَرَّمَ = جملة فعلية: خبر إن (في محل رفع)')
    expect(text).toContain('    حَرَّمَ = فعل + فاعل (ضمير مستتر تقديره هو)')
    expect(text).toContain('    مِنَ الرَّضَاعَةِ = متعلق بـحَرَّمَ')
    expect(text).toContain('    مَا حَرَّمَ = اسم موصول وصلته: مفعول به')
    expect(text).toContain('      حَرَّمَ = جملة فعلية: صلة')
  })

  it('leaves a word no rule named as an open mark, not a guess', () => {
    const tree = { word: null, label: 'جملة فعلية', children: [{ word: 0, role: null, children: [] }] }
    const text = buildIraabExportText({ sentence: 'أمس', words: [], tree: { words: ['أمس'], tree } })
    expect(text).toContain('  أمس = ؟')
  })

  it('prints the pieces of one written word joined, as it is written', () => {
    const tree = { label: 'جملة', children: [
      { word: 0, role: 'حرف عطف', children: [] }, { word: 1, role: 'فعل', children: [] }, { word: 2, role: 'فاعل', children: [] }] }
    const text = buildIraabExportText({ sentence: '', words: [], tree: { words: ['فَ', 'قَامَ', 'زَيْدٌ'], written: [0, 0, 1], tree } })
    expect(text).toContain('فَقَامَ زَيْدٌ = جملة')
  })
})

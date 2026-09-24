import { describe, expect, it } from 'vitest'

import { buildIraabExportText } from './iraabExport'

describe('buildIraabExportText', () => {
  it('copies the case and sign in Arabic, from either engine', () => {
    const text = buildIraabExportText({
      sentence: 'ذهب الطالب',
      words: [
        { word: 'الطالب', role: 'فاعل', case: "raf'", sign: 'ضمة', root: 'طلب' },
        { word: 'الدرس', role: 'مفعول به', case: 'nasb', sign: 'fatha' },
        { word: 'لم', case: 'mabni (سكون على اللام)' },
      ],
    })
    expect(text).toContain('Case: مرفوع (ضمة)')
    expect(text).toContain('Case: منصوب (فتحة)')
    expect(text).toContain('Case: مبني (سكون على اللام)')
    expect(text).not.toMatch(/raf'|nasb|mabni/)
  })
})

/**
 * Why two look-alike verses differ: what the differing words mean and what
 * role each plays, then what each verse is about. The wording is the symptom;
 * this is the reason, and a reason is what makes a pair stick.
 *
 * Everything here is the Qur'an tab's own data: the word-by-word grammar
 * (quranAyahQuery), the reader's chosen translation (useTranslation) and a
 * tafsir, the one the reader last picked or similar.json's short default.
 * Shut, it fetches nothing: the drill never pays for it.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getAyahEditions, getQuranEditions, quranAyahQuery } from '../../api'
import { posLabel } from '../../lib/nahw/grammarTerms'
import { posColor } from '../../lib/nahw/roleColors'
import { glossAt, whereOf } from '../../lib/similar/similar'
import { parsePlace } from '../../lib/similar/similarPlace'
import { useRemembered } from '../../lib/store/useRemembered'
import { useTranslation } from '../../lib/similar/useTranslation'
import copy from '../../config/similar.json'

import ArabicText from '../ui/text/ArabicText'
import Disclosure from '../ui/overlays/Disclosure'
import ShowRest from '../ui/buttons/ShowRest'
import { Skeleton } from '../ui/feedback/Skeleton'

/** One verse's grammar, translation line and tafsir passage, asked for once it is wanted. */
function useContext(verse, tafsir, on) {
  const { surah, ayah } = parsePlace(verse.key)
  const grammar = useQuery({ ...quranAyahQuery(surah, ayah), enabled: on })
  const translation = useTranslation(on ? surah : 0)
  const passage = useQuery({
    queryKey: ['ayah-editions', surah, ayah, tafsir],
    queryFn: () => getAyahEditions(surah, ayah, [tafsir]),
    enabled: on && Boolean(tafsir),
    retry: false,
  })
  return {
    words: grammar.data?.words,
    pending: grammar.isPending || passage.isPending,
    line: translation.textFor(ayah),
    tafsir: passage.data?.passages?.[0]?.text ?? '',
  }
}

/** The differing words of one side: their English, and each word's role. */
function Words({ verse, span, grammar, color }) {
  const gloss = glossAt(verse.text.split(/\s+/).filter(Boolean), grammar, span)
  return (
    <div className="space-y-1">
      <p className="type-label font-semibold" style={{ color }}>{whereOf(verse.key)}</p>
      {gloss === null && grammar && <p className="type-small text-[var(--text-faint)]">{copy['why-no-grammar']}</p>}
      {gloss?.meaning && <p className="type-ui text-[var(--text)]">{gloss.meaning}</p>}
      {gloss?.roles.map((w, i) => (
        <p key={i} className="type-small text-[var(--text-dim)] flex flex-wrap items-baseline gap-x-2">
          <ArabicText size="sm" className="arabic-inline text-[var(--text)]">{w.arabic}</ArabicText>
          {w.pos && <span style={{ color: posColor(w.pos) }}>{posLabel(w.pos)}</span>}
          <span>{w.grammar.join(' · ')}</span>
        </p>
      ))}
    </div>
  )
}

/** One verse in the reader's English, then the tafsir's passage, folded. */
function Context({ verse, line, tafsir, pending, color, accent }) {
  return (
    <div className="space-y-1 min-w-0">
      <p className="type-label font-semibold" style={{ color }}>{whereOf(verse.key)}</p>
      {pending && <Skeleton className="h-10 w-full" />}
      {line && <p className="type-ui text-[var(--text)]">{line}</p>}
      {!pending && (tafsir
        ? <ShowRest lines={4} accent={accent} more={copy['show-all']} less={copy['show-less']}><p className="type-small leading-relaxed text-[var(--text-dim)] whitespace-pre-line">{tafsir}</p></ShowRest>
        : <p className="type-small text-[var(--text-faint)]">{copy['why-no-tafsir']}</p>)}
    </div>
  )
}

export default function Why({ mine, partner, colors: [mineColor, twinColor], accent }) {
  const [open, setOpen] = useState(false)
  const { data: books } = useQuery({ queryKey: ['quran-editions', 'tafsir'], queryFn: () => getQuranEditions('tafsir'), enabled: open })
  const [tafsir] = useRemembered('tafsir-edition', books?.map((b) => b.id) ?? null, copy.tafsir)
  const a = useContext(mine, tafsir, open)
  const b = useContext(partner, tafsir, open)
  return (
    <Disclosure label={copy.why} tone="strong" onToggle={setOpen} className="pt-2">
      {open && (
        <div className="space-y-3 pt-2">
          {partner.changes.length > 0 && (
            <>
              <h4 className="eyebrow">{copy['why-words']}</h4>
              {partner.changes.map((change, i) => (
                <div key={i} className="grid grid-cols-2 gap-3">
                  <Words verse={mine} span={change.self} grammar={a.words} color={mineColor} />
                  <Words verse={partner} span={change.other} grammar={b.words} color={twinColor} />
                </div>
              ))}
            </>
          )}
          <h4 className="eyebrow">{copy['why-context']}</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Context verse={mine} {...a} color={mineColor} accent={accent} />
            <Context verse={partner} {...b} color={twinColor} accent={accent} />
          </div>
        </div>
      )}
    </Disclosure>
  )
}

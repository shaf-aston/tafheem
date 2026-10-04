/**
 * What the words between the narrators of a chain mean: how each one says the
 * hadith was received. Laid out as GrammarGlossary lays out the grammar terms;
 * every word and meaning comes from hadith.json chain.terms, and the two ways
 * the chain drawing colours (heard, did not say how) wear their colour here.
 */
import HADITH from '../../hadith.json'
import { themeVariable } from '../../theme'

import ArabicText from './ArabicText'

export default function ChainWords() {
  return (
    <div className="grid gap-y-5 sm:grid-cols-[auto_1fr]">
      {HADITH.chain.terms.groups.map(({ way, title, name, terms }) => (
        <section key={way} className="col-span-full grid grid-cols-subgrid">
          <h3 className="col-span-full flex items-center gap-2 type-tiny uppercase tracking-[0.14em] text-[var(--text-faint)] mb-2">
            {themeVariable(`--hadith-${way}`) && <span aria-hidden="true" className="w-1.5 h-1.5 rounded-full" style={{ background: `var(--hadith-${way})` }} />}
            {title}
            {name && <ArabicText size="tiny" className="normal-case tracking-normal">{name}</ArabicText>}
          </h3>
          <dl className="col-span-full grid grid-cols-subgrid gap-x-4 gap-y-2 items-baseline m-0">
            {terms.map(({ arabic, meaning }) => (
              <div key={arabic} className="contents">
                <dt>
                  <ArabicText size="sm" className="whitespace-nowrap">{arabic}</ArabicText>
                </dt>
                <dd className="type-small text-[var(--text-dim)] leading-relaxed m-0">{meaning}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </div>
  )
}

/**
 * What the grammar terms mean, shut by default, at the foot of the Nahw page.
 *
 * The tags on the page say مبتدأ and منصوب and no more. This is the one place
 * the English is: a reader who needs it opens it once, a reader who does not
 * never sees a paragraph under every tag. Every term comes from grammar.json.
 */
import { GLOSSARY } from '../../lib/grammarTerms'

import ArabicText from './ArabicText'
import Disclosure from './Disclosure'

export default function GrammarGlossary() {
  return (
    <Disclosure label="What the terms mean">
      {/* One grid shared by every section (subgrid), so every meaning on the
          list starts on the same edge however long the term. */}
      <div className="grid gap-y-5 sm:grid-cols-[auto_1fr]">
        {GLOSSARY.map(({ title, terms }) => (
          <section key={title} className="col-span-full grid grid-cols-subgrid">
            <h3 className="col-span-full type-label text-[var(--text-faint)] mb-2">{title}</h3>
            <dl className="col-span-full grid grid-cols-subgrid gap-x-4 gap-y-2 items-baseline">
              {terms.map(({ arabic, meaning }) => (
                <div key={arabic} className="contents">
                  <dt className="whitespace-nowrap">
                    <ArabicText size="sm">{arabic}</ArabicText>
                  </dt>
                  <dd className="type-small text-[var(--text-dim)] leading-relaxed">{meaning}</dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>
    </Disclosure>
  )
}

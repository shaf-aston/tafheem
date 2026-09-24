/**
 * What the grammar terms mean, shut by default, at the foot of the Nahw page.
 *
 * The tags on the page say مبتدأ and منصوب and no more. This is the one place
 * the English is: a reader who needs it opens it once, a reader who does not
 * never sees a paragraph under every tag. Every term comes from grammar.json.
 */
import { GLOSSARY, ROLES } from '../../lib/grammarTerms'
import { roleVar } from '../../lib/roleColors'

import ArabicText from './ArabicText'
import Disclosure from './Disclosure'

export default function GrammarGlossary() {
  return (
    <Disclosure label="What the terms mean">
      <dl className="grid gap-x-4 gap-y-2 sm:grid-cols-[auto_1fr] items-baseline">
        {GLOSSARY.map(({ key, arabic, said, meaning }) => (
          /* One fragment per term, laid straight into the two-column grid so
             every meaning starts on the same edge however long the term. */
          <div key={key} className="contents">
            <dt className="flex items-baseline gap-2 whitespace-nowrap">
              {/* The role's own colour, so the glossary reads as the key to
                  the tags above it and not a separate list. A case has no
                  colour of its own and stays in the ordinary text colour. */}
              <ArabicText size="sm" style={{ color: roleVar(key in ROLES ? key : null) }}>
                {arabic}
              </ArabicText>
              <span className="type-small text-[var(--text-faint)]">{said}</span>
            </dt>
            <dd className="type-small text-[var(--text-dim)] leading-relaxed">{meaning}</dd>
          </div>
        ))}
      </dl>
    </Disclosure>
  )
}

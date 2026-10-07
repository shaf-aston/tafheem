/**
 * A practice sentence made only of words this learner has learnt.
 *
 * The AI writes it; a plain program on the server checks every word and throws
 * away any sentence with a word outside the learnt list. Asked for on a press,
 * never on page load, so nobody pays for a sentence they did not want.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { getCheckedSentence } from '../api'
import { smartError } from '../lib/apiError'

import ArabicText from './ui/ArabicText'
import SmallButton from './ui/SmallButton'

export default function PracticeSentence({ say }) {
  const [meaning, setMeaning] = useState(false)
  const make = useMutation({ mutationFn: getCheckedSentence, onMutate: () => setMeaning(false) })
  const sentence = make.data

  return (
    <section className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-4 py-3 space-y-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h3 className="type-small uppercase tracking-wide text-[var(--text-faint)]">{say('Practice sentence')}</h3>
        <SmallButton onClick={() => make.mutate()} disabled={make.isPending}>
          {make.isPending ? say('Writing…') : sentence ? say('Another') : say('Make one')}
        </SmallButton>
      </div>

      {make.isError && (
        <p className="type-small text-[var(--text-dim)]">{say(smartError(make.error))}</p>
      )}

      {sentence && !make.isPending && (
        <div className="space-y-2">
          <ArabicText size="lg">{sentence.ar}</ArabicText>
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <button type="button" onClick={() => setMeaning(!meaning)}
              className="type-small text-[var(--text-dim)] underline underline-offset-2">
              {meaning ? say('Hide meaning') : say('Show meaning')}
            </button>
            <span className="type-tiny text-[var(--text-faint)]">{say('written by AI, every word checked')}</span>
          </div>
          {meaning && <p className="type-body text-[var(--text-dim)]">{sentence.en}</p>}
        </div>
      )}
    </section>
  )
}

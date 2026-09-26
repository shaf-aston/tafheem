/**
 * One lesson, read top to bottom in the order the plan fixes: situation and
 * goal, phrases, dialogue, book vs natural, culture, then Practise. Arabic
 * always goes through ArabicText (lang, dir, the app's sizes); everything else
 * is left to right.
 */
import { useState } from 'react'

import ArabicText from '../components/ui/ArabicText'
import PrimaryButton from '../components/ui/PrimaryButton'
import Segmented from '../components/ui/Segmented'
import { Back, COPY, Gloss, Section } from './parts'

export default function LessonPage({ lesson, accent, onBack, onPractise }) {
  const [gloss, setGloss] = useState(true)

  return (
    <div className="space-y-4">
      <Back onClick={onBack} />
      <Section title={COPY.situation}>
        <p>{lesson.situation}</p>
        <p className="type-small text-[var(--text-dim)]"><b>{COPY.goal}:</b> {lesson.goal}</p>
      </Section>

      <Section title={COPY.phrases}>
        <ul className="divide-y divide-[var(--border)]">
          {lesson.phrases.map((p, i) => (
            <li key={i} className="py-2 space-y-1">
              <ArabicText as="p">{p.ar}</ArabicText>
              <Gloss translit={p.translit} en={p.en} />
              {p.use && <p className="type-tiny text-[var(--text-faint)]">{p.use}</p>}
              {p.reply && (
                <div className="ms-4 ps-3 border-s-2 border-[var(--c)]">
                  <span className="type-tiny text-[var(--text-faint)]">{COPY.reply}</span>
                  <ArabicText as="p" size="sm">{p.reply.ar}</ArabicText>
                  <Gloss translit={p.reply.translit} en={p.reply.en} />
                </div>
              )}
            </li>
          ))}
        </ul>
      </Section>

      <Section title={COPY.dialogue}>
        <Segmented
          label={COPY['show-gloss']}
          captioned
          accent={accent}
          value={gloss}
          onChange={setGloss}
          options={[{ id: true, label: COPY['gloss-on'] }, { id: false, label: COPY['gloss-off'] }]}
        />
        <ol className="space-y-2">
          {lesson.dialogue.map((line, i) => (
            <li key={i}>
              <span className="type-tiny font-semibold text-[var(--c)]">{line.speaker}</span>
              <ArabicText as="p">{line.ar}</ArabicText>
              {gloss && <Gloss translit={line.translit} en={line.en} />}
            </li>
          ))}
        </ol>
      </Section>

      <Section title={COPY['de-book']}>
        <ul className="divide-y divide-[var(--border)]">
          {lesson.de_book.map((d, i) => (
            <li key={i} className="py-2 grid gap-1 sm:grid-cols-2">
              <div><span className="type-tiny text-[var(--text-faint)]">{COPY.book}</span><ArabicText as="p" size="sm" className="line-through decoration-[var(--text-faint)]">{d.book}</ArabicText></div>
              <div><span className="type-tiny text-[var(--text-faint)]">{COPY.natural}</span><ArabicText as="p" size="sm">{d.natural}</ArabicText></div>
              <p className="sm:col-span-2 type-small text-[var(--text-dim)]">{d.why}</p>
            </li>
          ))}
        </ul>
      </Section>

      {lesson.grammar && <Section title={COPY.grammar}><p className="type-small">{lesson.grammar}</p></Section>}
      <Section title={COPY.culture}><p className="type-small">{lesson.culture}</p></Section>

      <PrimaryButton accent={accent} disabled={!onPractise} onClick={onPractise}>{COPY.practise}</PrimaryButton>
    </div>
  )
}

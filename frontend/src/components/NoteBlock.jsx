/**
 * One piece of a topic's notes, drawn the way the page has it.
 *
 * In reading mode every marked piece shows as plain text. In test mode a piece
 * whose role is switched off is a dashed blank, pressed to reveal, and a table
 * that names the column it asks hides that column. Nothing here changes the
 * note: `hidden` and `revealed` decide what shows, the text stays the text.
 */
import { parseMarked, stripMarks } from '../lib/notes'
import { notePageUrl } from '../api'

import ArabicText from './ui/ArabicText'

const pieceKey = (blockId, field, at) => `${blockId}:${field}:${at}`

function Blank({ text, what, onReveal }) {
  return (
    <button
      type="button"
      onClick={onReveal}
      aria-label={`Hidden ${what}, press to show`}
      className="inline-block min-w-[4ch] px-1 mx-0.5 rounded border border-dashed border-[var(--c)]
        text-transparent select-none bg-[color-mix(in_srgb,var(--c)_8%,transparent)] hover:bg-[color-mix(in_srgb,var(--c)_16%,transparent)]
        transition-colors align-baseline"
    >
      {/* The hidden words keep their width, so revealing one does not reflow the line. */}
      {text}
    </button>
  )
}

/** A string with its marked pieces shown, or blanked where the test hides them. */
function Marked({ text, field, block, hidden, revealed, onReveal }) {
  return parseMarked(text).map((part, at) => {
    const key = pieceKey(block.id, field, at)
    if (part.role && hidden.has(part.role) && !revealed.has(key)) {
      return <Blank key={key} text={part.text} what={part.role} onReveal={() => onReveal(key)} />
    }
    return part.role
      ? <span key={key} className={hidden.has(part.role) ? 'font-semibold text-[var(--c)]' : undefined}>{part.text}</span>
      : <span key={key}>{part.text}</span>
  })
}

// Most lines are Arabic, but the teacher writes some list lines and headings in English.
const isArabic = (text) => /[؀-ۿ]/.test(text ?? '')

// type-body, not type-small: here the English is what is being read, not a
// label on something else, and the scale's own note says body is that size.
function English({ children }) {
  return <p className="type-body text-[var(--text-dim)] leading-relaxed">{children}</p>
}

function PageLink({ topicId, page }) {
  return (
    <a
      href={notePageUrl(topicId, page)}
      target="_blank"
      rel="noreferrer noopener"
      className="type-micro text-[var(--text-faint)] hover:text-[var(--text-dim)] underline-offset-2 hover:underline"
    >
      page {page + 1}
    </a>
  )
}

export default function NoteBlock({ topicId, block, testing, hidden, revealed, onReveal, english }) {
  const shown = testing ? hidden : new Set()
  const marked = (field) => block[field] && (
    <Marked text={block[field]} field={field} block={block} hidden={shown} revealed={revealed} onReveal={onReveal} />
  )
  const cellHidden = (col, key) => testing && col === block.answer_col && !revealed.has(key)

  const body = {
    heading: block.ar ? (
      <div className="space-y-1">
        <ArabicText as="h3" size="lg" className="font-semibold">{marked('ar')}</ArabicText>
        {english && block.en && <English>{marked('en')}</English>}
      </div>
    ) : (
      <h3 className="text-lg font-semibold">{marked('en')}</h3>
    ),
    rule: (
      <div className="space-y-1.5">
        {block.ar && <ArabicText as="p" size="base" className="leading-loose">{marked('ar')}</ArabicText>}
        {english && block.en && <English>{marked('en')}</English>}
      </div>
    ),
    list: (
      <div className="space-y-1.5">
        {block.ar && <ArabicText as="p">{marked('ar')}</ArabicText>}
        <ol className="list-decimal ps-6 space-y-1">
          {(block.items ?? []).map((line, i) => {
            const text = <Marked text={line} field={`items.${i}`} block={block} hidden={shown} revealed={revealed} onReveal={onReveal} />
            return isArabic(line)
              ? <ArabicText as="li" key={i} className="leading-loose">{text}</ArabicText>
              : <li key={i} className="type-body">{text}</li>
          })}
        </ol>
        {english && block.en && <English>{marked('en')}</English>}
      </div>
    ),
    example: (
      <div className="space-y-1.5">
        <ArabicText as="p" size="lg">{marked('ar')}</ArabicText>
        {english && block.en && <English>{marked('en')}</English>}
        {block.labels?.length > 0 && (
          <dl className="flex flex-wrap gap-x-4 gap-y-1" dir="rtl">
            {block.labels.map((label, i) => {
              const key = pieceKey(block.id, `labels.${i}`, 0)
              const blank = testing && hidden.has('label') && !revealed.has(key)
              return (
                <div key={key} className="flex items-baseline gap-1.5">
                  <ArabicText as="dt">{label.word}</ArabicText>
                  <span aria-hidden="true" className="text-[var(--text-faint)]">·</span>
                  <ArabicText as="dd" className="text-[var(--c)]">
                    {blank ? <Blank text={label.label} what={`label for ${label.word}`} onReveal={() => onReveal(key)} /> : label.label}
                  </ArabicText>
                </div>
              )
            })}
          </dl>
        )}
      </div>
    ),
    table: (
      <figure className="space-y-2">
        {block.caption && <ArabicText as="figcaption" className="font-semibold">{stripMarks(block.caption)}</ArabicText>}
        {english && block.caption_en && <English>{stripMarks(block.caption_en)}</English>}
        <div className="overflow-x-auto">
          <table dir="rtl" className="w-full border-collapse text-start">
            <thead>
              <tr>
                {(block.columns ?? []).map((name, c) => (
                  <th key={c} scope="col" className="border border-[var(--border)] px-3 py-1.5 bg-[var(--surface-hi)]">
                    <ArabicText>{stripMarks(name)}</ArabicText>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(block.rows ?? []).map((row, r) => (
                <tr key={r}>
                  {row.map((cell, c) => {
                    const key = pieceKey(block.id, `rows.${r}.${c}`, 'cell')
                    return (
                      <td key={c} className="border border-[var(--border)] px-3 py-1.5 align-top">
                        <ArabicText className="leading-loose">
                          {cellHidden(c, key)
                            ? <Blank text={stripMarks(cell)} what={`${block.columns?.[c] ?? 'cell'}, row ${r + 1}`} onReveal={() => onReveal(key)} />
                            : <Marked text={cell} field={`rows.${r}.${c}`} block={block} hidden={shown} revealed={revealed} onReveal={onReveal} />}
                        </ArabicText>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {block.note_ar && <ArabicText as="p" size="sm" className="text-[var(--text-dim)]">{stripMarks(block.note_ar)}</ArabicText>}
        {english && block.note_en && <English>{stripMarks(block.note_en)}</English>}
      </figure>
    ),
    picture: (
      <div className="space-y-1.5">
        {block.caption && <ArabicText as="p">{stripMarks(block.caption)}</ArabicText>}
        {block.caption_en && <English>{stripMarks(block.caption_en)}</English>}
        <a href={notePageUrl(topicId, block.page)} target="_blank" rel="noreferrer noopener" className="block">
          <img
            src={notePageUrl(topicId, block.page)}
            alt={stripMarks(block.caption_en || block.caption) || `Page ${block.page + 1} of the notes`}
            loading="lazy"
            className="max-w-full rounded-[var(--radius-md)] border border-[var(--border)]"
          />
        </a>
      </div>
    ),
  }[block.kind]

  return (
    <section className="space-y-1" aria-label={block.kind}>
      {body}
      <div className="flex justify-end"><PageLink topicId={topicId} page={block.page} /></div>
    </section>
  )
}

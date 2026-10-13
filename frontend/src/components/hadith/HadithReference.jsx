/**
 * Where a hadith stands, as sunnah.com prints it under one: the collection and number (linked to
 * its page there) and its book with its place in it. Small and faint, a footnote under the words.
 * A place the data does not hold (`inBook` 0, a build from before it was kept) leaves the book alone.
 */
export default function HadithReference({ name, number, part = '', book, inBook = 0, cite }) {
  const rows = [
    ['Reference', `${name} ${number}${part}`, cite],
    book > 0 && ['In-book reference', `Book ${book}${inBook ? `, Hadith ${inBook}` : ''}`],
  ].filter(Boolean)
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-3 m-0 mt-3 type-tiny text-[var(--text-faint)]">
      {rows.map(([label, value, href]) => (
        <div key={label} className="contents">
          <dt>{label}</dt>
          <dd className="m-0 tabular-nums">
            {href
              ? <a href={href} target="_blank" rel="noreferrer" className="underline decoration-dotted underline-offset-2 hover:text-[var(--text-dim)]">{value}</a>
              : value}
          </dd>
        </div>
      ))}
    </dl>
  )
}

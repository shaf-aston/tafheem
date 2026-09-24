/** Sarf, the root, the pattern, and the full conjugation of a single word. */
import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { analyzeMorphology, analyzeMeaning, conjugateForm } from '../api'
import { errorMessage } from '../lib/apiError'
import { useArrival, useHeld } from '../lib/useArrival'
import { useSlowPending } from '../lib/useSlowPending'

import ArabicText from './ui/ArabicText'
import ErrorAlert from './ui/ErrorAlert'
import MicButton from './ui/MicButton'
import PresetsDrawer from './ui/PresetsDrawer'
import RetryButton from './ui/RetryButton'
import RootActions from './ui/RootActions'
import SearchBox from './ui/SearchBox'
import SectionHeader from './ui/SectionHeader'
import ShowRest from './ui/ShowRest'
import SourceBadge from './ui/SourceBadge'
import VerbFormTag from './ui/VerbFormTag'
import { Skeleton, AnalyzerSkeleton } from './ui/Skeleton'
import { verbClass } from '../lib/verbClass'

// The book prints the four active columns together and keeps the passives for
// later, so the first four columns the server sends are what opens by default.
const DEFAULT_COLUMN_COUNT = 4

export default function SarfPanel({ accent, incoming, arrival, onGo, onVisit }) {
  const [word, setWord] = useState(incoming ?? '')
  // Preset data shows instantly; the API fills in the table behind it.
  const [preview, setPreview] = useState(null)
  // Which verb form the table is for. The word alone cannot say which Form I
  // baab a verb takes, so the reader chooses and the table is rebuilt.
  const [form, setForm] = useState('')

  // A word that came back is a place reached, so the trail and the back
  // arrow can carry it, the same as the Dictionary. See lib/journey.js.
  const mutation = useMutation({
    mutationFn: analyzeMorphology,
    onSuccess: (_, { word: asked }) => onVisit?.(asked),
  })
  // A باب switch is its own, much smaller question, so it is its own request; 
  // the word's answer is not thrown away and asked for again to change a table.
  const swap = useMutation({ mutationFn: conjugateForm })
  // The meaning can come from a live AI call, which can take seconds; so it is
  // its own request, fired once the table above is already on screen instead of
  // holding the whole page up for it.
  const meaning = useMutation({ mutationFn: analyzeMeaning })

  // A new word answers everything again, so a swap made for the old word goes
  // with it.
  const clear = () => { mutation.reset(); swap.reset(); meaning.reset() }

  // The word's answer is quick enough that saying "waiting" and unsaying it
  // was a flash rather than news, so the waiting is only announced once it has
  // actually lasted. The button is still refused a second press at once, below.
  const waiting = useSlowPending(mutation.isPending)

  // A word arriving: handed over from another tab, or the back arrow returning
  // to one. App no longer remounts the panel for it, that remount was the
  // screen flash (see lib/useArrival).
  const { arrived, returning } = useArrival(arrival, mutation.isPending)

  // Through a return the last table stays up until the next one lands, so the
  // page keeps its height rather than collapsing for the length of a request.
  const base = useHeld(mutation.data ?? preview, returning)
  // The AI is asked for the meaning, and it answers with a verb class too. That
  // class is a guess and the rules' own answer is not: asked about دعو the AI
  // said "Sahih (Salim)" where the rules say ناقص, and spreading the whole reply
  // put the guess on screen. It may only fill the gap, never overwrite.
  const guessed = meaning.data?.meaning ? meaning.data : null
  const data = base && {
    ...base,
    ...swap.data,
    meaning: guessed?.meaning ?? base.meaning,
    meaning_source: guessed?.meaning_source ?? base.meaning_source,
    verb_class: base.verb_class ?? meaning.data?.verb_class,
  }

  // Fires right after the table lands, not on every باب swap; the word hasn't
  // changed, so asking again would just repeat the same network call.
  const { mutate: fetchMeaning } = meaning
  useEffect(() => {
    if (mutation.data && !mutation.data.meaning) fetchMeaning({ word: mutation.data.word })
  }, [mutation.data, fetchMeaning])

  // The box and the باب follow the word during the render.
  if (arrived && incoming) {
    setWord(incoming)
    setPreview(null)
    setForm('')
  }

  // And it is conjugated, so the journey ends in an answer rather than in a
  // filled-in box. The previous word's swap and meaning go with it.
  const { mutate: analyze, reset: resetWord } = mutation
  const { reset: resetSwap } = swap
  const { reset: resetMeaning } = meaning
  useEffect(() => {
    if (!incoming) return
    resetWord()
    resetSwap()
    resetMeaning()
    analyze({ word: incoming })
  }, [arrival, incoming, analyze, resetWord, resetSwap, resetMeaning])

  const submit = (text, nextForm = form) => {
    const trimmed = (text ?? word).trim()
    if (!trimmed) return
    setWord(trimmed)
    clear()
    mutation.mutate({ word: trimmed, form: nextForm || undefined })
  }

  const chooseForm = (id) => {
    setForm(id)
    // With a root in hand the rules can rebuild the table on their own; without
    // one there is nothing to conjugate from, so the word is analysed again.
    if (data?.root) swap.mutate({ root: data.root, form: id })
    else submit(word, id)
  }

  // A failed baab swap is answered right beside the select that caused it, not
  // at the top of the page; the top alert is left for the word lookup only.
  const retrySwap = () => swap.mutate({ root: data.root, form })

  const pickPreset = (preset) => {
    // The old word's finished table would otherwise stay on screen underneath
    // the new preset's facts, so it goes first.
    clear()
    setWord(preset.arabic)
    setPreview({
      root: preset.root,
      wazn: preset.wazn,
      verb_class: preset.verb_class,
      meaning: preset.meaning,
    })
    mutation.mutate({ word: preset.arabic, form: form || undefined })
  }

  const reset = () => {
    setWord('')
    setPreview(null)
    setForm('')
    clear()
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Sarf"
        arabic="صرف"
        subtitle="Where a word comes from: its three-letter root, its pattern, and how it conjugates."
      />

      <div className="space-y-3">
        {/* The same field as Dictionary, Daleel and the Qur'an tab, down to the
            keycap and the microphone. See ui/SearchBox. */}
        <SearchBox
          id="sarf-input"
          label="Arabic word"
          hint="Enter to analyse, or say it"
          arabic
          placeholder="اكتب كلمة..."
          value={word}
          onChange={(v) => { setWord(v); setPreview(null); setForm(''); clear() }}
          onSubmit={() => submit()}
          onClear={reset}
          busy={waiting}
          accent={accent}
        >
          <MicButton
            onHeard={({ text }) => { setWord(text || ''); setPreview(null); setForm(''); clear() }}
            accent={accent}
            title="Say the word"
          />
        </SearchBox>

        <PresetsDrawer onPick={pickPreset} accent={accent} />
      </div>

      {mutation.isError && (
        <ErrorAlert title="Analysis failed">
          {errorMessage(mutation.error)}
          <RetryButton onClick={() => submit()} />
        </ErrorAlert>
      )}

      {waiting && !base && <AnalyzerSkeleton />}

      {data && (
        <SarfResult
          data={data}
          loading={waiting}
          meaningPending={meaning.isPending}
          swapPending={swap.isPending}
          swapError={swap.isError ? errorMessage(swap.error) : null}
          onRetrySwap={retrySwap}
          accent={accent}
          onForm={chooseForm}
          onGo={onGo}
        />
      )}
    </div>
  )
}

function SarfResult({ data, loading, meaningPending, swapPending, swapError, onRetrySwap, accent, onForm, onGo }) {
  // A card with nothing in it is just white space, so only the facts we have
  // get a card at all. Meaning is fetched separately and can still be on its
  // way even once the rest of this list is settled, so it gets a slot of its
  // own rather than silently popping in later.
  const facts = [
    { label: 'Root (جذر)', value: data.root, arabic: true },
    { label: 'Pattern (وزن)', value: data.wazn, arabic: true },
    { label: 'Verb class', ...verbClass(data.verb_class) },
  ].filter((f) => f.value)

  return (
    <div className="space-y-4">
      {/* The table and the meaning are two different claims: the table is a rule
          applied, the meaning may be a machine's guess. Labelled separately. */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        {data.verb ? <VerbFormTag readings={data.verb.readings} /> : <span />}
        <div className="flex items-center gap-2 flex-wrap">
          <SourceBadge source={data.source} />
          {data.meaning && data.meaning_source?.key !== data.source?.key && (
            <SourceBadge source={data.meaning_source} />
          )}
        </div>
      </div>

      {/* Root first means root on the right, the way the rest of this tab reads. */}
      {(facts.length > 0 || data.meaning || meaningPending) && (
        <div dir="rtl" className="grid gap-3 grid-cols-[repeat(auto-fit,minmax(11rem,1fr))]">
          {facts.map((f, i) => (
            <InfoCard key={f.label} {...f} accent={accent} i={i} />
          ))}
          <MeaningCard
            meaning={data.meaning}
            pending={meaningPending}
            root={data.root}
            onGo={onGo}
            accent={accent}
            i={facts.length}
          />
        </div>
      )}

      {loading && !data.table && (
        <div className="space-y-2">
          <div className="text-[var(--text)] font-medium text-sm">Conjugations (تصريف)</div>
          <Skeleton className="h-48 w-full" />
        </div>
      )}

      {!data.table && data.table_note && <TableNote accent={accent}>{data.table_note}</TableNote>}
      {/* Gardaan draws the form select with no grid when table is null, so a
          word with no recorded باب still lets the reader pick one. */}
      {(data.table || Object.keys(data.form_options ?? {}).length > 0) && (
        <Gardaan
          table={data.table}
          accent={accent}
          form={data.form}
          options={data.form_options}
          onForm={onForm}
          swapPending={swapPending}
          swapError={swapError}
          onRetrySwap={onRetrySwap}
        />
      )}

      {data.notes && (
        <div className="p-3 rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)] text-sm text-[var(--text-dim)]">
          <div className="text-[var(--text-faint)] type-tiny uppercase tracking-wide mb-1">Notes</div>
          {data.notes}
        </div>
      )}
    </div>
  )
}

/**
 * Saying no is an answer too. A weak root or a noun has no gardaan, and this
 * panel gives the reason in full rather than looking like something failed.
 */
function TableNote({ accent, title = 'Why there is no table', children }) {
  return (
    <div
      style={{ '--c': accent }}
      className="p-4 rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
        border-l-4 border-l-[var(--c)] space-y-1"
    >
      <div className="text-[var(--text-faint)] type-tiny uppercase tracking-wide">{title}</div>
      <p className="text-sm leading-relaxed text-[var(--text-dim)]">{children}</p>
    </div>
  )
}

/**
 * The gardaan, laid out the way a madrasah book prints it: the fourteen persons
 * read down the side, each tense reads across. Seeing the pattern repeat is the
 * whole point, so nothing here is allowed to push the grid off the page; it
 * scrolls inside its own box and the person column stays pinned beside it.
 */
function Gardaan({ table, accent, form, options, onForm, swapPending, swapError, onRetrySwap }) {
  // table is null when no source names a باب yet: the select below still
  // lets the reader choose one, it is only the grid that has nothing to show.
  const { columns = [], rows = [], summary = [], notes = [] } = table ?? {}
  const allIds = columns.map((c) => c.id)

  // A pick answers instantly in the UI even though the table itself is still
  // rebuilding on the server; without this the select snaps back to the old
  // form until that swap resolves, which reads as the click having failed.
  const [picked, setPicked] = useState(form ?? '')
  const choose = (id) => { setPicked(id); onForm(id) }

  // A different baab can bring different columns, so the choice starts fresh
  // rather than pointing at columns that are no longer there. Reset while
  // rendering, the same way the input box follows an incoming root above; one
  // idiom for "this state follows that prop", not two.
  const signature = allIds.join('|')
  const [shown, setShown] = useState(() => allIds.slice(0, DEFAULT_COLUMN_COUNT))
  const [known, setKnown] = useState(signature)
  if (signature !== known) {
    setKnown(signature)
    setShown(allIds.slice(0, DEFAULT_COLUMN_COUNT))
  }

  const visible = columns.filter((c) => shown.includes(c.id))
  // Emptying the table entirely helps nobody, so the last column stays on.
  const toggle = (id) => setShown((prev) => (
    prev.includes(id)
      ? (prev.length > 1 ? prev.filter((x) => x !== id) : prev)
      : allIds.filter((x) => prev.includes(x) || x === id)
  ))

  return (
    <div className="space-y-3">
      {summary.length > 0 && <SarfSagheer summary={summary} accent={accent} />}

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <span className="text-[var(--text)] font-medium text-sm">Conjugations (تصريف)</span>
        {options && (
          <div className="flex items-center gap-2">
            {swapPending && (
              <span className="type-small text-[var(--text-faint)]">Rebuilding the table…</span>
            )}
            <select
              aria-label="Verb form"
              value={picked || form || ''}
              onChange={(e) => choose(e.target.value)}
              disabled={swapPending}
              style={{ '--c': accent }}
              className="py-1 px-2.5 rounded-full text-xs max-w-[14rem]
                bg-[var(--surface)] border border-[var(--border)] text-[var(--text-dim)]
                hover:text-[var(--text)] focus:border-[var(--c)] focus:outline-none transition-colors
                disabled:opacity-60 disabled:cursor-wait"
            >
              {/* No form chosen yet (no book records the باب): the control must not
                  read as an answer, so it opens on a blank prompt, never on a form. */}
              {!(picked || form) && <option value="">Choose a باب</option>}
              {Object.entries(options).map(([id, label]) => (
                <option key={id} value={id}>{label}</option>
              ))}
            </select>
            {/* Beside the control that failed, not at the top of the page: the
                word's own answer above is still good, only the swap broke. */}
            {swapError && (
              <span className="flex items-center gap-1.5 type-small text-[var(--danger)]">
                {swapError}
                <RetryButton onClick={onRetrySwap} />
              </span>
            )}
          </div>
        )}
      </div>

      {table && (
        <>
          {/* Six columns at once is too wide for a laptop and unreadable on a phone,
              so the reader turns on only the ones being studied. */}
          <fieldset dir="rtl" className="flex flex-wrap items-center gap-2">
            <legend className="sr-only">Columns to show</legend>
            {columns.map((c) => {
              const on = shown.includes(c.id)
              return (
                <label
                  key={c.id}
                  style={on
                    ? { '--c': accent, color: accent, borderColor: accent, background: `color-mix(in srgb, ${accent} 12%, transparent)` }
                    : { '--c': accent }}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
                    border border-[var(--border)] cursor-pointer transition-colors
                    focus-within:ring-2 focus-within:ring-[var(--c)] ${
                    on ? '' : 'text-[var(--text-faint)] hover:text-[var(--text-dim)]'
                  }`}
                >
                  <input type="checkbox" checked={on} onChange={() => toggle(c.id)} className="sr-only" />
                  {c.label}
                </label>
              )
            })}
          </fieldset>

          {/* Arabic reads right to left, and so does the book's grid: ماضي sits on
              the right and نهي on the left. The direction lives on the scroll box so
              a table too wide for the screen opens at ماضي, not at the passives. */}
          <div
            dir="rtl"
            className={`overflow-x-auto rounded-[var(--radius-md)] border border-[var(--border)] transition-opacity ${
              swapPending ? 'opacity-50' : ''
            }`}
          >
            <table className="w-max min-w-full text-sm border-collapse">
              <thead>
                <tr className="bg-[var(--surface-hi)]">
                  {visible.map((c) => (
                    <th key={c.id} className="px-4 py-2 text-center align-bottom">
                      <div className="text-[var(--text-dim)] text-xs uppercase tracking-wide">{c.label}</div>
                      {c.arabic && (
                        <ArabicText size="sm" className="block text-[var(--text-faint)]">{c.arabic}</ArabicText>
                      )}
                    </th>
                  ))}
                  {/* Last in an RTL row is the far left, which is where the one
                      English column belongs, out of the way of the Arabic. */}
                  <th
                    dir="ltr"
                    className="sticky left-0 z-10 bg-[var(--surface-hi)] text-left px-4 py-2
                      text-[var(--text-faint)] text-xs uppercase tracking-wide"
                  >
                    Person
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={row.person} className={i % 2 ? 'bg-[var(--surface)]' : ''}>
                    {visible.map((c) => (
                      <td key={c.id} className="px-4 py-1.5 text-center whitespace-nowrap text-[var(--text)]" dir="rtl" lang="ar">
                        {/* Reading size, the same as the صرف صغير above; a verb is
                            the thing being studied here, not a label. */}
                        <ArabicText>{row.cells?.[c.id] ?? ''}</ArabicText>
                      </td>
                    ))}
                    <th
                      scope="row"
                      dir="ltr"
                      className={`sticky left-0 z-10 px-4 py-1.5 text-left font-normal whitespace-nowrap
                        text-xs text-[var(--text-dim)] ${i % 2 ? 'bg-[var(--surface)]' : 'bg-[var(--surface-hi)]'}`}
                    >
                      {row.person}
                    </th>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Some of the book's rules allow a second spelling. Choosing one of
              them silently would print a preference as if it were the rule, so
              the others are named under the table instead. */}
          {notes.length > 0 && (
            <TableNote accent={accent} title="The book also allows">
              {notes.join(' ')}
            </TableNote>
          )}
        </>
      )}
    </div>
  )
}

/**
 * The sarf sagheer, the one line a book puts at the head of a baab, and the
 * part a reader actually memorises. It belongs above the grid, not under it.
 */
function SarfSagheer({ summary, accent }) {
  return (
    <div
      style={{ '--c': accent }}
      className="p-4 rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
        border-l-4 border-l-[var(--c)] space-y-3"
    >
      <span className="block text-[var(--text)] font-medium text-sm">Sarf sagheer (صرف صغير)</span>
      {/* The book reads the باب out right to left, ماضي first, on the right; 
          so the slots are laid out that way too, same as the grid below. */}
      <div dir="rtl" className="grid gap-2 grid-cols-[repeat(auto-fit,minmax(8rem,1fr))]">
        {summary.map((slot, i) => (
          <div
            key={slot.label}
            style={{ '--i': i }}
            className="rise-in rounded-[var(--radius-md)] p-3 text-center
              bg-[var(--surface-hi)] border border-[var(--border)]"
          >
            <div dir="ltr" className="text-[var(--text-faint)] type-tiny uppercase tracking-wide mb-1">{slot.label}</div>
            <ArabicText className="block text-[var(--text)]">{slot.arabic}</ArabicText>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * What the word means, and the two ways out of this tab.
 *
 * The buttons used to sit in a line of their own under the cards, with the root
 * repeated beside them: a row that said nothing the ROOT card did not, in the
 * one place a reader has finished reading. They live here now, under the
 * meaning, where the next question actually is, where does this word come from
 * and where is it used.
 *
 * The meaning itself is the dictionary's first sense. Define is for the reader
 * who wants the rest of that entry, so the card is the short answer and the
 * button is the long one.
 */
function MeaningCard({ meaning, pending, root, onGo, accent, i }) {
  return (
    <div
      dir="ltr"
      style={{ '--i': i, '--c': accent }}
      className="rise-in rounded-[var(--radius-md)] p-4 bg-[var(--surface)] border border-[var(--border)]
        flex flex-col gap-2"
    >
      <div className="text-[var(--text-faint)] type-tiny uppercase tracking-wide">Meaning</div>

      {/* Three lines, then the rest one press away. Half the dictionary's senses
          are a handful of words, but the longest is 800 characters of prose about
          the letter hamzah. Cut with ShowRest, as everywhere else: a hover title
          said nothing on a phone, where there is no hover. */}
      {meaning && (
        <ShowRest lines={3} accent={accent} className="text-[var(--text)] text-sm">{meaning}</ShowRest>
      )}
      {!meaning && pending && <Skeleton className="h-4 w-2/3" />}
      {/* A gap stays a gap. The dictionary has no entry for plenty of real
          words, and Define is exactly the button for that case. */}
      {!meaning && !pending && (
        <div className="type-small text-[var(--text-faint)]">No dictionary entry for this word.</div>
      )}

      {root && (
        <RootActions
          root={root}
          onGo={onGo}
          exclude="sarf"
          showRoot={false}
          className="mt-auto pt-1"
        />
      )}
    </div>
  )
}

function InfoCard({ label, value, gloss, arabic, accent, i }) {
  return (
    <div
      dir="ltr"
      style={{ '--i': i, '--c': accent }}
      className="rise-in rounded-[var(--radius-md)] p-4 bg-[var(--surface)] border border-[var(--border)]"
    >
      <div className="text-[var(--text-faint)] type-tiny uppercase tracking-wide mb-1">{label}</div>
      {/* The card itself reads left to right, so the Arabic stays inline and
          starts where the label starts, a block would push it to the far edge
          and leave the label and the gloss pointing the other way. */}
      {arabic
        ? <ArabicText className="text-[var(--text)]">{value}</ArabicText>
        : <div className="text-[var(--text)] text-sm">{value}</div>}
      {gloss && <div className="text-[var(--text-dim)] text-xs mt-1 leading-snug">{gloss}</div>}
    </div>
  )
}

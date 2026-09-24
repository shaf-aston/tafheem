/**
 * Nahw: the reader's own sentence, analysed.
 *
 * Analyse answers both questions at once, because one reading produces both:
 * which words join and what that unit does (the bracket picture), and what each
 * word is, its case and the reason (the cards under it). They were two tabs,
 * Tarkeeb and I'raab, and splitting them meant the picture could only ever show
 * a stored example while a typed sentence got cards alone.
 *
 * Tamreen is practice and Notes is the theory. The books' own worked tarkeeb
 * lives in a drawer inside Analyse: it is what to compare against, not the point.
 *
 * This file only picks which of the three is on screen and carries a sentence in
 * from elsewhere.
 */
import { useEffect, useState } from 'react'

import { useArrival } from '../lib/useArrival'
import { readViewParam, writeViewParams } from '../lib/tabUrl'
import { useRemembered } from '../lib/useRemembered'

import IraabAnalyzer from './IraabAnalyzer'
import NotesPanel from './NotesPanel'
import TamreenPanel from './TamreenPanel'
import TarkeebPanel from './TarkeebPanel'
import Disclosure from './ui/Disclosure'
import GrammarGlossary from './ui/GrammarGlossary'
import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'

const VIEWS = [
  // Named, not explained: the header above already says what each one is.
  { id: 'analyse', label: 'Analyse · تحليل' },
  { id: 'tamreen', label: 'Tamreen · تمرين' },
  { id: 'notes', label: 'Notes · قواعد' },
]

// The two views this page used to have. A saved address still opens the page
// they meant, which is now the one view that answers both.
const MERGED = { tarkeeb: 'analyse', iraab: 'analyse' }

// The address keys each view writes, so leaving a view clears only its own.
const VIEW_PARAMS = {
  tamreen: ['mode', 'topic', 'kind', 'show', 'question'],
  notes: ['note', 'notes-mode'],
}

const VIEW_IDS = VIEWS.map((one) => one.id)

export default function NahwPanel({ accent, incoming, arrival, onGo, onVisit, onProgress }) {
  // The view they last switched to, still the view on return (useRemembered).
  const [lastChosen, rememberView] = useRemembered('nahw-view', VIEW_IDS)
  // A sentence handed over from elsewhere, the command bar included, opens the
  // view that can show it. Not remembered, being the sentence's doing rather
  // than a choice made.
  const asked = readViewParam('view', [...VIEW_IDS, ...Object.keys(MERGED)])
  const [view, setView] = useState(incoming ? 'analyse' : MERGED[asked] ?? asked ?? lastChosen)
  useEffect(() => {
    const others = Object.entries(VIEW_PARAMS).filter(([id]) => id !== view).flatMap(([, keys]) => keys)
    writeViewParams({ view, ...Object.fromEntries(others.map((key) => [key, ''])) })
  }, [view])

  // The notes topic a Tamreen question asked for, handed to the notes view.
  // Only for that one trip: choosing Notes from the row opens the last topic read.
  const [noteTopic, setNoteTopic] = useState(null)
  const chooseView = (id) => {
    setView(id)
    rememberView(id)
    setNoteTopic(null)
  }
  const openNotes = (topicId) => {
    chooseView('notes')
    setNoteTopic(topicId)
  }
  // A sentence picked out of the books' drawer. Null while the reader is typing
  // their own, which is what tells the box above which sentence it is showing.
  const [fromExample, setFromExample] = useState(null)

  // A sentence arriving on the tab already open, from the command bar or from
  // the back arrow, is the same event as one arriving with the tab: it is the
  // sentence to analyse, and the example the reader was on is not it. App
  // used to remount the panel for it, which faded the whole page back in; see
  // lib/useArrival.
  const { arrived } = useArrival(arrival)
  if (arrived && incoming) {
    setFromExample(null)
    setView('analyse')
  }

  // Not remembered either, for the same reason: the example goes when the page
  // does, and coming back to an empty box would be worse than coming back to
  // the drawer of examples they were reading.
  const openWordByWord = (sentence) => {
    setFromExample(sentence)
    setView('analyse')
  }

  return (
    <div className="space-y-5">
      {/* The views ride on the title line, in the space a two-word title leaves
          empty. On their own row they cost a whole row and read as a step to
          take before typing, which they are not. */}
      <SectionHeader
        title="Nahw"
        arabic="نحو"
        aside={(
          <Segmented
            label="Which part of Nahw to work on"
            value={view}
            onChange={chooseView}
            accent={accent}
            options={VIEWS}
            className="w-fit"
          />
        )}
      />

      {view === 'analyse' && (
        <div className="space-y-5">
          {/* Keyed by the sentence: a new one arriving starts fresh on it
              rather than leaving the last analysis on screen. One prop,
              whether it came from an example or from the command bar. */}
          <IraabAnalyzer
            key={fromExample ?? incoming ?? 'typed'}
            accent={accent}
            onGo={onGo}
            onVisit={onVisit}
            analyse={fromExample ?? incoming}
          />
          {/* The books' own tarkeeb sentences, now the second thing on the page:
              the reader's own sentence is the first. Shut until asked for, and
              picking one sends it up to the box above. Named for tarkeeb, not
              "worked examples": that reads as questions to answer, which is
              Tamreen, and it is where the reader went looking for tarkeeb. */}
          <Disclosure label="Tarkeeb book examples" tone="strong">
            <div className="pt-4">
              <TarkeebPanel accent={accent} onWordByWord={openWordByWord} />
            </div>
          </Disclosure>
        </div>
      )}
      {view === 'tamreen' && <TamreenPanel accent={accent} onProgress={onProgress} onNotes={openNotes} />}
      {view === 'notes' && <NotesPanel accent={accent} topic={noteTopic} onTamreen={() => chooseView('tamreen')} />}

      {/* The one place the terms are put into English. Shut until asked. */}
      <GrammarGlossary />
    </div>
  )
}

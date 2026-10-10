/**
 * Nahw: Analyse (the reader's own sentence: bracket picture and a card per word,
 * from one reading), Tamreen (practice) and Notes (theory). The books' worked
 * tarkeeb sits in a drawer inside Analyse, to compare against. This file only
 * picks which view is on screen and carries a sentence in from elsewhere.
 */
import { useEffect, useState } from 'react'

import { useArrival } from '../lib/useArrival'
import { readViewParam, writeViewParams } from '../lib/tabUrl'
import { useRemembered } from '../lib/useRemembered'

import IraabAnalyzer from './nahw/IraabAnalyzer'
import NotesPanel from './nahw/NotesPanel'
import TamreenPanel from './nahw/TamreenPanel'
import TarkeebPanel from './nahw/TarkeebPanel'
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

  // A sentence arriving on the open tab (command bar, back arrow) is the one to
  // analyse, same as arriving with the tab. Remounting for it re-faded the page.
  const { arrived } = useArrival(arrival)
  if (arrived && incoming) {
    setFromExample(null)
    setView('analyse')
  }

  // Not remembered: coming back to an empty box beats losing the drawer they were reading.
  const openWordByWord = (sentence) => {
    setFromExample(sentence)
    setView('analyse')
  }

  return (
    <div className="panel">
      {/* The views ride on the title line: on their own row they read as a step before typing. */}
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
          {/* Keyed by the sentence, so a new one starts fresh. */}
          <IraabAnalyzer
            key={fromExample ?? incoming ?? 'typed'}
            accent={accent}
            onGo={onGo}
            onVisit={onVisit}
            analyse={fromExample ?? incoming}
          />
          {/* Named for tarkeeb, not "worked examples": that reads as questions, which is Tamreen. */}
          <Disclosure label="Tarkeeb book examples" tone="strong">
            <div className="pt-4">
              <TarkeebPanel accent={accent} onWordByWord={openWordByWord} />
            </div>
          </Disclosure>
        </div>
      )}
      {view === 'tamreen' && <TamreenPanel accent={accent} onProgress={onProgress} onNotes={openNotes} />}
      {view === 'notes' && <NotesPanel accent={accent} topic={noteTopic} onTamreen={() => chooseView('tamreen')} />}

      {/* The one place the terms are put into English. */}
      <GrammarGlossary />
    </div>
  )
}

/**
 * An Arabic sentence, analysed: the bracket picture of how its words join, then
 * a card for each word. One `/api/analyze` request returns both, so they are the
 * same reading. The picture is left out when nothing could be joined.
 */
import { useState } from 'react'

import { analyzeIraab, generatePractice } from '../../api'
import { errorMessage, errorStatus } from '../../lib/api/apiError'
import { useMutation } from '../../lib/api/useMutation'
import { useArrivalEffect } from '../../lib/nav/useArrival'

import WordCard from '../grammar/WordCard'
import BottomSheet from '../ui/overlays/BottomSheet'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import ExampleChips from '../ui/inputs/ExampleChips'
import MicButton from '../ui/buttons/MicButton'
import SearchBox from '../ui/inputs/SearchBox'
import QuestionForm from '../ui/inputs/QuestionForm'
import { AnalyzerSkeleton } from '../ui/feedback/Skeleton'
import AnalysisResults from './iraab/AnalysisResults'

const EXAMPLES = [
  { arabic: 'ضَرَبَ زيدٌ عمراً', meaning: 'Zayd struck ʿAmr' },
  { arabic: 'الكِتَابُ مُفِيدٌ', meaning: 'The book is useful' },
  { arabic: 'إِنَّ اللهَ غَفُورٌ رَحِيمٌ', meaning: 'Indeed Allah is Forgiving, Merciful' },
  { arabic: 'ذَهَبَ الطَّالِبُ إِلَى الْمَدْرَسَةِ', meaning: 'The student went to school' },
]

// `more` is the page's own extras, drawn as rows under this sentence's (Full table,
// Practice) so they read as one list, or alone when nothing is analysed yet.
export default function IraabAnalyzer({ accent, onGo, onVisit, analyse = null, more = null }) {
  const [sentence, setSentence] = useState(analyse ?? '')
  const [selectedWord, setSelectedWord] = useState(null)
  // A sentence analysed is a place reached; the trail shortens it to fit.
  const practice = useMutation({ mutationFn: generatePractice })
  // A new sentence drops the last one's questions.
  const analyze = useMutation({
    mutationFn: analyzeIraab,
    onSuccess: (_, asked) => { practice.reset(); onVisit?.(asked) },
  })
  const shown = analyze.data && !analyze.isPending

  const submit = () => {
    const trimmed = sentence.trim()
    if (trimmed) analyze.mutate(trimmed)
  }

  const runExample = (text) => {
    setSentence(text)
    analyze.mutate(text)
  }

  // A sentence handed over from the wide view is analysed on arrival; the box
  // is already filled from the same prop. Once per sentence, not per return to the tab.
  useArrivalEffect(analyse, () => {
    if (analyse) analyze.mutate(analyse)
  })

  return (
    <div className="space-y-6">
      <QuestionForm>
        {/* The same field as Dictionary and Daleel, grown to a textarea: see
            ui/SearchBox's multiline mode. */}
        <SearchBox
          id="iraab-input"
          label="Arabic sentence"
          verb="analyse"
          placeholder="اكتب جملة عربية هنا..."
          value={sentence}
          onChange={setSentence}
          onSubmit={submit}
          onClear={() => { setSentence(''); analyze.reset(); practice.reset() }}
          busy={analyze.isPending}
          accent={accent}
          arabic
          multiline
        >
          <MicButton
            onHeard={({ text }) => setSentence(text)}
            accent={accent}
            title="Say the sentence"
          />
        </SearchBox>

        <ExampleChips examples={EXAMPLES} onPick={runExample} accent={accent} />
      </QuestionForm>

      {analyze.isError && <AnalyzeError error={analyze.error} onRetry={submit} />}
      {analyze.isPending && <AnalyzerSkeleton />}

      <div aria-live="polite">
        {shown && (
          <AnalysisResults
            data={analyze.data}
            accent={accent}
            onGo={onGo}
            onWordClick={setSelectedWord}
            picked={analyze.data.words.indexOf(selectedWord)}
            practice={practice}
            more={more}
          />
        )}
      </div>
      {/* The opened word's card, over the page (a dialog's top layer): closing it leaves the page where it
          was, whichever of the chart, grid or table opened it. */}
      {shown && selectedWord && (
        <BottomSheet label={`${selectedWord.word}: grammar`} onClose={() => setSelectedWord(null)}
          className="max-h-[var(--sheet-tall)] overflow-y-auto p-3">
          <WordCard word={selectedWord} onClose={() => setSelectedWord(null)} onGo={onGo} exclude="nahw" />
        </BottomSheet>
      )}
      {!shown && more && <div>{more}</div>}
    </div>
  )
}

function AnalyzeError({ error, onRetry }) {
  const status = errorStatus(error)
  return (
    <ErrorAlert title={status === 504 ? 'Timed out' : 'Analysis failed'} onRetry={onRetry}>
      <div>{errorMessage(error)}</div>
    </ErrorAlert>
  )
}

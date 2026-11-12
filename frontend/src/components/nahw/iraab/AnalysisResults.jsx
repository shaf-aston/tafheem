import { useRemembered } from '../../../lib/store/useRemembered'
import { caseFrom } from '../../../lib/nahw/grammarTerms'
import { buildIraabExportText } from '../../../lib/nahw/iraabExport'
import { useTarkeebView } from '../../../lib/nahw/useTarkeebView'
import ArabicText from '../../ui/text/ArabicText'
import CopyButton from '../../ui/buttons/CopyButton'
import FlagButton from '../../ui/buttons/FlagButton'
import SourceBadge from '../../ui/feedback/SourceBadge'
import StatusNote from '../../ui/feedback/StatusNote'
import TarkeebTools from '../../grammar/tarkeeb/TarkeebTools'
import PracticePanel from '../PracticePanel'
import ChartWithPeek from './ChartWithPeek'
import FullIraabTable from './FullIraabTable'
import { EnglishFoot, EnglishMeaning } from './SentenceEnglish'
import { useSentenceMeaning } from '../../../lib/nahw/useSentenceMeaning'
import WordGrid, { GovernsWhy } from './WordGrid'

// What the word row draws: each word's role, or arcs from governor to governed.
const LENSES = ['roles', 'governs']

export default function AnalysisResults({ data, accent, onGo, onWordClick, picked, practice, more }) {
  const [lens, setLens] = useRemembered('nahw.analyse-lens', LENSES)
  const linked = data.words.some((w) => caseFrom(w) !== undefined)
  const governs = linked && lens === 'governs'
  const view = useTarkeebView(data.tree)
  const meaning = useSentenceMeaning(data.sentence)
  const copy = <CopyButton text={buildIraabExportText(data)} label="Copy" />
  return (
    <div className="space-y-4">
      {/* With a tree, Copy sits in the tree card's foot, not on a row of its own. */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        {data.summary && (
          <div
            className="rise-in flex items-center gap-2 type-ui px-3 py-2 rounded-[var(--radius-md)]
              bg-[var(--surface)] border border-[var(--border)]"
          >
            <span className="text-[var(--text-faint)] type-label uppercase tracking-wide">Sentence</span>
            <span className="text-[var(--text)]">{data.summary}</span>
            <SourceBadge source={data.source} />
          </div>
        )}
        {!data.tree && copy}
      </div>

      {data.unvowelled && (
        <StatusNote>
          {data.unvowelled.en} <ArabicText size="tiny">{data.unvowelled.ar}</ArabicText>
        </StatusNote>
      )}

      {data.tree && (
        // An ayah drawn from its record carries the words the book supplies,
        // (هُوَ) or an elided khabar, and the mark it writes them with.
        <ChartWithPeek data={data} view={view} glosses={meaning.data?.words}
          onMore={onWordClick} onLookup={onGo && ((w) => onGo('dict', w))}
          foot={<EnglishFoot meaning={meaning} accent={accent} onGo={onGo}><TarkeebTools view={view} />{copy}</EnglishFoot>} />
      )}
      {!data.tree && <EnglishMeaning meaning={meaning} accent={accent} onGo={onGo} />}
      <WordGrid words={data.words} onClick={onWordClick} governs={governs} picked={picked}
        corner={linked && (
          <FlagButton value={governs} onChange={(on) => setLens(on ? 'governs' : 'roles')} accent={accent}
            title="Draw arrows from each governor to the word it governs">
            see governance
          </FlagButton>
        )} />
      <p className="text-center type-small text-[var(--text-faint)]">
        {governs && picked >= 0 && caseFrom(data.words[picked]) !== undefined
          ? <GovernsWhy words={data.words} i={picked} />
          : 'Tap a word for breakdown'}
      </p>

      {/* The extras: one list of rows, the page's own (`more`) after this sentence's. */}
      <div>
        <FullIraabTable words={data.words} onRowClick={onWordClick} />
        <PracticePanel practice={practice} sentence={data.sentence} accent={accent} />
        {more}
      </div>
    </div>
  )
}

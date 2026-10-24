import { answerParts, partPicks } from '../../../lib/nahw/tamreen'

import TamreenAnswerNote from '../TamreenAnswerNote'
import TamreenSentence, { TamreenLegend } from '../TamreenSentence'
import GridPart from './GridPart'
import OptionList from './OptionList'

// A picture question: its sentence, then every ticked part in the order asked.
export default function ExampleQuestion({ example, picks, onToggleRow, onToggleOption, checked }) {
  return (
    <div className="space-y-3">
      <TamreenSentence example={example} />
      {example.marked?.length > 0 && <TamreenLegend />}
      {/* Each part rises in after the last. On the part, not its rows: a row
          moving inside the sideways-scroll box flashed a scrollbar. */}
      {answerParts(example).map((part, n) => (
        <div key={part.letter} style={{ '--i': n }} className="rise-in space-y-2">
          {part.question && <p dir="auto" className="type-small text-[var(--text-dim)]">{part.question}</p>}
          {part.rows
            ? <GridPart part={part} picks={partPicks(picks, part)} checked={checked}
                onToggle={(row, option) => onToggleRow(part, row, option)} />
            : <OptionList part={part} picked={new Set(partPicks(picks, part))} checked={checked}
                onToggle={(option) => onToggleOption(part, option)} />}
        </div>
      ))}
      {checked && <TamreenAnswerNote example={example} />}
    </div>
  )
}

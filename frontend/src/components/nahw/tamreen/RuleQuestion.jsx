import OptionList from './OptionList'

export default function RuleQuestion({ rule, picked, onToggle, checked }) {
  return (
    <div className="space-y-2">
      <p dir="auto" className="font-medium text-[var(--text)]">{rule.question}</p>
      <OptionList part={rule} picked={picked} onToggle={onToggle} checked={checked} />
    </div>
  )
}

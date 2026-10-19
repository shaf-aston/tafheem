import { DIRECTIONS, MEANINGS } from '../../lib/quiz'
import { BANKS, QUIZ, WHOLE_SET_SCOPES } from '../../lib/quizBanks'

import Segmented from '../ui/Segmented'
import SettingsPill from '../ui/SettingsPill'
import WheelPicker from '../ui/WheelPicker'

/**
 * The Quiz tab's one quiet line of setup, so the question is the first thing you
 * see rather than something you scroll past three panels to reach. `setup` is
 * useQuizSetup's; every choice goes to `onChange`, which starts a fresh round.
 * `owed` is the count of words due, worn on the Review control.
 */
export default function QuizSetup({ setup, owed, say, phone, accent, onChange }) {
  const { language, direction, directions, bankId, bank, groups, scope, groupId, section } = setup

  // A phone has no room for the narrowing beside the words, so it goes behind
  // the same pill as the other two settings, and the pill names what it holds.
  const scopeOptions = [
    ...WHOLE_SET_SCOPES.map(({ id, label }) => ({ id, label: say(label) })),
    ...groups.map((s) => ({ id: s.id, label: say(s.label) })),
  ]
  const scopeControls = bank.grouped && (
    <>
      {/* Which kind of cut, then which one; two short controls instead of
          one dropdown holding 28 topics, 114 surahs and 30 juz at once. */}
      <Segmented
        captioned={phone}
        wrap={phone}
        label={say('Narrow by')}
        options={scopeOptions}
        value={scope}
        accent={accent}
        onChange={(id) => onChange({ scope: id })}
      />
      {section && (
        <>
          {/* Behind the pill every control wears its caption, as its neighbours do. */}
          {phone && <span className="eyebrow">{say('Which {kind}', { kind: say(section.label).toLowerCase() })}</span>}
          <span className="block">
            <WheelPicker
              label={say('Which {kind}', { kind: say(section.label).toLowerCase() })}
              options={section.options.map((option) => ({
                id: option.id,
                label: `${option.label} (${option.size})`,
                disabled: option.size < QUIZ.optionCount,
              }))}
              value={groupId}
              onChange={(group) => onChange({ group })}
              accent={accent}
              className="max-w-[13rem]"
            />
          </span>
        </>
      )}
    </>
  )
  // Which set of words. Wide screens keep it on the line; a phone has no room
  // for four options and a count beside the pill, so it goes behind the pill too.
  const bankControl = (
    <Segmented
      captioned
      wrap={phone}
      label={say('Words')}
      options={Object.entries(BANKS).map(([id, b]) => ({
        id,
        // The count rides on the control that goes there: a number sitting
        // anywhere else is a badge nobody connects to the button.
        label: b.live && owed > 0 ? `${say(b.label)} · ${owed}` : say(b.label),
      }))}
      value={bankId}
      accent={accent}
      onChange={(id) => onChange({ bank: id })}
    />
  )
  const pillWords = [
    ...(phone ? [say(bank.label)] : []),
    ...(phone && bank.grouped
      ? [section?.options.find((o) => o.id === groupId)?.label ?? scopeOptions.find((o) => o.id === scope)?.label]
      : []),
    MEANINGS[language].label,
    DIRECTIONS[direction].short,
  ].filter(Boolean)

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
      {!phone && bankControl}
      {!phone && scopeControls}
      {/* The two settings chosen once and left, folded behind one pill that
          says what they are. All four controls on the line needed 1,170px of
          a 1,120px column, so English wrapped on every screen. */}
      <SettingsPill
        label={pillWords.join(' · ')}
        title={`${say('Words')}, ${say('Meaning in')}, ${say('Direction')}`}
        align={phone ? 'start' : 'end'}
      >
        {phone && bankControl}
        {phone && scopeControls}
        <Segmented
          captioned
          label={say('Meaning in')}
          options={Object.entries(MEANINGS).map(([id, meaning]) => ({ id, label: meaning.label }))}
          value={language}
          accent={accent}
          onChange={(id) => onChange({ language: id })}
        />
        <Segmented
          captioned
          label={say('Direction')}
          // AR → UR stays as it is in every language: it is a pair of codes, not a
          // sentence, and an arrow glyph flips its own direction inside
          // right-to-left text, which would make the label say the opposite.
          options={directions.map((id) => ({ id, label: DIRECTIONS[id].short }))}
          value={direction}
          accent={accent}
          onChange={(id) => onChange({ direction: id })}
        />
      </SettingsPill>
    </div>
  )
}

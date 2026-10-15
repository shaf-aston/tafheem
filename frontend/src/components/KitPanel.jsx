/**
 * The kit: every token and every element, drawn from the live code.
 *
 * Reached at /app/kit and listed nowhere (the tab is `hidden`). Tokens are
 * read from theme.json, so a new one appears here with no edit to this file;
 * the elements are the real ui/ primitives, so a restyle shows here the moment
 * it lands. The token names printed beside each element are written by hand
 * and are the only part that can go stale.
 *
 * Each demo sits in its own boundary: an element that throws shows an
 * ErrorAlert in its card instead of blanking the page.
 */
import { Component, useState } from 'react'

import { tokenGroups, variableName } from '../theme'
import { CONFIDENCE } from '../lib/confidence'
import mascot from '../mascot.json'

import ArabicText from './ui/ArabicText'
import Chip from './ui/Chip'
import Disclosure from './ui/Disclosure'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import IndexNotBuilt from './ui/IndexNotBuilt'
import Mascot from './ui/Mascot'
import MicButton from './ui/MicButton'
import Popover from './ui/Popover'
import PrimaryButton from './ui/PrimaryButton'
import RetryButton from './ui/RetryButton'
import SearchBox from './ui/SearchBox'
import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'
import ShowRest from './ui/ShowRest'
import { AnalyzerSkeleton, Skeleton } from './ui/Skeleton'
import SmallButton from './ui/SmallButton'
import SourceBadge from './ui/SourceBadge'
import SpeakButton from './ui/SpeakButton'
import StatusNote from './ui/StatusNote'
import Tooltip from './ui/Tooltip'
import TranslationStrip from './ui/TranslationStrip'
import TwinCards from './ui/TwinCard'
import WheelPicker from './ui/WheelPicker'

// A value drawn as a swatch: a literal colour or a reference to a colour token.
const COLOURISH = /^(#[0-9a-f]{3,8}|rgba?\(|hsla?\(|color-mix\(|var\(--)/i

const SIZES = ['tiny', 'sm', 'base', 'lg']
const SAMPLE_AYAH = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ'
// Two twin verses (2:59 and 7:162), the differing words marked by position.
const TWIN_MINE = { key: '2:59', text: 'فَبَدَّلَ الَّذِينَ ظَلَمُوا قَوْلًا غَيْرَ الَّذِي قِيلَ لَهُمْ' }
const TWIN_QUERY = {
  idle: {
    data: {
      key: '2:59',
      partners: [{
        key: '7:162',
        text: 'فَبَدَّلَ الَّذِينَ ظَلَمُوا مِنْهُمْ قَوْلًا غَيْرَ الَّذِي قِيلَ لَهُمْ',
        change_type: 'addition & subtraction',
        diff_self: [],
        diff_other: [[4, 5]],
        sources: [{ label: 'Mutashabihat list', confidence: 'verified', detail: 'Demo' }],
      }],
    },
  },
  loading: { isPending: true },
  empty: { data: { key: '2:59', partners: [] } },
  error: { isError: true, error: new Error('The backend did not answer.'), refetch: () => {} },
}

const LONG_TEXT = 'A line of English long enough to run past its cut, so the fold has something to hide. '
  .repeat(6)

/** Catches one demo's crash so the rest of the page lives. */
class DemoBoundary extends Component {
  state = { error: null }
  static getDerivedStateFromError(error) { return { error } }
  render() {
    const { error } = this.state
    return error
      ? <ErrorAlert title="This element threw" inline>{String(error.message ?? error)}</ErrorAlert>
      : this.props.children
  }
}

function Card({ title, note, wide = false, children }) {
  return (
    <section
      className={`rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 space-y-3
        min-w-0 ${wide ? 'md:col-span-2 lg:col-span-3' : ''}`}
    >
      <header>
        <h3 className="text-sm font-semibold text-[var(--text)]">{title}</h3>
        {note && <p className="type-micro text-[var(--text-faint)] break-words">{note}</p>}
      </header>
      {children}
    </section>
  )
}

/** One element in its states; the boundary keeps a crash inside the card. */
const Demo = ({ name, tokens, wide, children }) => (
  <Card title={name} note={tokens} wide={wide}>
    <DemoBoundary>{children}</DemoBoundary>
  </Card>
)

// A labelled state: the label is dim and small so the element is what you read.
const State = ({ label, children }) => (
  <div className="space-y-1.5">
    <p className="type-micro text-[var(--text-faint)] uppercase tracking-wide">{label}</p>
    {children}
  </div>
)

function TokenCard({ group, entries }) {
  return (
    <Card title={group} note={`${entries.length} tokens`}>
      <ul className="space-y-1">
        {entries.map(([key, value]) => {
          const text = String(value)
          return (
            <li key={key} className="flex items-center gap-2 min-w-0">
              <span
                aria-hidden="true"
                className="w-4 h-4 shrink-0 rounded-[var(--radius-sm)] border border-[var(--border)]"
                style={COLOURISH.test(text) ? { background: text } : undefined}
              />
              <code className="type-small text-[var(--text-dim)] shrink-0">{variableName(group, key)}</code>
              <span className="type-micro text-[var(--text-faint)] truncate" title={text}>{text}</span>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}

function SearchDemo({ accent }) {
  const [value, setValue] = useState('')
  const box = (props) => (
    <SearchBox label="Search" placeholder="Type here" value={value} onChange={setValue}
      accent={accent} {...props} />
  )
  return (
    <div className="space-y-4">
      <State label="idle, type to see the clear button">{box({ id: 'kit-search' })}</State>
      <State label="busy">{box({ id: 'kit-search-busy', value: 'كتب', onSubmit: () => {}, busy: true })}</State>
      <State label="disabled">{box({ id: 'kit-search-off', disabled: true })}</State>
    </div>
  )
}

function ChoiceDemo({ accent }) {
  const [seg, setSeg] = useState('a')
  const [wheel, setWheel] = useState('b')
  const [chip, setChip] = useState('x')
  const options = ['a', 'b', 'c'].map((id) => ({ id, value: id, label: `Option ${id.toUpperCase()}` }))
  return (
    <div className="space-y-4">
      <State label="Segmented">
        <Segmented label="Kit segmented" options={options} value={seg} onChange={setSeg} accent={accent} />
      </State>
      <State label="WheelPicker">
        <WheelPicker label="Kit wheel" options={options} value={wheel} onChange={setWheel} accent={accent} />
      </State>
      <State label="Chip: plain, selected, tinted, quiet, cite, arabic">
        <div className="flex flex-wrap items-center gap-2">
          {['x', 'y'].map((id) => (
            <Chip key={id} accent={accent} selected={chip === id} onClick={() => setChip(id)}>{`Chip ${id}`}</Chip>
          ))}
          <Chip accent={accent} tinted selected>Tinted</Chip>
          <Chip accent={accent} quiet>Quiet</Chip>
          <Chip accent={accent} cite>Cited</Chip>
          <Chip accent={accent} arabic>كِتَاب</Chip>
        </div>
      </State>
    </div>
  )
}

function Elements({ accent }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Demo name="PrimaryButton, SmallButton, RetryButton"
        tokens="--primary --surface --text-faint --border --border-hi --danger --radius-md --radius-sm">
        <div className="space-y-3">
          <State label="idle"><PrimaryButton accent={accent}>Go</PrimaryButton></State>
          <State label="loading"><PrimaryButton accent={accent} loading>Working</PrimaryButton></State>
          <State label="disabled"><PrimaryButton accent={accent} disabled>Go</PrimaryButton></State>
          <State label="small, idle and disabled">
            <div className="flex gap-2">
              <SmallButton>Back</SmallButton>
              <SmallButton disabled>Skip</SmallButton>
            </div>
          </State>
          <State label="retry"><RetryButton onClick={() => {}} /></State>
        </div>
      </Demo>

      <Demo name="SearchBox" tokens="--surface --border --text --text-faint --radius-md --c" wide>
        <SearchDemo accent={accent} />
      </Demo>

      <Demo name="Segmented, WheelPicker, Chip"
        tokens="--surface --border --text-faint --text-dim --layout-chip --c">
        <ChoiceDemo accent={accent} />
      </Demo>

      <Demo name="Disclosure" tokens="--text-faint --text --surface --border --radius-md">
        <div className="space-y-3">
          <State label="quiet, shut"><Disclosure label="More detail">Hidden until opened.</Disclosure></State>
          <State label="framed, open">
            <Disclosure label="A framed body" framed defaultOpen tone="strong">Content inside the frame.</Disclosure>
          </State>
        </div>
      </Demo>

      <Demo name="ShowRest" tokens="--text-dim --text-faint">
        <ShowRest lines={2} accent={accent}>
          <p className="text-sm text-[var(--text-dim)]">{LONG_TEXT}</p>
        </ShowRest>
      </Demo>

      <Demo name="StatusNote, EmptyState, ErrorAlert, IndexNotBuilt" tokens="--text-dim --danger --radius-md">
        <div className="space-y-3">
          <State label="note"><StatusNote>searched prayer for pryer</StatusNote></State>
          <State label="empty"><EmptyState>Nothing here yet.</EmptyState></State>
          <State label="error"><ErrorAlert title="Could not load">The backend did not answer.</ErrorAlert></State>
          <State label="error, inline"><ErrorAlert title="Failed" inline>Try again in a moment.</ErrorAlert></State>
          <State label="no index"><IndexNotBuilt command="python backend/scripts/build_hadith_index.py" /></State>
        </div>
      </Demo>

      <Demo name="TwinCards" tokens="--surface --border --text-dim --text-faint --tab accent" wide>
        <div className="grid gap-3 md:grid-cols-2">
          {Object.entries(TWIN_QUERY).map(([state, query]) => (
            <State key={state} label={state}>
              <TwinCards mine={TWIN_MINE} query={query} accent={accent} />
            </State>
          ))}
        </div>
      </Demo>

      <Demo name="Skeleton" tokens="--surface --surface-hi --radius-sm --motion-scale">
        <div className="space-y-3">
          <State label="loading, one bar"><Skeleton className="h-4 w-1/2" /></State>
          <State label="loading, a panel"><AnalyzerSkeleton /></State>
        </div>
      </Demo>

      <Demo name="Tooltip, Popover" tokens="--surface-hi --border-hi --text --layer-tip --motion-instant-ms">
        <div className="flex items-center gap-4 pt-8">
          <Tooltip text="Hover or focus to read this"><SmallButton>Hover me</SmallButton></Tooltip>
          <Popover label="Open panel" title="A floating panel">
            <p className="type-small text-[var(--text-dim)]">Shuts on Escape or a click elsewhere.</p>
          </Popover>
        </div>
      </Demo>

      <Demo name="SpeakButton, MicButton" tokens="--c --primary --danger --mic-weight --mic-pulse-ms">
        <div className="space-y-3">
          <State label="speak, idle (press to hear)"><SpeakButton text="كتاب" /></State>
          <State label="mic, idle (press to record)">
            <MicButton accent={accent} onHeard={() => {}} />
          </State>
        </div>
      </Demo>

      <Demo name="Mascot (Qalam)" tokens="--c --motion-scale --motion-spring-ms --size-rem in mascot.json" wide>
        <div className="flex flex-wrap gap-6">
          {Object.keys(mascot.captions).map((mood) => (
            <State key={mood} label={mood}><Mascot mood={mood} place="header" caption /></State>
          ))}
        </div>
      </Demo>

      <Demo name="TranslationStrip, SourceBadge" tokens="--surface-hi --border --success --primary --warn" wide>
        <div className="grid gap-4 md:grid-cols-2">
          <State label="strip with its credit">
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] overflow-clip">
              <TranslationStrip source={{ label: 'Saheeh International', confidence: 'verified' }}>
                <p className="type-body text-[var(--text-dim)]">In the name of Allah, the Entirely Merciful.</p>
              </TranslationStrip>
            </div>
          </State>
          <State label="badge, each confidence level">
            <div className="flex flex-wrap gap-2">
              {Object.keys(CONFIDENCE).map((level) => (
                <SourceBadge key={level} source={{ label: level, confidence: level }} />
              ))}
            </div>
          </State>
        </div>
      </Demo>

      <Demo name="ArabicText" tokens="--arabic-tiny-rem --arabic-small-rem --arabic-reading-rem --arabic-display-rem --font-arabic --font-urdu" wide>
        <div className="space-y-2">
          {SIZES.map((size) => (
            <State key={size} label={`size ${size}`}>
              <ArabicText as="p" size={size}>{SAMPLE_AYAH}</ArabicText>
            </State>
          ))}
          <State label="Urdu (lang ur)">
            <ArabicText as="p" lang="ur">یہ ایک جملہ ہے</ArabicText>
          </State>
        </div>
      </Demo>
    </div>
  )
}

function Motion() {
  // Remounting is what replays a one-shot animation; the key is the whole trick.
  const [run, setRun] = useState(0)
  return (
    <Card title="Motion" note=".dance, .rise-in, .skeleton (the shimmer); durations from the motion and dance groups">
      <SmallButton onClick={() => setRun((n) => n + 1)}>Replay</SmallButton>
      <div key={run} className="flex flex-wrap items-center gap-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="dance rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] px-4 py-3 type-small"
            style={{ '--i': i }}>.dance {i}</div>
        ))}
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="rise-in rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] px-4 py-3 type-small"
            style={{ '--i': i }}>.rise-in {i}</div>
        ))}
        <div className="skeleton h-10 w-40" aria-hidden="true" />
      </div>
    </Card>
  )
}

export default function KitPanel({ accent }) {
  return (
    <div className="space-y-6">
      <SectionHeader title="Kit" arabic="عدة"
        subtitle="Every token and every element, drawn from the live code." />

      <h2 className="text-sm font-semibold text-[var(--text-dim)]">Tokens</h2>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {tokenGroups().map(([group, entries]) => (
          <TokenCard key={group} group={group} entries={entries} />
        ))}
      </div>

      <h2 className="text-sm font-semibold text-[var(--text-dim)]">Elements</h2>
      <Elements accent={accent} />

      {/* No "Motion" heading: the card's own title says it. */}
      <Motion />
    </div>
  )
}

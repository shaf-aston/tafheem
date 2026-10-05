/**
 * The settings panel, one small place for everything a reader can change.
 *
 * It renders whatever settings.json declares and knows nothing about any
 * individual setting: a new entry in that file appears here on its own, with
 * its own label and help text. Adding a setting should never mean editing this.
 *
 * A native <dialog> is used on purpose, the browser gives focus trapping, Esc
 * to close and the backdrop for free, none of which is worth hand-writing.
 */
import { useEffect, useState } from 'react'

import { SETTINGS, resetSettings, setSetting, useSetting } from '../../lib/settings'
import { useHealth } from '../../lib/useHealth'
import { useModal } from '../../lib/useModal'
import { levelOf } from '../../lib/confidence'
import { forgetSaved } from '../../lib/stored'
import { useSources } from '../../lib/useSources'

import Disclosure from './Disclosure'
import Segmented from './Segmented'

// Settings grouped by the module they change, in the order settings.json first names each.
const SECTIONS = Object.entries(Object.groupBy(SETTINGS, (setting) => setting.section))

export default function SettingsPanel({ open, onClose }) {
  const dialog = useModal(open)
  const health = useHealth()

  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      // A click that lands on the dialog itself is a click on the backdrop:
      // every real control sits inside the box below.
      onClick={(e) => e.target === dialog.current && onClose()}
      aria-labelledby="settings-title"
      className="m-auto p-0 bg-transparent max-w-[min(var(--sheet-narrow),92vw)] w-full"
    >
      <div
        // Scrolls as one box. The source list below can run past the screen,
        // and giving it its own scroller would leave two bars side by side.
        className="rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
          p-5 space-y-5 max-h-[var(--sheet-tall)] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-baseline justify-between gap-3">
          <h2 id="settings-title" className="text-base font-bold text-[var(--text)]">
            Settings
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors"
          >
            Close
          </button>
        </div>

        {SECTIONS.map(([section, all]) => {
          const settings = all.filter((setting) => !setting['needs-health'] || health[setting['needs-health']])
          return settings.length > 0 && (
            <section key={section} aria-label={section} className="space-y-4">
              <h3 className="type-micro uppercase tracking-[0.18em] text-[var(--text-faint)]">{section}</h3>
              {settings.map((setting) => (
                <Setting key={setting.key} setting={setting} />
              ))}
            </section>
          )
        })}

        <SourceList />

        <a
          href="/"
          target="_blank"
          rel="noreferrer noopener"
          className="block type-small text-[var(--text-faint)] hover:text-[var(--text)] transition-colors"
        >
          About this project ↗
        </a>

        <StorageFooter />
      </div>
    </dialog>
  )
}

/** The small quiet button the two footer actions share, so they cannot drift. */
function FooterButton({ onClick, danger = false, disabled = false, title, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      style={danger ? { color: 'var(--danger)', borderColor: 'var(--danger)' } : undefined}
      className="type-small px-2.5 py-1 rounded-[var(--radius-sm)] border border-[var(--border)]
        text-[var(--text-dim)] hover:text-[var(--text)] hover:border-[var(--border-hi)]
        disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
    >
      {children}
    </button>
  )
}

/** How long the clear button stays armed before it goes quiet again. */
const ARMED_MS = 5000

/**
 * What is kept on this device: reset the switches above, or forget the lot
 * (lib/stored.js).
 *
 * Clearing takes two clicks and has no undo; one click is the click made by
 * accident on the way to Close. Armed, it disarms after a few seconds rather
 * than staying loaded for whoever opens the panel next.
 *
 * The warning replaces the line already there instead of appearing under the
 * button, so nothing moves as it arrives. It names everything that goes,
 * quiz answers included: they live on the machine, and the wipe reaches them
 * through lib/stored.js.
 */
function StorageFooter() {
  const [asking, setAsking] = useState(false)

  useEffect(() => {
    if (!asking) return undefined
    const timer = setTimeout(() => setAsking(false), ARMED_MS)
    return () => clearTimeout(timer)
  }, [asking])

  return (
    <div className="pt-1 border-t border-[var(--border)] space-y-2">
      {/* Above the line that changes, so that the warning growing from one line
          to three cannot move the button somebody is reaching for. */}
      <div className="flex items-center justify-end gap-2">
        <FooterButton onClick={resetSettings}>Reset settings</FooterButton>
        <FooterButton
          danger={asking}
          title="Settings, remembered choices, recent searches, the best streak and every quiz answer"
          onClick={() => (asking ? forgetSaved() : setAsking(true))}
        >
          {asking ? 'Sure? Clear it all' : 'Clear saved data'}
        </FooterButton>
      </div>

      <p aria-live="polite" className="type-small text-[var(--text-faint)] leading-snug">
        {asking
          ? 'Settings, what you last chose on each tab, recent searches, your best '
            + 'streak, and every quiz answer, so Review empties too.'
          : 'Kept on this device.'}
      </p>
    </div>
  )
}

function Setting({ setting }) {
  const value = useSetting(setting.key)
  const id = `setting-${setting.key}`
  // A switch is one control and takes the label; a choice is a row of them and
  // carries its own group label, so pointing a second one at it would say the
  // name twice.
  const Name = setting.type === 'switch' ? 'label' : 'span'

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between gap-3">
        <Name
          htmlFor={setting.type === 'switch' ? id : undefined}
          className="text-sm font-medium text-[var(--text)]"
        >
          {setting.label}
        </Name>
        {setting.type === 'switch' ? (
          <Switch id={id} setting={setting} value={value} />
        ) : (
          <Segmented
            label={setting.label}
            options={setting.options}
            value={value}
            onChange={(chosen) => setSetting(setting.key, chosen)}
            accent="var(--primary)"
          />
        )}
      </div>

      <p id={`${id}-help`} className="type-small text-[var(--text-faint)] leading-snug">
        {setting.help}
      </p>
    </div>
  )
}

// Reference list copy, in one place.
const REFS = {
  title: 'References',
  intro: 'Every source an answer can come from.',
  pending: 'Loading…',
  error: 'Backend unreachable; list not loaded.',
  noLink: 'No public copy',
}

/** Host of a URL, shown instead of the full address. */
const hostOf = (url) => new URL(url).hostname.replace(/^www\./, '')

/**
 * Every source the app rests on: name, trust level, one line, link.
 * Wording lives in data/sources.json; trust wording in lib/confidence.js.
 */
function SourceList() {
  const { sources, isPending, isError } = useSources()

  return (
    <Disclosure
      tone="strong"
      className="border-t border-[var(--border)] pt-4"
      label={
        <>
          {REFS.title}
          {sources.length > 0 && (
            <span className="text-[var(--text-faint)] font-normal"> · {sources.length}</span>
          )}
        </>
      }
    >
      <p className="type-small text-[var(--text-faint)] mt-2">{REFS.intro}</p>
      {isPending && <p className="type-small text-[var(--text-faint)] mt-3">{REFS.pending}</p>}
      {isError && <p className="type-small text-[var(--warn)] mt-3">{REFS.error}</p>}

      <ul className="mt-3 space-y-3">
        {sources.map((source) => (
          <SourceRow key={source.key} source={source} />
        ))}
      </ul>
    </Disclosure>
  )
}

function SourceRow({ source }) {
  const level = levelOf(source)
  const faint = 'type-small text-[var(--text-faint)] leading-snug'

  return (
    <li className="space-y-0.5">
      <div className="flex items-baseline justify-between gap-2 flex-wrap">
        <span className="text-sm text-[var(--text)]">{source.label}</span>
        <span className="type-small shrink-0" style={{ color: level.color }}>{level.say}</span>
      </div>
      <p className={faint} title={source.detail}>{source.where || source.detail}</p>
      {source.url ? (
        <a
          href={source.url}
          target="_blank"
          rel="noreferrer noopener"
          className="type-small text-[var(--text-dim)] underline underline-offset-2
            hover:text-[var(--text)] transition-colors"
        >
          {hostOf(source.url)}
        </a>
      ) : (
        <p className={`${faint} italic`}>{REFS.noLink}</p>
      )}
    </li>
  )
}

function Switch({ id, setting, value }) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={value}
      aria-describedby={`${id}-help`}
      onClick={() => setSetting(setting.key, !value)}
      className={`relative w-10 h-5 rounded-full border transition-colors shrink-0
        ${value
          ? 'bg-[var(--primary)] border-[var(--primary)]'
          : 'bg-[var(--surface-hi)] border-[var(--border)]'}`}
    >
      <span
        aria-hidden="true"
        className={`absolute top-0.5 w-3.5 h-3.5 rounded-full bg-[var(--bg)] transition-all
          ${value ? 'left-[1.375rem]' : 'left-0.5'}`}
      />
    </button>
  )
}

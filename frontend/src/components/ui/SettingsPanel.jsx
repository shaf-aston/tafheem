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
import { useEffect, useRef, useState } from 'react'

import { SETTINGS, resetSettings, setSetting, useSetting } from '../../lib/settings'
import { levelOf } from '../../lib/confidence'
import { forgetSaved } from '../../lib/stored'
import { useSources } from '../../lib/useSources'

import Disclosure from './Disclosure'
import Segmented from './Segmented'

export default function SettingsPanel({ open, onClose }) {
  const dialog = useRef(null)

  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (open && !element.open) element.showModal()
    if (!open && element.open) element.close()
  }, [open])

  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      // A click that lands on the dialog itself is a click on the backdrop:
      // every real control sits inside the box below.
      onClick={(e) => e.target === dialog.current && onClose()}
      aria-labelledby="settings-title"
      className="m-auto p-0 bg-transparent max-w-[min(28rem,92vw)] w-full"
    >
      <div
        // Scrolls as one box. The source list below can run past the screen,
        // and giving it its own scroller would leave two bars side by side.
        className="rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)]
          p-5 space-y-5 max-h-[88vh] overflow-y-auto"
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

        <div className="space-y-5">
          {SETTINGS.map((setting) => (
            <Setting key={setting.key} setting={setting} />
          ))}
        </div>

        <SourceList />

        <a
          href="/welcome"
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
            + 'streak, and every quiz answer, so Mistakes empties too.'
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

/**
 * Everything the app is built on, in one place.
 *
 * The line at the foot of a tab says what that tab reads. This is the whole
 * list, for the reader who wants to know once what the app rests on: what each
 * source is in plain words, how far it can be trusted, where it physically
 * lives, and a link to the thing itself where there is one to give.
 *
 * Closed by default, it is reference, not a setting, and it is long. Kept
 * inside Settings rather than given a page of its own because it is read once
 * and then rarely, and a sixth tab for it would cost every reader screen space
 * for something most of them look at twice.
 */
function SourceList() {
  const { sources, isPending, isError } = useSources()

  return (
    <Disclosure
      tone="strong"
      className="border-t border-[var(--border)] pt-4"
      label={
        <>
          References
          {sources.length > 0 && (
            <span className="text-[var(--text-faint)] font-normal"> · {sources.length}</span>
          )}
        </>
      }
    >
      <p className="type-small text-[var(--text-faint)] leading-snug mt-2">
        Every place an answer in this app can come from. Nothing is shown without one.
      </p>

      {isPending && (
        <p className="type-small text-[var(--text-faint)] mt-3">Asking the backend…</p>
      )}

      {isError && (
        <p className="type-small text-[var(--warn)] mt-3">
          Couldn&rsquo;t reach the backend, so this list can&rsquo;t be shown. It is not
          empty. It is unread.
        </p>
      )}

      <ul className="mt-3 space-y-3">
        {sources.map((source) => (
          <SourceRow key={source.key} source={source} />
        ))}
      </ul>
    </Disclosure>
  )
}

/** One source: what it is, how far to trust it, where it lives, and a link. */
function SourceRow({ source }) {
  const level = levelOf(source)

  return (
    <li className="space-y-1">
      <div className="flex items-baseline justify-between gap-2 flex-wrap">
        <span className="text-sm text-[var(--text)]">{source.label}</span>
        <span className="type-small shrink-0" style={{ color: level.color }}>
          {level.say}
        </span>
      </div>

      {/* Two sentences with two jobs, and this is the one page with room for
          both. `where` says where the thing physically lives. `detail` says what
          it is and how far it can be trusted, for the sources that have been
          measured it carries the numbers, and those were reaching nobody while
          this row showed only one of the two.

          Skipped where it is shorter than `where`: for most sources `detail` is
          the short phrase written for a badge tooltip, and printing it under a
          fuller sentence says the same thing twice. Length is a proxy for that,
          not a rule about writing, a `detail` that grows past its `where` has
          stopped being a badge phrase. */}
      <p className="type-small text-[var(--text-faint)] leading-snug">
        {source.where || source.detail}
      </p>

      {source.where && source.detail?.length > source.where.length && (
        <p className="type-small text-[var(--text-faint)] leading-snug">
          {source.detail}
        </p>
      )}

      {source.url ? (
        <a
          href={source.url}
          target="_blank"
          rel="noreferrer noopener"
          className="type-small text-[var(--text-dim)] underline underline-offset-2
            hover:text-[var(--text)] transition-colors break-all"
        >
          {source.url}
        </a>
      ) : (
        // Saying why there is no link matters: a missing address here means
        // "there is nothing public to point at", never "we lost track of it".
        <p className="type-small text-[var(--text-faint)] italic">
          Nothing public to link to. It lives on this machine or in print.
        </p>
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

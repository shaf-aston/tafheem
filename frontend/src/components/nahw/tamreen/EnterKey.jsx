// The key printed on the button it fires, so the shortcut is learnt where it is
// used rather than from a line of hints.
const EnterKey = () => (
  <kbd aria-hidden="true"
    className="px-1.5 py-0.5 rounded type-tiny font-semibold leading-none bg-[var(--bg)]/25 border border-current/30">
    Enter ↵
  </kbd>
)

export default EnterKey

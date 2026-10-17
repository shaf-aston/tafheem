// How a checked option looks, and the word printed beside it.
export const STATUS_CLASS = {
  ok: 'border-[var(--success)] text-[var(--success)]',
  bad: 'border-[var(--danger)] text-[var(--danger)]',
  miss: 'border-dotted border-2 border-[var(--danger)] text-[var(--danger)]',
  '': 'border-[var(--border)] text-[var(--text)]',
}

export const MARK_LABEL = { ok: 'Right', bad: 'Not true', miss: 'You missed this', '': '' }

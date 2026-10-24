import { shareLink } from './tabUrl'
import { COPY_RESET_MS, useMoment } from '../hooks/useMoment'

/**
 * The header's tools (lib/nav/tools.js) as they stand this moment. A tool that just
 * worked shows its `done` look for a moment. A tool with a `tab` opens it with
 * `go` (App's switchTab).
 *
 * `run[id]` presses a tool, `now(tool)` is the tool in its current look,
 * `staysOpen(tool)` says the More sheet should stay up after a press, and
 * `said` is what a screen reader hears of the last press, or null.
 */
export function useTools(tools, go) {
  const [doneTool, setDoneTool] = useMoment(COPY_RESET_MS)
  const run = {
    copyLink: () => navigator.clipboard.writeText(shareLink()).then(() => setDoneTool('copyLink'), () => {}),
    ...Object.fromEntries(tools.filter((tool) => tool.tab).map((tool) => [tool.id, () => go(tool.tab)])),
  }
  const now = (tool) => (doneTool === tool.id ? { ...tool, ...tool.done } : tool)
  // Pressed in the More sheet, a tool with something to show next keeps the sheet open.
  const staysOpen = (tool) => Boolean(tool.done)
  const said = doneTool ? now(tools.find((tool) => tool.id === doneTool)).aria : null
  return { run, now, staysOpen, said }
}

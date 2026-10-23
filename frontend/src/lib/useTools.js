import { shareLink } from './tabUrl'
import { COPY_RESET_MS, useMoment } from './useMoment'

/**
 * The header's tools (lib/tools.js) as they stand this moment. A tool that just
 * worked shows its `done` look for a moment. `open.map` opens the map, the one
 * tool whose work is the shell's.
 *
 * `run[id]` presses a tool, `now(tool)` is the tool in its current look,
 * `staysOpen(tool)` says the More sheet should stay up after a press, and
 * `said` is what a screen reader hears of the last press, or null.
 */
export function useTools(tools, open) {
  const [doneTool, setDoneTool] = useMoment(COPY_RESET_MS)
  const run = {
    copyLink: () => navigator.clipboard.writeText(shareLink()).then(() => setDoneTool('copyLink'), () => {}),
    map: open.map,
  }
  const now = (tool) => (doneTool === tool.id ? { ...tool, ...tool.done } : tool)
  // Pressed in the More sheet, a tool with something to show next keeps the sheet open.
  const staysOpen = (tool) => Boolean(tool.done)
  const said = doneTool ? now(tools.find((tool) => tool.id === doneTool)).aria : null
  return { run, now, staysOpen, said }
}

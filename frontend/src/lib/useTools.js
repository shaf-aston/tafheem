import { startOver } from './journey'
import { shareLink } from './tabUrl'
import { ARMED_MS, COPY_RESET_MS, useMoment } from './useMoment'

/**
 * The header's tools (lib/tools.js) as they stand this moment. A tool that just
 * worked shows its `done` look for a moment; one with an `armed` look asks once
 * before it acts, its first click arming it until that runs out. `open.map`
 * opens the map, the one tool whose work is the shell's.
 *
 * `run[id]` presses a tool, `now(tool)` is the tool in its current look,
 * `staysOpen(tool)` says the More sheet should stay up after a press, and
 * `said` is what a screen reader hears of the last press, or null.
 */
export function useTools(tools, open) {
  const [doneTool, setDoneTool] = useMoment(COPY_RESET_MS)
  const [armedTool, setArmedTool] = useMoment(ARMED_MS)
  const armedFirst = (id, act) => () => (armedTool === id ? act() : setArmedTool(id))
  const run = {
    startOver: armedFirst('startOver', startOver),
    copyLink: () => navigator.clipboard.writeText(shareLink()).then(() => setDoneTool('copyLink'), () => {}),
    map: open.map,
  }
  const now = (tool) => (
    doneTool === tool.id ? { ...tool, ...tool.done } : armedTool === tool.id ? { ...tool, ...tool.armed } : tool
  )
  // Pressed in the More sheet, a tool with something to show next keeps the sheet open.
  const staysOpen = (tool) => tool.done || (tool.armed && armedTool !== tool.id)
  const last = doneTool || armedTool
  const said = last ? now(tools.find((tool) => tool.id === last)).aria : null
  return { run, now, staysOpen, armed: armedTool, said }
}

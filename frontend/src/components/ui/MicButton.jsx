import { useEffect, useRef, useState } from 'react'
import { listen } from '../../api'
import config from '../../dictation.json'
import { watchForVoice } from '../../lib/dictation'
import { canRecord, openMicrophone } from '../../lib/microphone'
import { useSetting } from '../../lib/settings'
import MicMark from './MicMark'

/**
 * Record a few seconds, and hand back what was said.
 *
 * One button, used by every box you can speak into, so recording works the same
 * way everywhere and only this file knows how a browser records. The caller
 * decides what the words are for: the Qur'an tab asks for the ayahs too, Daleel
 * just searches the words.
 *
 * The mark on it is the capsule microphone, which is what dictation looks
 * like everywhere in this app; MicMark owns its shape and its motion, this file
 * only says which of the three states it is in.
 *
 * Four states, and each says something different, because "nothing happened" is
 * the one thing a microphone must never look like:
 *   idle       press to speak
 *   recording  it is listening, press again to stop
 *   thinking   it is working out what you said
 *   refused    the browser would not give up the microphone, and why
 *
 * Nothing is recorded until it is pressed, and the microphone is released the
 * moment it stops: a page that keeps a live microphone open is a page nobody
 * should have to trust. It also stops itself after a quiet stretch
 * (dictation.json), so a press by mistake does not leave it listening.
 *
 * It counts the seconds while it records, and that is not decoration. Pressing
 * to start and pressing to stop looks the same as holding to talk, so people
 * let go after a third of a second and get told nothing was heard; the real
 * recordings this fixed were 0.3 and 0.78 seconds long. A number climbing on
 * screen is what says the thing is still listening. The number sits under the
 * button rather than beside it, so the box it belongs to does not shrink when
 * recording starts; the colour already says the rest.
 */
export default function MicButton({ onHeard, match = false, accent, title = 'Recite' }) {
  // Falls back to the theme's own colour, so a caller that gives no accent gets
  // a button that is still visible while recording rather than a white-on-white one.
  const live = accent || 'var(--primary)'
  const [state, setState] = useState('idle')
  const fusha = useSetting('fusha')
  const [problem, setProblem] = useState('')
  const recorder = useRef(null)
  const chunks = useRef([])
  const began = useRef(0)
  // Whether a voice was heard at all this recording. Set by the level meter.
  const spoke = useRef(false)
  const [seconds, setSeconds] = useState(0)

  // The seconds on screen while it records. Cleared the moment it stops, so a
  // stopped button never sits there showing a number that is no longer moving.
  useEffect(() => {
    if (state !== 'recording') return undefined
    const tick = setInterval(() => setSeconds((was) => was + 1), 1000)
    return () => clearInterval(tick)
  }, [state])

  // Whatever happens, do not leave the microphone on when this disappears.
  useEffect(() => () => {
    const live = recorder.current
    if (live && live.state !== 'inactive') live.stop()
    live?.stream?.getTracks().forEach((track) => track.stop())
  }, [])

  async function start() {
    setProblem('')
    if (!canRecord()) {
      setState('refused')
      setProblem('This browser cannot record.')
      return
    }
    try {
      const stream = await openMicrophone()
      const made = new MediaRecorder(stream)
      const stopWatching = watchForVoice(stream, {
        onVoice: () => { spoke.current = true },
        onQuiet: () => made.state === 'recording' && made.stop(),
      })
      chunks.current = []
      made.ondataavailable = (event) => { if (event.data.size) chunks.current.push(event.data) }
      made.onstop = async () => {
        stopWatching()
        stream.getTracks().forEach((track) => track.stop())
        const held = (Date.now() - began.current) / 1000

        // Answered before the recording is sent. A third of a second holds no
        // word, and sending it spends a second of the reader's time to be told
        // something this side already knew.
        if (held < config['too-short-s']) {
          setState('refused')
          setProblem('That was too quick. Press it, say the word, then press it again.')
          return
        }
        // Stopped by the quiet, with no voice heard in all that time. Only the
        // self-stop is refused here: a reader who pressed stop themselves may
        // simply speak softly, and their recording is always sent.
        if (!spoke.current && held >= config['quiet-stop-s']) {
          setState('refused')
          setProblem('Nothing was heard. Try again, closer to the microphone.')
          return
        }

        setState('thinking')
        try {
          const heard = await listen(new Blob(chunks.current, { type: made.mimeType }), { match, fusha })
          // Nothing heard is answered here rather than passed on. It is the
          // ordinary result of a quiet room, and every box this button sits in
          // would otherwise show its own "nothing matched", which blames what
          // was typed for something the microphone did.
          if (!heard.text) {
            setState('refused')
            setProblem('Nothing was heard. Try again, closer to the microphone.')
            return
          }
          onHeard(heard)
          setState('idle')
        } catch (error) {
          setState('refused')
          setProblem(error?.response?.data?.detail || 'Could not make that out.')
        }
      }
      made.start()
      recorder.current = made
      began.current = Date.now()
      spoke.current = false
      setSeconds(0)
      setState('recording')
    } catch {
      setState('refused')
      setProblem('The microphone was not allowed.')
    }
  }

  function stop() {
    if (recorder.current?.state === 'recording') recorder.current.stop()
  }

  const recording = state === 'recording'
  const busy = state === 'thinking'
  const label = recording ? 'Stop recording' : busy ? 'Working out what you said' : title

  return (
    <div className="flex items-center gap-2">
      <span className="relative shrink-0 grid place-items-center">
        {recording && (
          <span
            aria-hidden="true"
            className="mic-ring absolute inset-0 rounded-full border-2"
            style={{ borderColor: live }}
          />
        )}
        <button
          type="button"
          onClick={recording ? stop : start}
          disabled={busy}
          aria-label={label}
          title={label}
          aria-pressed={recording}
          style={recording ? { backgroundColor: live, borderColor: live } : undefined}
          className={`mic-host relative w-10 h-10 grid place-items-center rounded-full border
            transition-colors duration-[calc(var(--motion-instant-ms)*1ms)]
            ${recording
              ? 'text-white border-transparent shadow-sm'
              : 'border-[var(--border)] text-[var(--text-faint)] hover:text-[var(--text)] hover:border-[var(--text-faint)]'}
            ${busy ? 'opacity-70 cursor-wait' : ''}`}
        >
          <MicMark state={recording ? 'recording' : busy ? 'thinking' : 'idle'} />
        </button>
        {recording && (
          <span
            aria-hidden="true"
            className="absolute top-full mt-0.5 type-tiny text-[var(--text-faint)] tabular-nums pointer-events-none"
          >
            {seconds}s
          </span>
        )}
      </span>
      {!recording && problem && (
        <span className="type-tiny text-[var(--text-faint)]">{problem}</span>
      )}
    </div>
  )
}

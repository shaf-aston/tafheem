/**
 * When a recording should stop itself. Pure, so it is tested without a microphone.
 * ui/MicButton.jsx meters the sound; this decides what the meter means.
 */
import config from '../dictation.json'

/**
 * Loud enough to be a voice rather than the room.
 *
 * Against the room, not against a number. How loud a voice measures depends on
 * the microphone, how far away it is and how the browser is levelling it, and
 * one fixed number cannot be right for a hissy laptop in a kitchen and a good
 * microphone in a silent room at the same time. It was one number, and
 * somebody reciting softly sat under it: nothing they said counted as a voice,
 * so nothing was sent to be read, and the page reported an empty recitation.
 *
 * `room` is the quietest level heard so far on this microphone. Leave it out
 * and only the floor applies, which is what a caller with nothing to compare
 * against yet should do.
 */
export const isVoice = (level, room = null) =>
  level > Math.max(config['voice-level'], room == null ? 0 : room * config['over-room'])

/**
 * How long silence may run before the recording ends.
 *
 * Two waits, because silence means two different things. After a voice it is
 * someone who has finished, so it ends quickly. Before any voice it is someone
 * still gathering the word, and cutting them off there is worse than waiting.
 *
 * A patient listener, reciting, only ever uses the long wait: a reciter breathes
 * between ayahs for longer than the short one, and the page was ending the
 * whole recitation at the first such breath. The long wait is still there for
 * a microphone left on.
 */
export const quietLimitMs = (heardVoice, patient = false) =>
  (heardVoice && !patient ? config['after-speech-s'] : config['quiet-stop-s']) * 1000

/**
 * How many of the newest samples one read judges (judge-s), never less than
 * what arrived since the last read, so nothing falls between two reads.
 */
export const freshSamples = (sampleRate, held) =>
  Math.min(held, Math.ceil(sampleRate * Math.max(config['judge-s'], config['level-check-ms'] / 1000 * 1.5)))

/**
 * Watch a live microphone and say when a voice is heard and when it has gone.
 *
 * Here rather than in the button because two things record now: the button, for
 * one word, and reciting, for as long as somebody wants. Both have to stop a
 * microphone left on by mistake, and one idea of "nobody is speaking" is enough
 * for the app.
 *
 * `onQuiet` fires on every read past the limit, not once, so a caller that
 * ignores the first one still hears the next. Returns the function that stops
 * reading and lets the audio go.
 */
export function watchForVoice(stream, { onVoice, onQuiet, patient = false }) {
  const context = new AudioContext()
  const meter = context.createAnalyser()
  // The largest window the browser allows, about 0.7 seconds. The default is
  // 46 milliseconds, so a read every quarter second saw a twentieth of what
  // was said and one word landed between two reads.
  meter.fftSize = 32768
  context.createMediaStreamSource(stream).connect(meter)
  const samples = new Uint8Array(meter.fftSize)
  let lastVoice = Date.now()
  let heardVoice = false
  // What this microphone sounds like with nobody speaking: the quietest read
  // so far. It only ever goes down, so a first read taken mid-word starts it
  // too high and the first real gap settles it.
  let room = null
  const timer = setInterval(() => {
    meter.getByteTimeDomainData(samples)
    // Only the newest judge-s of sound, which sits at the end. Judging the
    // whole window kept a voice "heard" for 0.7 seconds after it stopped, so
    // every pause was noticed that much late.
    const fresh = samples.subarray(-freshSamples(context.sampleRate, samples.length))
    // Samples sit around 128 in silence; how far the loudest one strays is the level.
    const level = fresh.reduce((top, s) => Math.max(top, Math.abs(s - 128)), 0) / 128
    room = room == null ? level : Math.min(room, level)
    if (isVoice(level, room)) {
      lastVoice = Date.now()
      heardVoice = true
      onVoice()
    } else if (Date.now() - lastVoice >= quietLimitMs(heardVoice, patient)) {
      onQuiet()
    }
  }, config['level-check-ms'])
  return () => {
    clearInterval(timer)
    context.close()
  }
}

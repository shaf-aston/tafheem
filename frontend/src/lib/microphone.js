/**
 * Opening the microphone, and asking the browser to clean up what it hears.
 *
 * One job. It does not know what is being recorded or who wants it; both the
 * button that takes one spoken word and the page that follows a recitation
 * open the microphone through here, so there is one idea of what a microphone
 * sounds like in this app and not two that drift apart.
 *
 * What is asked for, and why each one
 * -----------------------------------
 * Every browser carries this work already, done properly, on the sound before
 * it ever reaches us, and it costs nothing to ask for. Asked for by name
 * because the plain `{ audio: true }` this used to send leaves each of them to
 * the browser's own mood.
 *
 *   levelled       the browser raises a quiet speaker and holds a loud one
 *                  down, continuously. Somebody reciting softly, or sitting
 *                  back from the microphone, was recording sound so small that
 *                  the page never counted it as a voice at all and sent
 *                  nothing to be read: recited, and nothing came back.
 *   noise cut      steady room sound, a fan, traffic, is taken out and the
 *                  voice left. Which is also the honest answer to separating a
 *                  reciter from a noisy room: this is what is free and what
 *                  works on steady noise. Telling two people apart in one
 *                  recording is a different and much larger thing, and nothing
 *                  here claims to do it.
 *   no echo cut    that one is for phone calls. It listens for what the
 *                  speakers are playing and subtracts it, and a recitation
 *                  playing back on the same machine, which is how this app is
 *                  tested, is exactly what it would subtract.
 *   one channel    a voice is one voice; two copies of it is sound to carry
 *                  and upload for nothing.
 *
 * A browser that does not know one of these ignores it, which is why they are
 * asked for plainly rather than through `advanced` constraints that fail the
 * whole request when one is unsupported.
 */

/** What every microphone in this app is opened with. */
export const asked = {
  audio: {
    autoGainControl: true,
    noiseSuppression: true,
    echoCancellation: false,
    channelCount: 1,
  },
}

/** True when this browser can record at all. Ask before opening. */
export const canRecord = () => Boolean(navigator.mediaDevices?.getUserMedia)

/**
 * The microphone, cleaned up. Throws exactly what getUserMedia throws, so the
 * caller still tells "not allowed" from "no microphone" in its own words.
 *
 * A browser that refuses the settings rather than ignoring them still gets a
 * microphone: the plain request is tried once more, because recording at all
 * matters more than recording well.
 */
export const openMicrophone = async () => {
  try {
    return await navigator.mediaDevices.getUserMedia(asked)
  } catch (error) {
    if (error?.name !== 'OverconstrainedError' && error?.name !== 'TypeError') throw error
    return navigator.mediaDevices.getUserMedia({ audio: true })
  }
}

/**
 * A recorder for an open microphone. Named here so the reciting session can be
 * handed a scripted one in tests: the browser's own is the only other kind.
 */
export const createRecorder = (stream) => new MediaRecorder(stream)

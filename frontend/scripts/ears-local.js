/**
 * The local ear: posts a recording to a running backend and returns what it heard.
 *
 * A plain module, not part of ears.test.js. `npm test` is a bare `vitest run`
 * that already collects every scripts/*.test.js file; importing this function
 * from inside the benchmark's own test file would register that file's
 * describe block a second time, running the 36-ayah benchmark twice for
 * anyone with the cloud keys set.
 *
 * `match=true` forces Arabic server-side, the same forced language Groq's ear
 * is given; `fusha=false` sends no register hint, matching Groq's call.
 */
export const localHears = (url) => async (mp3) => {
  const form = new FormData()
  form.append('audio', new Blob([mp3], { type: 'audio/mpeg' }), 'a.mp3')
  const got = await fetch(`${url}?match=true&fusha=false`, { method: 'POST', body: form })
  const body = await got.json()
  if (!got.ok) throw new Error(body.detail || String(got.status))
  return body.text ?? ''
}

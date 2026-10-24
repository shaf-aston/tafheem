import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { analyzeMorphology, analyzeMeaning, conjugateForm } from '../../api'
import { useArrival, useArrivalEffect, useHeld } from '../useArrival'
import { useSlowPending } from '../useSlowPending'

/**
 * What the Sarf tab is asking about and what came back: the word in the box,
 * the three requests (the word, a باب swap, the meaning) and the table they add
 * up to. `incoming`, `arrival` and `onVisit` are the panel's own props.
 * `edit` is a keystroke or a heard word, `submit` asks, `chooseForm` swaps the
 * باب, `pickPreset` takes a preset, `reset` empties the box.
 */
export function useSarf({ incoming, arrival, onVisit }) {
  const [word, setWord] = useState(incoming ?? '')
  // Preset data shows instantly; the API fills in the table behind it.
  const [preview, setPreview] = useState(null)
  // Which verb form the table is for. The word alone cannot say which Form I
  // baab a verb takes, so the reader chooses and the table is rebuilt.
  const [form, setForm] = useState('')

  // A word that came back is a place reached, so the trail and the back
  // arrow can carry it, the same as the Dictionary. See lib/journey.js.
  const mutation = useMutation({
    mutationFn: analyzeMorphology,
    onSuccess: (_, { word: asked }) => onVisit?.(asked),
  })
  // A باب switch is its own, much smaller question, so it is its own request;
  // the word's answer is not thrown away and asked for again to change a table.
  const swap = useMutation({ mutationFn: conjugateForm })
  // The meaning can come from a live AI call, which can take seconds; so it is
  // its own request, fired once the table above is already on screen instead of
  // holding the whole page up for it.
  const meaning = useMutation({ mutationFn: analyzeMeaning })

  // A new word answers everything again, so a swap made for the old word goes
  // with it.
  const clear = () => { mutation.reset(); swap.reset(); meaning.reset() }

  // The word's answer is quick enough that saying "waiting" and unsaying it
  // was a flash rather than news, so the waiting is only announced once it has
  // actually lasted. The button is still refused a second press at once, below.
  const waiting = useSlowPending(mutation.isPending)

  // A word arriving: handed over from another tab, or the back arrow returning
  // to one. App no longer remounts the panel for it, that remount was the
  // screen flash (see lib/useArrival).
  const { arrived, returning } = useArrival(arrival, mutation.isPending)

  // Through a return the last table stays up until the next one lands, so the
  // page keeps its height rather than collapsing for the length of a request.
  const base = useHeld(mutation.data ?? preview, returning)
  // The AI is asked for the meaning, and it answers with a verb class too. That
  // class is a guess and the rules' own answer is not: asked about دعو the AI
  // said "Sahih (Salim)" where the rules say ناقص, and spreading the whole reply
  // put the guess on screen. It may only fill the gap, never overwrite.
  const guessed = meaning.data?.meaning ? meaning.data : null
  const data = base && {
    ...base,
    ...swap.data,
    meaning: guessed?.meaning ?? base.meaning,
    meaning_source: guessed?.meaning_source ?? base.meaning_source,
    verb_class: base.verb_class ?? meaning.data?.verb_class,
  }

  // Fires right after the table lands, not on every باب swap; the word hasn't
  // changed, so asking again would just repeat the same network call.
  const { mutate: fetchMeaning } = meaning
  useEffect(() => {
    if (mutation.data && !mutation.data.meaning) fetchMeaning({ word: mutation.data.word })
  }, [mutation.data, fetchMeaning])

  // The box and the باب follow the word during the render.
  if (arrived && incoming) {
    setWord(incoming)
    setPreview(null)
    setForm('')
  }

  // And it is conjugated, so the journey ends in an answer rather than in a
  // filled-in box. The previous word's swap and meaning go with it.
  useArrivalEffect(arrival, () => {
    if (!incoming) return
    mutation.reset()
    swap.reset()
    meaning.reset()
    mutation.mutate({ word: incoming })
  })

  // Typed or heard, a changed word drops the old answer and the old باب.
  const edit = (text) => { setWord(text); setPreview(null); setForm(''); clear() }

  const submit = (text, nextForm = form) => {
    const trimmed = (text ?? word).trim()
    if (!trimmed) return
    setWord(trimmed)
    clear()
    mutation.mutate({ word: trimmed, form: nextForm || undefined })
  }

  const chooseForm = (id) => {
    setForm(id)
    // With a root in hand the rules can rebuild the table on their own; without
    // one there is nothing to conjugate from, so the word is analysed again.
    if (data?.root) swap.mutate({ root: data.root, form: id })
    else submit(word, id)
  }

  // A failed baab swap is answered right beside the picker that caused it, not
  // at the top of the page; the top alert is left for the word lookup only.
  const retrySwap = () => swap.mutate({ root: data.root, form })

  const pickPreset = (preset) => {
    // The old word's finished table would otherwise stay on screen underneath
    // the new preset's facts, so it goes first.
    clear()
    setWord(preset.arabic)
    setPreview({
      root: preset.root,
      wazn: preset.wazn,
      verb_class: preset.verb_class,
      meaning: preset.meaning,
    })
    mutation.mutate({ word: preset.arabic, form: form || undefined })
  }

  const reset = () => {
    setWord('')
    setPreview(null)
    setForm('')
    clear()
  }

  return {
    word, data, base, waiting, mutation, swap, meaning,
    edit, submit, chooseForm, retrySwap, pickPreset, reset,
  }
}

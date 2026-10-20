/**
 * Which component draws which kind of exercise.
 *
 * The one place an exercise type turns into something on screen. ExerciseHost is
 * the only reader, so a new kind of practice is a new file beside this one and a
 * line here, and no panel or lesson layout is touched. The same list on the
 * backend is backend/services/colloquial/exercises/registry.py; the two must
 * name the same five types.
 *
 * Every renderer is handed the same four things and nothing else:
 *   exercise  the exercise as the API sent it
 *   value     what the learner has entered or picked so far
 *   onChange  hand back the new value
 *   status    '' while answering, then 'right' or 'wrong', and the renderer
 *             becomes read-only rather than being swapped for a different one
 * That contract is what lets a renderer be reused from anywhere, including
 * outside the Colloquial tab.
 */
import ChooseExercise from '../../components/colloquial/exercises/ChooseExercise'
import ReorderExercise from '../../components/colloquial/exercises/ReorderExercise'
import TypedExercise from '../../components/colloquial/exercises/TypedExercise'

export const RENDERERS = {
  reply: TypedExercise,
  fill_blank: TypedExercise,
  translate_to_arabic: TypedExercise,
  choose: ChooseExercise,
  reorder: ReorderExercise,
}

/** What the learner starts with: a picked option is one string, an arrangement a list. */
export const blankValue = (type) => (type === 'reorder' ? [] : '')

/** The component for a type, or null where a unit names a type this build has no
 *  renderer for. Null is drawn as a plain note rather than an empty space, so a
 *  new content type that arrives before its renderer is visible, not silent. */
export const rendererFor = (type) => RENDERERS[type] ?? null

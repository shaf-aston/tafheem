/**
 * What each kind of exercise is: the component that draws it, what the learner
 * starts with, and how an answer is marked.
 *
 * The one place an exercise type turns into behaviour. ExerciseHost is the only
 * reader, so a new kind of practice is a new file beside this one and a line
 * here, and no panel or lesson layout is touched. The same list on the backend
 * is backend/services/colloquial/exercises/registry.py; the two must name the
 * same five types.
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
import { ARRANGED, PICKED, TYPED } from '../../../lib/colloquialAnswer'
import ChooseExercise from './ChooseExercise'
import ReorderExercise from './ReorderExercise'
import TypedExercise from './TypedExercise'

const EXERCISES = {
  reply: { Renderer: TypedExercise, ...TYPED },
  fill_blank: { Renderer: TypedExercise, ...TYPED },
  translate_to_arabic: { Renderer: TypedExercise, ...TYPED },
  choose: { Renderer: ChooseExercise, ...PICKED },
  reorder: { Renderer: ReorderExercise, ...ARRANGED },
}

/** A type's { Renderer, blank, judge }, or null where a unit names a type this build
 *  has none for. Null is drawn as a plain note rather than an empty space, so a new
 *  content type that arrives before its renderer is visible, not silent. */
export const exerciseOf = (type) => EXERCISES[type] ?? null

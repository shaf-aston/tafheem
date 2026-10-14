/**
 * A lessons world's picture, picked by `view` in worlds.json. Each scene is a component of
 * `{ items, world }`: `items` from lib/useLessonWorld.js ({ key, item, status }, status known | learning | new).
 * Shown by ../LessonWorld.jsx (SCENES[world.view]; none = the stage list); styles in styles/growWorlds.css.
 */
import Shelf from './Shelf'
import Sky from './Sky'

export const SCENES = { shelf: Shelf, sky: Sky }

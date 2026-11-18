# Picture boards

A picture board teaches a topic's words on a drawing: tap a place to hear its word (Explore), or hear a
word and tap its place (Test). Every board, whatever it draws, is built and shown the same way.

## What a board is (data)

`lib/colloquial/wordPictures.js` builds a topic's boards from its words; `lib/colloquial/sceneBoards.js`
holds the scene and panel layouts. A board is:

| field | what it is |
|---|---|
| `id`, `label` | the board, as the picker names it |
| `art` | which drawing to put behind it (see below) |
| `view` | `[x, y, w, h]`, the drawing's own units |
| `spots` | the places: a **dot** (`x`, `y`), an **area** (`area: [x, y, w, h]`, a room or a tile), or a **led-out dot** (`to: [x, y]`, a dot set aside on a line where places sit too close to tap apart); each with the `words` it means |

A board is offered only when it places at least `least-picture-words` of the topic's words
(`config/colloquial-display.json`).

## How every board is shown (one pattern)

`WordPicture.jsx` draws every board with the same parts, never a board-specific path:

1. **The drawing**: `Art` picks the drawing by `art` (`BodyArt`, `SceneArt`, `PanelArt`, `ThingArt`,
   `MapArt`); each draws only the boards it knows.
2. **The places** over it: dots and areas, one keyboard Tab stop for the whole picture, arrow keys between places.
3. **The label rail**: the picture is the board's `view` widened by a rail on its right
   (`lib/colloquial/labelRail.js`, `label-rail` in config). A tapped place's word stands in the rail, level
   with the place (a dot's centre, an area's right edge), joined by a thin line (`Callout.jsx`). The rail is
   empty space, so a word never covers the drawing, on any board. In Explore the label is the word's one
   place, with its speaker; in Test it shows a wrong tap's word, in red.
4. **One layout**: the picture beside its controls (picker, Explore/Test, the question) on a wide screen,
   over them on a phone, wherever a board is used: a word topic's Browse or a phrase topic's "See it".

## Adding a board

Add its layout to `sceneBoards.js` (or `wordPictures.js` for a body or a map) and, if it needs a new
drawing, one `Art` component that draws it in the board's `view`. Nothing in `WordPicture.jsx` changes:
places, the label rail, Test and the keyboard come with the pattern.

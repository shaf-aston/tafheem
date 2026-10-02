/**
 * The header's tool buttons, listed once. The header draws each as an icon;
 * `phone: 'more'` hides it on phones and lists it in the More sheet instead.
 * Moving a tool between the bar and More is one word here. What a tool does
 * is App's (`run` names its handler), so this file stays data.
 */
export const TOOLS = [
  {
    id: 'startOver',
    label: 'Start over',
    aria: 'Start over: forget where you have been, your answers and your Grow steps, and reopen this tab clean',
    hint: 'Start over forgets where you have been, your answers and your Grow steps.',
    paths: ['M3 12a9 9 0 1 0 3-6.7', 'M3 4v5h5'],
    phone: 'more',
  },
  {
    id: 'map',
    label: 'Map',
    aria: 'Open the map: a high-level overview',
    dialog: true,
    paths: ['M9 3 3 5.5v15L9 18l6 2.5L21 18V3l-6 2.5L9 3Z', 'M9 3v15M15 5.5v15'],
    phone: 'more',
  },
]

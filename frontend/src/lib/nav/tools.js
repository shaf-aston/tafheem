/**
 * The header's tool buttons, listed once. The header draws each as an icon;
 * `phone: 'more'` hides it on phones and lists it in the More sheet instead;
 * `phone: 'both'` keeps it on the phone's bar and lists it in More too.
 * Moving a tool between the bar and More is one word here. What a tool does
 * is App's (`run` names its handler), so this file stays data. `done` is what a
 * tool shows for a moment after it worked. Start over is not here: it lives
 * with Delete account, in the profile's danger zone.
 */
export const TOOLS = [
  {
    id: 'copyLink',
    label: 'Copy link',
    aria: 'Copy a link to exactly this page, with what is open on it',
    paths: ['M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7', 'M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7'],
    // What the button shows for a moment after it worked. A tool with one keeps
    // the More sheet open when pressed there, so the result is seen.
    done: { label: 'Link copied', aria: 'Link copied', paths: ['M20 6 9 17l-5-5'] },
    phone: 'more',
  },
  {
    id: 'map',
    label: 'Map',
    aria: 'Open the map: a high-level overview',
    dialog: true,
    paths: ['M9 3 3 5.5v15L9 18l6 2.5L21 18V3l-6 2.5L9 3Z', 'M9 3v15M15 5.5v15'],
    phone: 'both',
  },
]

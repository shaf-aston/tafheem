/**
 * A small line picture for a hadith book's topic, so a book is found again by
 * its shape before its name is read. Which topic a book is comes from
 * hadith.json (lib/hadithGrade topicOf); this file only draws. Stroke takes
 * currentColor, so the caller's text colour (and hover) paints it.
 */
const PATHS = {
  purify: 'M12 3c3 4 6 7 6 11a6 6 0 0 1-12 0c0-4 3-7 6-11z',
  prayer: 'M4 20h16M6 20v-7M18 20v-7M6 13a6 6 0 0 1 12 0M12 7V4M10 20v-4a2 2 0 0 1 4 0v4',
  funeral: 'M7 21V9a5 5 0 0 1 10 0v12M5 21h14M10 11h4',
  fasting: 'M20 14A8 8 0 1 1 10 4a6.5 6.5 0 0 0 10 10z',
  zakat: 'M12 3a9 9 0 1 0 0 18a9 9 0 0 0 0-18zM15 9.5c0-1-1.3-1.8-3-1.8s-3 .8-3 1.8 1.3 1.6 3 2 3 1 3 2-1.3 1.8-3 1.8-3-.8-3-1.8M12 6v12',
  hajj: 'M4 7l8-4 8 4v10l-8 4-8-4zM4 7l8 4 8-4M12 11v10M4 10.5l8 4 8-4',
  quran: 'M3 5h6a3 3 0 0 1 3 3v12a2 2 0 0 0-2-2H3zM21 5h-6a3 3 0 0 0-3 3v12a2 2 0 0 1 2-2h7z',
  faith: 'M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2M12 8a4 4 0 1 0 0 8a4 4 0 0 0 0-8z',
  knowledge: 'M4 20l4-1 11-11a2.1 2.1 0 0 0-3-3L5 16zM14 7l3 3',
  family: 'M4 14a5 5 0 1 0 10 0a5 5 0 1 0-10 0M10 14a5 5 0 1 0 10 0a5 5 0 1 0-10 0',
  trade: 'M5 8h14l-1 12H6zM9 8V6a3 3 0 0 1 6 0v2',
  law: 'M12 4v16M8 20h8M5 7h14M5 7l-3 6a3 3 0 0 0 6 0zM19 7l-3 6a3 3 0 0 0 6 0z',
  jihad: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z',
  food: 'M4 11h16a8 8 0 0 1-16 0zM8 7c0-1 1-1 1-2M12 7c0-1 1-1 1-2M16 7c0-1 1-1 1-2',
  dress: 'M8 4L3 7l2 4 3-1v10h8V10l3 1 2-4-5-3a4 4 0 0 1-8 0z',
  health: 'M5 19c0-8 5-14 15-14 0 10-6 15-14 15M5 19l7-7',
  manners: 'M4 5h16v11H9l-5 4z',
  heart: 'M12 20s-8-5-8-11a4 4 0 0 1 8-1 4 4 0 0 1 8 1c0 6-8 11-8 11z',
  endtimes: 'M6 3h12M6 21h12M7 3c0 6 10 6 10 9s-10 3-10 9M17 3c0 6-10 6-10 9s10 3 10 9',
  people: 'M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.4l-5.3 3 1.2-6-4.5-4.1 6-.7z',
}

/** The timelines' pictures, drawn on a 48 box: bigger, since they sit faint behind a card. */
const BIG_PATHS = {
  moon: 'M34 32A15 15 0 0 1 17 9a15 15 0 1 0 17 23z',
  star: 'M24 5l4.6 14.4L43 24l-14.4 4.6L24 43l-4.6-14.4L5 24l14.4-4.6z',
  book: 'M6 10h15a4 4 0 0 1 3 1.5A4 4 0 0 1 27 10h15v28H27a4 4 0 0 0-3 1.5A4 4 0 0 0 21 38H6zM24 11.5V39',
  mountain: 'M3 39l14-24 8 12 5-7 15 19zM17 15l4 6',
  drop: 'M24 5c8 10 13 16 13 23a13 13 0 0 1-26 0c0-7 5-13 13-23zM18 30a6 6 0 0 0 6 6',
  sun: 'M32 24a8 8 0 1 0-16 0a8 8 0 1 0 16 0zM24 4v6M24 38v6M4 24h6M38 24h6M9.9 9.9l4.2 4.2M33.9 33.9l4.2 4.2M9.9 38.1l4.2-4.2M33.9 14.1l4.2-4.2',
  branch: 'M24 43V13M24 31c-9 0-13-6-13-13 9 0 13 6 13 13zM24 24c9 0 13-6 13-13-9 0-13 6-13 13z',
  dome: 'M9 39V27a15 15 0 0 1 30 0v12zM3 39h42M24 6v6M20 39v-8a4 4 0 0 1 8 0v8',
  hourglass: 'M11 5h26M11 43h26M13 5c0 13 11 13 11 19s-11 6-11 19M35 5c0 13-11 13-11 19s11 6 11 19',
  // A Muslim grave: a mound and a plain rounded headstone, no cross.
  grave: 'M4 42h40M8 42c3-6 29-6 32 0M19 37V16a5 5 0 0 1 10 0v21',
  scales: 'M24 7v33M12 40h24M8 13h32M8 13L2 27a6.5 6.5 0 0 0 12 0zM40 13l-6 14a6.5 6.5 0 0 0 12 0z',
}

/**
 * Nothing for a topic with no picture, so a book no word matched just shows its name.
 * w-5 h-5 unless the caller's className brings its own width.
 */
export default function TopicIcon({ topic, className = '' }) {
  const big = BIG_PATHS[topic]
  const d = big ?? PATHS[topic]
  if (!d) return null
  return (
    <svg
      aria-hidden="true" viewBox={big ? '0 0 48 48' : '0 0 24 24'} fill="none" stroke="currentColor"
      strokeWidth={big ? 1.4 : 1.6} strokeLinecap="round" strokeLinejoin="round"
      className={`shrink-0 ${className.includes('w-') ? '' : 'w-5 h-5'} ${className}`.trim()}
    >
      <path d={d} />
    </svg>
  )
}

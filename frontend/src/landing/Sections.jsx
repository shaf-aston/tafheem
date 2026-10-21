import { accentOf, GROUPS, LISTED } from '../lib/tabs.js'
import ArabicText from '../components/ui/ArabicText.jsx'
import TabGroups from '../components/ui/TabGroups.jsx'
import Tile from '../components/ui/Tile.jsx'
import links from './links.json'

const SHOWN = GROUPS.filter((group) => LISTED.some((tab) => tab.group === group.id))

// Every section of the app, laid out as the All sections menu lays it out: one tap opens that tab.
export default function Sections() {
  return (
    <section className="landing-sections" aria-labelledby="landing-sections-title">
      <div className="wrap">
        <h2 id="landing-sections-title">{links.sections.title}</h2>
        <div className="landing-sections-groups">
          {/* A phone fills each row; a wide screen sets short groups side by side. */}
          <TabGroups groups={SHOWN} tabs={LISTED} className="basis-full lg:basis-auto"
            grid="gap-2 grid-cols-[repeat(auto-fill,minmax(12rem,1fr))] lg:grid-cols-none lg:grid-flow-col lg:auto-cols-[12rem]">
            {(tab, index) => (
              <Tile key={tab.id} as="a" href={`${links.tool}/${tab.id}`} variant="chip" accent={accentOf(tab.id)} style={{ '--i': index }}>
                <span className="flex items-center gap-2 type-ui font-semibold">
                  <span aria-hidden="true" className="w-2.5 h-2.5 rounded-full shrink-0 bg-[var(--c)]" />
                  {tab.label}
                </span>
                <ArabicText size="lg" className="shrink-0 leading-tight text-[var(--c)]">{tab.arabic}</ArabicText>
              </Tile>
            )}
          </TabGroups>
        </div>
      </div>
    </section>
  )
}

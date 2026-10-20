import { accentOf, GROUPS, LISTED } from '../lib/tabs.js'
import ArabicText from '../components/ui/ArabicText.jsx'
import TabGroups from '../components/ui/TabGroups.jsx'
import Tile from '../components/ui/Tile.jsx'
import links from './links.json'

const SHOWN = GROUPS.filter((group) => LISTED.some((tab) => tab.group === group.id))

// Every section of the app, as Home and All sections show them: one tap opens that tab.
export default function Sections() {
  return (
    <section className="landing-sections" aria-labelledby="landing-sections-title">
      <div className="wrap">
        <p className="label">{links.sections.eyebrow}</p>
        <h2 id="landing-sections-title">{links.sections.title}</h2>
        <div className="landing-sections-groups">
          <TabGroups groups={SHOWN} tabs={LISTED} grid="gap-2 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
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

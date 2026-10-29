import { accentOf, GROUPS, LISTED } from '../lib/nav/tabs.js'
import ArabicText from '../components/ui/ArabicText.jsx'
import TabGroups from '../components/ui/TabGroups.jsx'
import Tile from '../components/ui/Tile.jsx'
import { Flag } from '../components/colloquial/CountryMap'
import dialectFile from '../lib/colloquial/dialectsPreview.json'
import links from './links.json'

const SHOWN = GROUPS.filter((group) => LISTED.some((tab) => tab.group === group.id))

// The dialects as one more group: each opens Colloquial on that dialect (lib/colloquial/place.js).
const SPOKEN = [{ id: 'spoken', label: 'Spoken dialects' }]
const DIALECTS = dialectFile.dialects.map((d) => ({ ...d, id: d.key, group: 'spoken' }))

const GRID = 'landing-sections-grid grid grid-cols-[repeat(auto-fill,minmax(13rem,1fr))] lg:grid-cols-none lg:grid-flow-col lg:auto-cols-[13rem]'

// Every section of the app, laid out as the All sections menu lays it out: one tap opens that tab.
export default function Sections() {
  const colloq = accentOf('colloq')
  return (
    <section className="landing-sections" aria-labelledby="landing-sections-title">
      <div className="wrap">
        <h2 id="landing-sections-title">{links.sections.title}</h2>
        <div className="landing-sections-groups">
          {/* A phone fills each row; a wide screen sets short groups side by side. */}
          <TabGroups groups={SHOWN} tabs={LISTED} className="basis-full lg:basis-auto" grid={GRID}>
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
          <TabGroups groups={SPOKEN} tabs={DIALECTS} className="basis-full"
            grid="landing-sections-grid grid grid-cols-[repeat(auto-fill,minmax(13rem,1fr))]">
            {(d, index) => (
              <Tile key={d.key} as="a" href={`${links.tool}/colloq/${d.key}`} variant="chip" accent={colloq} style={{ '--i': index }}>
                <span className="flex items-center gap-2 type-ui font-semibold">
                  <span aria-hidden="true" className="flex shrink-0">{d.countries.slice(0, 1).map((code) => <Flag key={code} code={code} className="h-4" />)}</span>
                  {d.label}
                </span>
                <ArabicText size="lg" className="shrink-0 leading-tight text-[var(--c)]">{d.arabic}</ArabicText>
              </Tile>
            )}
          </TabGroups>
        </div>
      </div>
    </section>
  )
}

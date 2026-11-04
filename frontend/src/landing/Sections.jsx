import { accentOf, GROUPS, LISTED } from '../lib/nav/tabs.js'
import ArabicText from '../components/ui/text/ArabicText.jsx'
import TabGroups from '../components/ui/inputs/TabGroups.jsx'
import Tile from '../components/ui/display/Tile.jsx'
import { CountryIcons, CountryMap } from '../components/colloquial/CountryMap'
import { colorFor } from '../theme'
import dialectFile from '../lib/colloquial/dialectsPreview.json'
import links from './links.json'

const SHOWN = GROUPS.filter((group) => LISTED.some((tab) => tab.group === group.id))

// The dialects as one more group: each opens Colloquial on that dialect (lib/colloquial/place.js).
const SPOKEN = [{ id: 'spoken', label: 'Spoken dialects' }]
const DIALECTS = dialectFile.dialects.map((d) => ({ ...d, id: d.key, group: 'spoken' }))

// Every section of the app, laid out as the All sections menu lays it out: one tap opens that tab.
// The dialects follow as one more group, each drawn as the course picker draws it (CountryMap).
export default function Sections() {
  const colloq = accentOf('colloq')
  const hue = colorFor('tab', 'colloq')
  return (
    <section className="landing-sections" aria-labelledby="landing-sections-title">
      <div className="wrap">
        <h2 id="landing-sections-title">{links.sections.title}</h2>
        <div className="landing-sections-groups">
          {/* One group to a row, every row on the same tile columns, so the groups line up
              down the page: a phone's tiles fill the row, a wide screen's keep one width. */}
          <TabGroups groups={SHOWN} tabs={LISTED}
            grid="gap-2 grid-cols-[repeat(auto-fill,minmax(12rem,1fr))] lg:grid-cols-[repeat(auto-fill,12rem)]">
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
          <TabGroups groups={SPOKEN} tabs={DIALECTS}
            grid="gap-2 grid-cols-2 sm:grid-cols-[repeat(auto-fill,minmax(8rem,1fr))] lg:grid-cols-[repeat(auto-fill,9rem)]">
            {(d, index) => (
              <Tile key={d.key} as="a" href={`${links.tool}/colloq/${d.key}`} variant="chip" accent={colloq} style={{ '--i': index }}
                className="landing-dialect">
                <CountryMap codes={d.countries} cities={d.cities} hue={hue} className="w-full max-w-20 sm:max-w-28" />
                <span className="type-ui font-semibold">{d.label}</span>
                <ArabicText size="lg" className="leading-tight text-[var(--c)]">{d.arabic}</ArabicText>
                <CountryIcons codes={d.countries} most={2} />
              </Tile>
            )}
          </TabGroups>
        </div>
      </div>
    </section>
  )
}

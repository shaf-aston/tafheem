import './landing.css'

import Hero from './Hero.jsx'
import SourcesMarquee from './SourcesMarquee.jsx'
import StoryScroll from './StoryScroll.jsx'
import FolioBand from './FolioBand.jsx'
import SentenceDemo from './SentenceDemo.jsx'
import ClipStrip from './ClipStrip.jsx'
import Counters from './Counters.jsx'
import Finale from './Finale.jsx'
import Footer from './Footer.jsx'
import CursorBlob from './CursorBlob.jsx'

export default function Landing() {
  return (
    <main className="landing-page js">
      <CursorBlob />
      <Hero />
      <SourcesMarquee />
      <StoryScroll />
      <FolioBand />
      <SentenceDemo />
      <ClipStrip />
      <Counters />
      <Finale />
      <Footer />
    </main>
  )
}

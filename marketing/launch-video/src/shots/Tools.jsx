// Shots 9-11: three tool cards, the eight tools, the page they build.
import { useVideoConfig } from 'remotion'
import { C, CARDS, FONT, TOOLS } from '../config'
import T from '../timeline.json'
import { Stage, Bleed, At, Camera, useFit } from '../ui/Stage'
import { WarmBg, ToolCard, Tile, Pic } from '../ui/Kit'
import { enter, mix, ramp, typed, easeOut, easeInOut } from '../motion'

// Shot 9. The reference's three agent cards, as Tafheem's three core tools.
export function Cards({ frame }) {
  const f = frame - 750
  const at = T.cue.cardsIn
  const { width, height } = useVideoConfig()
  const tall = height > width * 1.2
  const fit = tall ? 1 : useFit(1500)
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={5} />
      </Bleed>
      <Stage>
        <Camera scale={(1 + f * 0.0007) * fit}>
          {CARDS.map((card, i) => {
            const t = enter(frame, at + i * 6, 28)
            const on = ramp(frame, T.cue.toggleOn + i * 6, T.cue.toggleOn + i * 6 + 9, easeOut)
            return (
              <At key={i} x={tall ? 0 : (i - 1) * 492} y={(tall ? (i - 1) * 420 : [-6, -12, 4][i]) + (1 - t) * 70}>
                <div style={{ opacity: Math.min(1, t * 1.6) }}>
                  <ToolCard card={card} on={on} w={440} k={tall ? 1.4 : 1.06} />
                </div>
              </At>
            )
          })}
        </Camera>
      </Stage>
    </>
  )
}

// Shot 10. The app's eight tools pop in, one by one.
export function Icons({ frame }) {
  const f = frame - 820
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={5.5} />
      </Bleed>
      <Stage>
        <Camera scale={(1 + f * 0.001) * useFit(1300)}>
          <At>
            <div style={{ display: 'flex', gap: 62 }}>
              {TOOLS.map(([name, ar, tone], i) => {
                const t = enter(frame, T.cue.iconsIn + i * 6, 24)
                return (
                  <div key={name} style={{ transform: `scale(${t})`, opacity: Math.min(1, t * 2) }}>
                    <Tile glyph={ar} tone={tone} size={96} label={name} />
                  </div>
                )
              })}
            </div>
          </At>
        </Camera>
      </Stage>
    </>
  )
}

// Shot 11. The reference's website mock-up, here Tafheem's own page on Al-'Alaq.
export function Page({ frame }) {
  const f = frame - 870
  const pop = enter(frame, 870, 26)
  const word = ramp(frame, 892, 906, easeOut)
  const foot = enter(frame, 878, 26)
  const W = 1180
  return (
    <>
      <Bleed>
        <WarmBg frame={frame} seed={6} />
      </Bleed>
      <Stage>
        <Camera scale={(0.9 + 0.1 * pop) * (1 + f * 0.0006) * useFit(1220)}>
          <At y={(1 - pop) * 40}>
            <div
              style={{
                width: W,
                padding: 28,
                boxSizing: 'border-box',
                background: '#fbfaf9',
                borderRadius: 14,
                boxShadow: '0 40px 120px rgba(0,0,0,0.55)',
                fontFamily: FONT.ui,
                color: C.ink,
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: 30 }}>
                <span style={{ fontWeight: 700, letterSpacing: 1.5, fontSize: 17 }}>TAFHEEM</span>
                <span style={{ display: 'flex', gap: 26, fontSize: 15, color: '#6c6560' }}>
                  <span>Nahw</span>
                  <span>Sarf</span>
                  <span>Qur’an</span>
                  <span>Dictionary</span>
                  <span>Quiz</span>
                  <span style={{ width: 14, height: 14, borderRadius: '50%', border: '2px solid #6c6560', display: 'inline-block' }} />
                </span>
              </div>
              <div style={{ display: 'flex', gap: 12, height: 360 }}>
                <div
                  style={{
                    width: 340,
                    background: C.saffron,
                    borderRadius: 6,
                    padding: '26px 28px',
                    boxSizing: 'border-box',
                    color: '#fff',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ fontSize: 60, letterSpacing: -2, fontWeight: 500, lineHeight: 1 }}>{typed('Al-ʿAlaq', frame, 874, 890)}</div>
                  <div
                    style={{
                      fontFamily: FONT.mushaf,
                      fontSize: 120,
                      lineHeight: 1.1,
                      direction: 'rtl',
                      textAlign: 'right',
                      opacity: word,
                      transform: `translateY(${(1 - word) * 20}px)`,
                    }}
                  >
                    ٱقْرَأْ
                  </div>
                  <div style={{ fontSize: 17, opacity: 0.9 }}>96:1 · Read in the name of your Lord</div>
                </div>
                <Pic src="folio.jpg" w={W - 56 - 340 - 12} h={360} zoom={1.25} ox={40} oy={20} style={{ borderRadius: 6 }} />
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                {['nahw.jpg', 'sarf.jpg', 'quran.jpg', 'dict.jpg'].map((src, i) => (
                  <div key={src} style={{ opacity: ramp(frame, 880 + i * 4, 892 + i * 4) }}>
                    <Pic src={src} w={(W - 56 - 36) / 4} h={170} style={{ borderRadius: 6 }} />
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-around', padding: '6px 20px 0', transform: `translateY(${(1 - foot) * 120}px)`, opacity: Math.min(1, foot * 2) }}>
                {TOOLS.map(([name, ar, tone]) => (
                  <Tile key={name} glyph={ar} tone={tone} size={56} label={name} labelColor="#6c6560" />
                ))}
              </div>
            </div>
          </At>
        </Camera>
      </Stage>
    </>
  )
}

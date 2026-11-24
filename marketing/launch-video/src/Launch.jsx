import { AbsoluteFill, Sequence, useCurrentFrame, Audio, staticFile } from 'remotion'
import './fonts'
import T from './timeline.json'
import { Hook } from './scenes/Hook'
import { Problem } from './scenes/Problem'
import { Demo } from './scenes/Demo'
import { Payoff } from './scenes/Payoff'

const SCENES = [
  ['hook', Hook],
  ['problem', Problem],
  ['demo', Demo],
  ['payoff', Payoff],
]

// Each scene gets the global frame, so every cue in timeline.json is one number.
function Scene({ start, Body }) {
  const frame = useCurrentFrame() + start
  return <Body frame={frame} />
}

export function Launch({ withAudio = true }) {
  return (
    <AbsoluteFill style={{ background: '#0f0d0b' }}>
      {SCENES.map(([key, Body]) => {
        const [a, b] = T.scenes[key]
        return (
          <Sequence key={key} from={a} durationInFrames={b - a} name={key}>
            <Scene start={a} Body={Body} />
          </Sequence>
        )
      })}
      {withAudio && <Audio src={staticFile('audio/soundtrack.wav')} />}
    </AbsoluteFill>
  )
}

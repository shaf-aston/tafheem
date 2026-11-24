import { AbsoluteFill, Sequence, useCurrentFrame, Audio, staticFile } from 'remotion'
import './fonts'
import T from './timeline.json'
import * as Open from './shots/Open'
import * as Chat from './shots/Chat'
import * as Engine from './shots/Engine'
import * as Tools from './shots/Tools'
import * as Proof from './shots/Proof'
import * as Close from './shots/Close'

// timeline.json names each shot; this maps the name to the component that draws it.
const BODY = {
  tunnel: Open.Tunnel,
  meet: Open.Meet,
  hello: Open.Hello,
  chat: Chat.Chat,
  prompt: Chat.Prompt,
  stream: Engine.Stream,
  connect: Engine.Connect,
  web: Engine.Web,
  cards: Tools.Cards,
  icons: Tools.Icons,
  page: Tools.Page,
  dots: Proof.Dots,
  folio: Proof.Folio,
  dash: Proof.Dash,
  final: Close.Final,
  logo: Close.Logo,
}

// Each shot gets the global frame, so every cue in timeline.json is one number.
function Shot({ start, Body }) {
  const frame = useCurrentFrame() + start
  return <Body frame={frame} />
}

export function Launch({ withAudio = true }) {
  return (
    <AbsoluteFill style={{ background: '#060302' }}>
      {T.shots.map(([key, a, b]) => (
        <Sequence key={key} from={a} durationInFrames={b - a} name={key}>
          <Shot start={a} Body={BODY[key]} />
        </Sequence>
      ))}
      {withAudio && <Audio src={staticFile('audio/soundtrack.wav')} />}
    </AbsoluteFill>
  )
}

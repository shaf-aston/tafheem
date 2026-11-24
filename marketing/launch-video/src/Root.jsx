import { Composition } from 'remotion'
import T from './timeline.json'
import { Launch } from './Launch'

// One video, three frames: the 16:9 master and the 9:16 and 1:1 cutdowns.
// Stage (ui/Stage.jsx) keeps the key action in the centre square for all three.
export function Root() {
  const common = { component: Launch, durationInFrames: T.total, fps: T.fps, defaultProps: { withAudio: true } }
  return (
    <>
      <Composition id="Launch" width={1920} height={1080} {...common} />
      <Composition id="LaunchVertical" width={1080} height={1920} {...common} />
      <Composition id="LaunchSquare" width={1080} height={1080} {...common} />
    </>
  )
}

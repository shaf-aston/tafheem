// A phrase's sound in English letters, shown only while the learner's setting asks for it.
import { useSetting } from '../../lib/settings'
import Pronunciation from '../ui/Pronunciation'

export default function Spelling(props) {
  return useSetting('colloq-spelling') ? <Pronunciation {...props} /> : null
}

// A phrase's sound in English letters, shown only while the learner's setting asks for it.
import { useSetting } from '../../../lib/store/settings'
import Pronunciation from '../../ui/text/Pronunciation'

export default function Spelling(props) {
  return useSetting('colloq-spelling') ? <Pronunciation {...props} /> : null
}

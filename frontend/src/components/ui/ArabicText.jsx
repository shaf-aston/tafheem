/**
 * Right-to-left content with the attributes assistive tech needs: lang switches
 * a screen reader to the right voice, dir="rtl" states direction in the markup
 * rather than leaving it to CSS.
 *
 * Arabic is what it is nearly always for, and the default. `lang="ur"` is the
 * other one: Urdu is the same direction and the same size ladder, and index.css
 * swaps the font and the line height on the element for it, so nothing here has
 * to know which script it is holding.
 *
 * Size is a prop, not a class a caller writes, so the four sizes in
 * index.css stay the only sizes any of this text can be.
 *
 * Qur'anic text is recognised by its own spelling, not by who shows it: an
 * ayah carries marks no other Arabic does (ٱ, ۟, the waqf signs), and the face
 * that draws everyday Arabic well stacks them badly. So the element says
 * data-script="quran" and index.css swaps the face, as it does for Urdu, and
 * no page has to remember to ask.
 */
import { isQuranic, textOf } from '../../lib/arabicText'

const SIZES = { tiny: 'arabic-tiny', sm: 'arabic-sm', base: 'arabic', lg: 'arabic-lg' }

export default function ArabicText({ as: Tag = 'span', size = 'base', lang = 'ar', className = '', children, ...props }) {
  return (
    <Tag
      className={`${SIZES[size]} ${className}`.trim()}
      lang={lang}
      dir="rtl"
      data-script={isQuranic(textOf(children)) ? 'quran' : undefined}
      {...props}
    >
      {children}
    </Tag>
  )
}

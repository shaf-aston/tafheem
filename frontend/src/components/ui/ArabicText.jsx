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
 * Qur'an text is recognised by its own marks (isQuranic) and flagged
 * data-script="quran" for the face drawn for them, and every piece of text
 * inside is given the tatweel a small alef stands on (seatSmallAlef). No page
 * has to remember to ask for either.
 */
import { cloneElement, isValidElement } from 'react'

import { isQuranic, seatSmallAlef, textOf } from '../../lib/arabicText'

const SIZES = { tiny: 'arabic-tiny', sm: 'arabic-sm', base: 'arabic', lg: 'arabic-lg' }

const seated = (node) => {
  if (typeof node === 'string') return seatSmallAlef(node)
  if (Array.isArray(node)) return node.map(seated)
  if (isValidElement(node) && node.props.children != null) {
    return cloneElement(node, { children: seated(node.props.children) })
  }
  return node
}

export default function ArabicText({ as: Tag = 'span', size = 'base', lang = 'ar', className = '', children, ...props }) {
  return (
    <Tag
      className={`${SIZES[size]} ${className}`.trim()}
      lang={lang}
      dir="rtl"
      data-script={isQuranic(textOf(children)) ? 'quran' : undefined}
      {...props}
    >
      {seated(children)}
    </Tag>
  )
}

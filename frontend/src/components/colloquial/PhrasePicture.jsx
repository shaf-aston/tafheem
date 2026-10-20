/**
 * The picture beside a phrase, or a quiet stand-in while there is none.
 *
 * Every layout draws a phrase's picture through this one component, so "no
 * picture yet" and "picture failed to load" look the same everywhere and a lesson
 * never shows a broken image. The size comes from the caller's className.
 */
import { useState } from 'react'

import { colloquialImageUrl } from '../../api'

export default function PhrasePicture({ phrase, className = '' }) {
  const [gone, setGone] = useState(false)
  const box = `overflow-hidden bg-[var(--surface-hi)] ${className}`
  if (!phrase.image || gone) return <div aria-hidden="true" className={box} />
  return (
    <img
      src={colloquialImageUrl(phrase.image)}
      alt={phrase.english}
      loading="lazy"
      onError={() => setGone(true)}
      className={`${box} object-cover`}
    />
  )
}

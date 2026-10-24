/**
 * Rise and fade in, once, when something scrolls into view (the .reveal class in
 * styles/motion.css). One wrapper for the landing's sections and the app's
 * grids; lib/motion/useReveal is the same thing for a component that owns its element.
 */
import { useReveal } from '../../lib/motion/useReveal'

export default function Reveal({ as: Tag = 'div', className = '', children, ...rest }) {
  const [ref, reveal] = useReveal()
  return (
    <Tag ref={ref} className={`${reveal} ${className}`.trim()} {...rest}>
      {children}
    </Tag>
  )
}

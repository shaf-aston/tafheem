import { useInView } from '../lib/useInView'

// Fades an element up into place the first time it crosses into view. Every
// section reuses this instead of re-wiring its own IntersectionObserver.
export default function Reveal({ as: Tag = 'div', className = '', children, ...rest }) {
  const [ref, inView] = useInView({ threshold: 0.15 })
  return (
    <Tag ref={ref} className={`reveal${inView ? ' in' : ''} ${className}`.trim()} {...rest}>
      {children}
    </Tag>
  )
}

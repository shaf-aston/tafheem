/**
 * [ref, className] for an element that should .reveal (styles/motion.css) when it
 * scrolls into view; landing/Reveal wraps it for the simple case, ui/Tile and Grow's
 * world tile own their element and use it directly. useInView treats everything
 * as seen where there is no IntersectionObserver, so nothing stays hidden.
 */
import { useInView } from './useInView'

export function useReveal() {
  const [ref, inView] = useInView({ threshold: 0.15 })
  return [ref, `reveal${inView ? ' in' : ''}`]
}

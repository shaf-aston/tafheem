import { useCallback, useState } from 'react'

/**
 * Drag one thing onto a place, on a mouse or a finger. Native drag and drop
 * does not fire on a touch screen, so this follows the pointer itself.
 *
 * A place is any element carrying data-slot="<name>". `grip(id)` is spread on
 * whatever starts the drag (it takes the touch, so a page scrolled by touching
 * it would not move); `drag` is { id, x, y, over } while one is in flight,
 * where `over` is the slot name under the pointer. `onDrop(id, slot)` gets the
 * name it was let go over, and nothing if it was let go anywhere else.
 */
export function useDrag(onDrop) {
  const [drag, setDrag] = useState(null)

  const grip = useCallback((id) => ({
    style: { touchAction: 'none' },
    onPointerDown: (event) => {
      event.currentTarget.setPointerCapture(event.pointerId)
      setDrag({ id, x: event.clientX, y: event.clientY, over: null })
    },
    onPointerMove: (event) => {
      const over = document.elementFromPoint(event.clientX, event.clientY)?.closest('[data-slot]')?.dataset.slot ?? null
      setDrag((now) => now && { ...now, x: event.clientX, y: event.clientY, over })
    },
    onPointerUp: (event) => {
      const over = document.elementFromPoint(event.clientX, event.clientY)?.closest('[data-slot]')?.dataset.slot
      setDrag(null)
      if (over !== undefined) onDrop(id, over)
    },
    onPointerCancel: () => setDrag(null),
  }), [onDrop])

  return { drag, grip }
}

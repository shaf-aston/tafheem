import { useEffect, useState } from 'react'

import EmptyState from '../components/ui/EmptyState'
import { COPY, Row } from './parts'
import { loadUnit, shown, unitIds } from './units'

/** Every unit in the folder, each loaded on its own. */
export default function UnitList({ onOpen }) {
  const [units, setUnits] = useState(null)

  useEffect(() => {
    let live = true
    Promise.all(unitIds().map((id) => loadUnit(id))).then((all) => live && setUnits(all.filter((u) => shown(u))))
    return () => { live = false }
  }, [])

  if (units && !units.length) return <EmptyState>{COPY['no-units']}</EmptyState>
  return (
    <ul className="grid gap-2 sm:grid-cols-2">
      {(units ?? []).map((u) => (
        <li key={u.id}>
          <Row disabled={!u.unit} onClick={() => onOpen(u.unit)}>
            <span className="type-tiny text-[var(--text-faint)]">{u.id}</span>
            <span className="block font-semibold">{u.unit?.title ?? COPY['unit-unavailable']}</span>
          </Row>
        </li>
      ))}
    </ul>
  )
}

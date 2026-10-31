import { useQuery } from '@tanstack/react-query'

import { mushafsQuery } from '../../api'
import { useRemembered } from '../store/useRemembered'

/** The reader's own layout, the ayah list; every other choice is a printing. */
const AYAHS = 'ayahs'

/**
 * How the reader lays a surah out: as its ayahs, or as the pages of one printed
 * mushaf. The printings are the server's list (data/quran/mushaf/printings.json),
 * so a new one is offered without a line here, and none is offered where none is
 * built: the choice then never appears and the ayah list is all there is.
 */
export function useMushaf() {
  const { data } = useQuery(mushafsQuery)
  const printings = data ?? []
  const [layout, choose] = useRemembered('reader-layout', [AYAHS, ...printings.map((one) => one.id)], AYAHS)
  const printing = printings.find((one) => one.id === layout) ?? null
  const choices = printings.length
    ? [{ id: AYAHS, label: 'Ayahs' }, ...printings.map((one) => ({ id: one.id, label: one.name }))]
    : []
  return { choices, layout, choose, printing }
}

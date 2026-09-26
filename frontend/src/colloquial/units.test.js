// The supplied unit files, checked for real. `npm run validate:colloq` runs
// just this file and prints the report; fixing a problem is the author's job.
import { expect, it } from 'vitest'

import { formatReport, validateAll } from './validate'

const units = Object.fromEntries(
  Object.entries(import.meta.glob('../data/colloquial/*.json', { eager: true, import: 'default' }))
    .map(([path, unit]) => [path.split('/').pop(), unit]),
)

it('every unit file passes the schema and rules', () => {
  const problems = validateAll(units)
  console.log(formatReport(problems, Object.keys(units).length))
  expect(problems).toEqual([])
})

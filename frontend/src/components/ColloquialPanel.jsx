import { useState } from 'react'

import LessonList from '../colloquial/LessonList'
import LessonPage from '../colloquial/LessonPage'
import UnitList from '../colloquial/UnitList'
import SectionHeader from './ui/SectionHeader'

/** Routes between the unit list, a unit's lessons and one lesson. */
export default function ColloquialPanel({ accent }) {
  const [unit, setUnit] = useState(null)
  const [lesson, setLesson] = useState(null)

  const screen = lesson ? (
    <LessonPage lesson={lesson} accent={accent} onBack={() => setLesson(null)} />
  ) : unit ? (
    <LessonList unit={unit} onOpen={setLesson} onBack={() => setUnit(null)} />
  ) : (
    <UnitList onOpen={setUnit} />
  )

  return (
    <div className="space-y-6">
      <SectionHeader title="Colloquial" arabic="عامية" subtitle="Spoken, everyday Arabic." />
      {screen}
    </div>
  )
}

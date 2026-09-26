import { Back, COPY, Row } from './parts'

export default function LessonList({ unit, onOpen, onBack }) {
  return (
    <div className="space-y-3">
      <Back onClick={onBack} />
      <h3 className="text-lg font-semibold">{unit.title}</h3>
      <ul className="grid gap-2" aria-label={COPY.lessons}>
        {unit.lessons.map((lesson) => (
          <li key={lesson.id}>
            <Row onClick={() => onOpen(lesson)}>
              <span className="type-tiny text-[var(--text-faint)]">{lesson.id}</span>
              <span className="block font-semibold">{lesson.situation}</span>
              <span className="block type-small text-[var(--text-dim)]">{lesson.goal}</span>
            </Row>
          </li>
        ))}
      </ul>
    </div>
  )
}

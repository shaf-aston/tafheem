/**
 * The form a tab asks its question in: the box, its microphone, and the chips and
 * pickers that go with it. Every tab that takes a question (Nahw, Sarf, the Qur'an,
 * the Dictionary, Daleel, Hadith) draws it through here, so how they all behave is
 * decided in this one file, not in six.
 *
 * It stays whole over the answer. Folding it into a slim pill holding the question
 * was tried and taken back: the box is the search, and a search that hides itself
 * behind a pill reads as a different control from one tab to the next.
 *
 * Its width is the field's (theme.json layout.field), so a box for one word is not a
 * banner across the page; see .question-form in styles/components.css.
 */
export default function QuestionForm({ accent, children }) {
  return (
    <div className="question-form" style={{ '--c': accent }}>
      {children}
    </div>
  )
}

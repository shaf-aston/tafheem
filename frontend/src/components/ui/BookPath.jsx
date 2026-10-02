import ArabicText from './ArabicText'

/**
 * The book's divisions that named a word (اسم ← ... (تسهيل النحو 3.1، ص 60)): the
 * source under a proof, on the word card and in the analyser's table alike.
 */
export default function BookPath({ path }) {
  if (!path) return null
  return <ArabicText as="p" size="tiny" className="mt-1.5 text-[var(--text-dim)]">{path}</ArabicText>
}

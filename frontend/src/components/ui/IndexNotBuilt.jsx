/**
 * A search whose index was never built on this machine. Not an EmptyState:
 * "nothing matches" would blame the question for a missing file, so it says
 * what is wrong and the one command that puts it right.
 */
import Code from './Code'
import ErrorAlert from './ErrorAlert'

export default function IndexNotBuilt({ command }) {
  return (
    <ErrorAlert title="Search index not built">
      Every search would come back empty until it is built:{' '}
      <Code>{command}</Code>
    </ErrorAlert>
  )
}

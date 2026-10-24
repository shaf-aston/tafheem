/** Sarf, the root, the pattern, and the full conjugation of a single word. */
import { errorMessage } from '../../lib/api/apiError'
import { useSarf } from '../../lib/sarf/useSarf'

import ErrorAlert from '../ui/ErrorAlert'
import MicButton from '../ui/MicButton'
import PresetsDrawer from '../nahw/PresetsDrawer'
import SarfResult from './SarfResult'
import SearchBox from '../ui/SearchBox'
import SectionHeader from '../ui/SectionHeader'
import { AnalyzerSkeleton } from '../ui/Skeleton'

export default function SarfPanel({ accent, incoming, arrival, onGo, onVisit }) {
  const {
    word, data, base, waiting, mutation, swap, meaning,
    edit, submit, chooseForm, retrySwap, pickPreset, reset,
  } = useSarf({ incoming, arrival, onVisit })

  return (
    <div className="panel">
      <SectionHeader
        tab="sarf"
        subtitle="Where a word comes from: its three-letter root, its pattern, and how it conjugates."
      />

      <div className="space-y-4">
        {/* The same field as Dictionary, Daleel and the Qur'an tab, down to the
            keycap and the microphone. See ui/SearchBox. */}
        <SearchBox
          id="sarf-input"
          label="Arabic word"
          verb="analyse"
          arabic
          placeholder="اكتب كلمة..."
          value={word}
          onChange={edit}
          onSubmit={() => submit()}
          onClear={reset}
          busy={waiting}
          accent={accent}
        >
          <MicButton
            onHeard={({ text }) => edit(text)}
            accent={accent}
            title="Say the word"
          />
        </SearchBox>

        <PresetsDrawer onPick={pickPreset} accent={accent} />
      </div>

      {mutation.isError && (
        <ErrorAlert title="Analysis failed" onRetry={() => submit()}>
          {errorMessage(mutation.error)}
        </ErrorAlert>
      )}

      {waiting && !base && <AnalyzerSkeleton />}

      {data && (
        <SarfResult
          data={data}
          loading={waiting}
          meaningPending={meaning.isPending}
          swapPending={swap.isPending}
          swapError={swap.isError ? errorMessage(swap.error) : null}
          onRetrySwap={retrySwap}
          accent={accent}
          onForm={chooseForm}
          onGo={onGo}
        />
      )}
    </div>
  )
}

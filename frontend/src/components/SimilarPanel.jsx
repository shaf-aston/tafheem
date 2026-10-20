/**
 * Similar verses (mutashabihat): pairs of verses that read almost alike, learnt
 * the way a hafiz learns them. Compare lays the two side by side with what tells
 * them apart; Drill takes each difference out and offers its own wording against
 * its twin's. A pair passed with no slip is filed as known in the progress store,
 * which also brings it back when it is due.
 *
 * The pairs and where they differ come from the backend catalogue; the rules are
 * in lib/similar.js; the words are in similar.json.
 */
import { useState } from 'react'

import surahs from '../data/surahs.json'
import { useRemembered } from '../lib/useRemembered'
import copy from '../similar.json'

import Compare from './similar/Compare'
import Drill from './similar/Drill'
import { useMastery, usePair, useSurahPairs } from './similar/hooks'
import PairList from './similar/PairList'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import PrimaryButton from './ui/PrimaryButton'
import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'
import { Skeleton } from './ui/Skeleton'
import WheelPicker from './ui/WheelPicker'

const SURAHS = surahs.map((s) => ({ id: String(s.n), label: `${s.n}. ${s.en}`, hint: s.ar }))

export default function SimilarPanel({ accent }) {
  const [surah, setSurah] = useRemembered('similar-surah', SURAHS.map((s) => s.id), String(copy['default-surah']))
  const { query: surahQuery, pairs } = useSurahPairs(Number(surah))
  const [chosenId, choose] = useState(null)
  const [step, setStep] = useState('compare')
  const [round, setRound] = useState(0)
  const { standing, file } = useMastery()

  const chosen = pairs.find((p) => p.id === chosenId) ?? pairs[0] ?? null
  const { query: pairQuery, mine, partner } = usePair(chosen)
  const known = pairs.filter((p) => standing(p.id) === 'known').length

  const open = (id, to = 'compare') => {
    choose(id)
    setStep(to)
    setRound((n) => n + 1)
  }
  const openSurah = (id) => {
    setSurah(id)
    choose(null)
    setStep('compare')
  }
  const after = pairs[(pairs.indexOf(chosen) + 1) % Math.max(pairs.length, 1)]

  return (
    <div className="panel">
      <SectionHeader emblem="similar" title={copy.title} arabic={copy.arabic} subtitle={copy.subtitle} />

      <div className="grid gap-4 lg:grid-cols-[var(--layout-rail)_minmax(0,1fr)] items-start">
        <aside className="min-w-0 space-y-3 lg:sticky lg:top-[calc(var(--app-header-h,0px)+1rem)]">
          <WheelPicker label={copy.surah} options={SURAHS} value={surah} onChange={openSurah} accent={accent} className="w-full" />
          {pairs.length > 0 && (
            <div className="space-y-1">
              <div className="flex justify-between type-small text-[var(--text-dim)]">
                <span>{copy.mastered}</span>
                <span>{known} / {pairs.length}</span>
              </div>
              <div className="h-1.5 rounded-full bg-[var(--surface-hi)] overflow-hidden">
                <div className="h-full bg-[var(--success)]" style={{ width: `${(100 * known) / pairs.length}%` }} />
              </div>
            </div>
          )}
          {surahQuery.isPending && <Skeleton className="h-40 w-full" />}
          <PairList pairs={pairs} chosen={chosen?.id} onChoose={(id) => open(id)} standing={standing} />
        </aside>

        <section className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-3 sm:p-5 space-y-4 min-w-0">
          {surahQuery.isError && (
            <ErrorAlert title={copy.error} error={surahQuery.error} fallback={copy.fallback} onRetry={surahQuery.refetch} />
          )}
          {surahQuery.isSuccess && pairs.length === 0 && <EmptyState>{copy.none}</EmptyState>}
          {chosen && (
            <>
              <Segmented label={copy.title} options={copy.steps} value={step} onChange={(id) => open(chosen.id, id)} accent={accent} />
              {pairQuery.isPending && <Skeleton className="h-48 w-full" />}
              {pairQuery.isError && (
                <ErrorAlert title={copy.error} error={pairQuery.error} fallback={copy.fallback} onRetry={pairQuery.refetch} />
              )}
              {mine && partner && step === 'compare' && (
                <>
                  <Compare mine={mine} partner={partner} />
                  <PrimaryButton accent={accent} onClick={() => open(chosen.id, 'drill')}>{copy.start}</PrimaryButton>
                </>
              )}
              {mine && partner && step === 'drill' && (
                <Drill
                  key={round}
                  seed={round}
                  mine={mine}
                  partner={partner}
                  accent={accent}
                  onDone={(correct) => file(chosen.id, correct)}
                  onCompare={() => open(chosen.id)}
                  onNext={() => open(after.id)}
                />
              )}
            </>
          )}
        </section>
      </div>
    </div>
  )
}

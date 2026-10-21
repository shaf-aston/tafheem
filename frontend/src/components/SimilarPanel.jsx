/**
 * Similar verses (mutashabihat): pairs of verses that read almost alike, learnt
 * the way a hafiz learns them. Compare lays the two side by side with what tells
 * them apart (and what follows each); Drill takes each difference out and offers
 * its own wording against its twin's. A pair passed with no slip is filed as
 * known in the progress store, which also brings it back when it is due.
 *
 * One way in: Start opens what is due, else the next new pair, and a passed drill
 * moves on the same way, so the list is for looking around, not for driving. On a
 * wide screen the list is the rail, scrolling inside it; on a phone it is a Browse
 * sheet and a stepper walks the pairs. Arriving with a verse ("2:3", the reader's
 * look-alikes link) opens that verse's first pair.
 *
 * The pairs and where they differ come from the backend catalogue; the rules are
 * in lib/similar.js; the words are in similar.json.
 */
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { similarAyahQuery } from '../api'
import surahs from '../data/surahs.json'
import { fill, firstPair, nextUp } from '../lib/similar'
import { SURAH_KEY } from '../lib/similarOpen'
import { parsePlace } from '../lib/similarPlace'
import { useArrivalWhenReady } from '../lib/useArrival'
import { PHONE, useMedia } from '../lib/useMedia'
import { useRemembered } from '../lib/useRemembered'
import { warm } from '../lib/warm'
import copy from '../similar.json'

import Compare from './similar/Compare'
import Drill from './similar/Drill'
import { useMastery, usePair, useSurahPairs } from './similar/hooks'
import PairList from './similar/PairList'
import BottomSheet from './ui/BottomSheet'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import PrimaryButton from './ui/PrimaryButton'
import SectionHeader from './ui/SectionHeader'
import Segmented from './ui/Segmented'
import { Skeleton } from './ui/Skeleton'
import Stepper from './ui/Stepper'
import WheelPicker from './ui/WheelPicker'

const SURAHS = surahs.map((s) => ({ id: String(s.n), label: `${s.n}. ${s.en}`, hint: s.ar }))

export default function SimilarPanel({ accent, incoming, arrival, onVisit }) {
  const [surah, setSurah] = useRemembered(SURAH_KEY, SURAHS.map((s) => s.id), String(copy['default-surah']))
  const { query: surahQuery, pairs } = useSurahPairs(Number(surah))
  const [chosenId, choose] = useState(null)
  // The verse a link asked for, until its pairs have come.
  const [wanted, setWanted] = useState(null)
  const [step, setStep] = useState('compare')
  const [round, setRound] = useState(0)
  const [browsing, setBrowsing] = useState(false)
  const phone = useMedia(PHONE)
  const { standing, file } = useMastery()

  if (useArrivalWhenReady(arrival, true)) {
    const place = parsePlace(incoming)
    if (place) {
      setSurah(String(place.surah))
      setWanted(`${place.surah}:${place.ayah}`)
      choose(null)
      setStep('compare')
    }
  }

  const chosen = pairs.find((p) => p.id === chosenId) ?? firstPair(pairs, wanted)
  const { query: pairQuery, mine, partner } = usePair(chosen)
  const known = pairs.filter((p) => standing(p.id) === 'known').length
  const at = pairs.indexOf(chosen)
  const up = nextUp(pairs, standing)

  // Fetched ahead: the pairs a learner most likely opens next (Start's, and the
  // one after this, for the stepper and a passed drill), and any the pointer is on.
  const client = useQueryClient()
  const ahead = (pair) => pair && client.prefetchQuery(similarAyahQuery(pair.mine))
  const after = pairs[at + 1]
  useEffect(() => {
    if (up) warm(client, similarAyahQuery(up.mine))
    if (after) warm(client, similarAyahQuery(after.mine))
  }, [client, up, after])

  const open = (id, to = 'compare') => {
    const pair = pairs.find((p) => p.id === id)
    choose(id)
    setWanted(null)
    setStep(to)
    setRound((n) => n + 1)
    setBrowsing(false)
    if (pair) onVisit?.(pair.mine)
  }
  const openSurah = (id) => {
    setSurah(id)
    choose(null)
    setWanted(null)
    setStep('compare')
  }
  const onward = () => {
    const next = nextUp(pairs, standing, at) ?? pairs[(at + 1) % pairs.length]
    open(next.id, standing(next.id) === 'due' ? 'drill' : 'compare')
  }

  const list = <PairList pairs={pairs} chosen={chosen?.id} onChoose={(id) => open(id)} onAhead={ahead} standing={standing} className={phone ? '' : 'lg:max-h-[60vh] lg:overflow-y-auto lg:pr-1'} />

  return (
    <div className="panel">
      <SectionHeader tab="similar" subtitle={copy.subtitle} />

      <div className="grid gap-4 lg:grid-cols-[var(--layout-rail)_minmax(0,1fr)] items-start">
        <aside className="min-w-0 space-y-3 lg:sticky lg:top-[calc(var(--app-header-h,0px)+1rem)]">
          <WheelPicker label={copy.surah} options={SURAHS} value={surah} onChange={openSurah} accent={accent} className="w-full" />
          {pairs.length > 0 && (
            <>
              <PrimaryButton accent={accent} disabled={!up} onClick={() => up && open(up.id, standing(up.id) === 'due' ? 'drill' : 'compare')}>
                {up ? (standing(up.id) === 'due' ? copy['start-due'] : copy['start-new']) : copy['all-done']}
              </PrimaryButton>
              <div className="space-y-1">
                <div className="flex justify-between type-label text-[var(--text-dim)]">
                  <span>{copy.mastered}</span>
                  <span>{known} / {pairs.length}</span>
                </div>
                <div className="h-1.5 rounded-full bg-[var(--surface-hi)] overflow-hidden">
                  <div className="h-full bg-[var(--success)]" style={{ width: `${(100 * known) / pairs.length}%` }} />
                </div>
              </div>
            </>
          )}
          {surahQuery.isPending && <Skeleton className="h-40 w-full" />}
          {pairs.length > 0 && (phone ? (
            <div className="flex items-center justify-between gap-3">
              <button type="button" onClick={() => setBrowsing(true)} className="press tap type-label underline underline-offset-4 text-[var(--text-dim)]">
                {copy.browse}
              </button>
              <span className="type-label text-[var(--text-dim)]">{fill(copy['pair-of'], { n: at + 1, of: pairs.length })}</span>
              <Stepper label={copy.pairs} onPrev={at > 0 ? () => open(pairs[at - 1].id) : null} onNext={at < pairs.length - 1 ? () => open(pairs[at + 1].id) : null} />
            </div>
          ) : list)}
        </aside>

        <section className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-3 sm:p-5 space-y-4 min-w-0">
          {surahQuery.isError && (
            <ErrorAlert title={copy.error} error={surahQuery.error} fallback={copy.fallback} onRetry={surahQuery.refetch} />
          )}
          {surahQuery.isSuccess && pairs.length === 0 && <EmptyState>{copy.none}</EmptyState>}
          {chosen && (
            <>
              <Segmented label={copy.pairs} options={copy.steps} value={step} onChange={(id) => open(chosen.id, id)} accent={accent} className="w-fit" />
              {pairQuery.isPending && <Skeleton className="h-48 w-full" />}
              {pairQuery.isError && (
                <ErrorAlert title={copy.error} error={pairQuery.error} fallback={copy.fallback} onRetry={pairQuery.refetch} />
              )}
              {mine && partner && step === 'compare' && (
                <>
                  <Compare mine={mine} partner={partner} accent={accent} />
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
                  onNext={onward}
                />
              )}
            </>
          )}
        </section>
      </div>

      {browsing && (
        <BottomSheet label={copy.browse} onClose={() => setBrowsing(false)} className="p-3 max-h-[80dvh] overflow-y-auto">
          {list}
        </BottomSheet>
      )}
    </div>
  )
}

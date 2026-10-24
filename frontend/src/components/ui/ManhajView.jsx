/**
 * The Map's methodologies view: four families of schools and movements, a card
 * per group, and a group's own page when one is picked.
 *
 * A group's page answers its family's fixed questions. With nothing to compare
 * against, each answer lists who else in the family holds it; with a second
 * group picked, answers sit side by side and the rows where they differ are
 * marked. Every "same/different" comes from lib/shell/manhajData's tags; this file
 * judges nothing itself.
 */
import { useState } from 'react'

import ArabicText from './ArabicText'
import { FAMILIES, differs, sharedWith } from '../../lib/shell/manhajData'

export default function ManhajView() {
  const [familyId, setFamilyId] = useState(FAMILIES[0].id)
  const [groupId, setGroupId] = useState(null)
  const [otherId, setOtherId] = useState('')

  const family = FAMILIES.find((f) => f.id === familyId)
  const group = family.groups.find((g) => g.id === groupId) ?? null
  const other = family.groups.find((g) => g.id === otherId) ?? null

  const pickFamily = (id) => { setFamilyId(id); setGroupId(null); setOtherId('') }
  const pickGroup = (id) => { setGroupId(id); setOtherId('') }

  return (
    <div className="p-4 sm:p-5 flex flex-col gap-4">
      <div role="tablist" aria-label="Families" className="flex gap-2 overflow-x-auto sm:flex-wrap -mx-1 px-1 pb-1">
        {FAMILIES.map((f) => (
          <button
            key={f.id}
            type="button"
            role="tab"
            aria-selected={f.id === familyId}
            onClick={() => pickFamily(f.id)}
            className={`shrink-0 whitespace-nowrap px-3 py-1.5 rounded-[var(--radius-md)] border type-small ${f.id === familyId
              ? 'border-[var(--text)] text-[var(--text)] font-bold'
              : 'border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--text)]'}`}
          >
            <ArabicText as="span" size="sm">{f.ar}</ArabicText> · {f.en}
          </button>
        ))}
      </div>

      {group ? (
        <GroupPage family={family} group={group} other={other} onBack={() => pickGroup(null)} onCompare={setOtherId} />
      ) : (
        <>
          <p className="type-small text-[var(--text-dim)]">{family.note} Pick one to see its core beliefs and where it differs.</p>
          <div className="grid gap-3 grid-cols-[repeat(auto-fill,minmax(14rem,1fr))]">
            {family.groups.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => pickGroup(g.id)}
                className="pbs-card text-right p-3 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)]"
              >
                <ArabicText as="p" size="base">{g.ar}</ArabicText>
                <p className="type-small text-[var(--text-dim)]">{g.en}</p>
                <p className="type-tiny text-[var(--text-faint)] mt-1">{g.era}</p>
              </button>
            ))}
          </div>
        </>
      )}

      <p className="type-tiny text-[var(--text-faint)]">
        Simplified from each group’s own main texts, positions as the group itself states them. Check details with a teacher.
      </p>
    </div>
  )
}

function GroupPage({ family, group, other, onBack, onCompare }) {
  const differCount = other ? family.questions.filter((q) => differs(group, other, q.id)).length : 0

  return (
    <article className="flex flex-col gap-4">
      <div className="flex items-start gap-3">
        <button type="button" onClick={onBack} className="icon-button shrink-0" aria-label={`Back to ${family.en}`} title={`Back to ${family.en}`}>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M15 18l-6-6 6-6" /></svg>
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline justify-between gap-x-3">
            <h3 className="type-body font-bold text-[var(--text)]">{group.en}</h3>
            <ArabicText as="p" size="lg" className="font-bold">{group.ar}</ArabicText>
          </div>
          <p className="type-tiny text-[var(--text-faint)]">{group.era} · {group.origin}</p>
        </div>
      </div>

      <dl className="grid gap-x-4 gap-y-1 sm:grid-cols-[8rem_1fr] type-small">
        <dt className="text-[var(--text-faint)]">Found today</dt><dd className="text-[var(--text-dim)]">{group.where}</dd>
        <dt className="text-[var(--text-faint)]">Main texts</dt><dd className="text-[var(--text-dim)]">{group.texts.join(' · ')}</dd>
      </dl>

      <section>
        <h4 className="type-tiny tracking-widest font-bold text-[var(--text-faint)] mb-1">IN THEIR OWN WORDS</h4>
        <p className="type-small text-[var(--text)] border-l-4 border-[var(--border-hi)] pl-3">{group.self}</p>
      </section>

      <section>
        <h4 className="type-tiny tracking-widest font-bold text-[var(--text-faint)] mb-1">CORE BELIEFS</h4>
        <ul className="list-disc pl-5 type-small text-[var(--text)] flex flex-col gap-1">
          {group.beliefs.map((b) => <li key={b}>{b}</li>)}
        </ul>
        {group.note && (
          <p className="mt-2 type-small text-[var(--text-dim)] rounded-[var(--radius-md)] border border-dashed border-[var(--border-hi)] p-2">
            <span className="font-bold">Note: </span>{group.note}
          </p>
        )}
      </section>

      <section>
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <h4 className="type-tiny tracking-widest font-bold text-[var(--text-faint)] flex-1">WHERE IT STANDS</h4>
          <label className="type-small text-[var(--text-dim)] flex items-center gap-2">
            Compare with
            <select
              value={other?.id ?? ''}
              onChange={(e) => onCompare(e.target.value)}
              className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-hi)] text-[var(--text)] px-2 py-1"
            >
              <option value="">—</option>
              {family.groups.filter((g) => g !== group).map((g) => <option key={g.id} value={g.id}>{g.en}</option>)}
            </select>
          </label>
        </div>
        {other && (
          <p className="type-small text-[var(--text-dim)] mb-2">
            Differ on <span className="font-bold text-[var(--text)]">{differCount}</span> of {family.questions.length}. Differences are marked.
          </p>
        )}

        <div className="flex flex-col gap-2">
          {family.questions.map((q) => {
            const mine = group.positions[q.id]
            const d = other ? differs(group, other, q.id) : null
            const same = other ? [] : sharedWith(family, group, q.id)
            return (
              <div
                key={q.id}
                className={`rounded-[var(--radius-md)] border p-2.5 ${d ? 'border-[var(--danger)] border-l-4 bg-[var(--danger-wash)]' : 'border-[var(--border)]'}`}
              >
                <div className="flex items-baseline gap-2 mb-1">
                  <p className="type-small font-bold text-[var(--text)] flex-1">{q.en}</p>
                  <ArabicText as="span" size="sm" className="text-[var(--text-faint)]">{q.ar}</ArabicText>
                  {d === true && <span className="type-tiny font-bold text-[var(--danger)]">DIFFER</span>}
                  {d === false && <span className="type-tiny text-[var(--text-faint)]">same</span>}
                </div>
                <div className={other ? 'grid gap-2 sm:grid-cols-2' : ''}>
                  <p className="type-small text-[var(--text-dim)]">
                    {other && <span className="font-bold text-[var(--text)]">{group.en}: </span>}{mine[1]}
                  </p>
                  {other && (
                    <p className="type-small text-[var(--text-dim)]">
                      <span className="font-bold text-[var(--text)]">{other.en}: </span>{other.positions[q.id][1]}
                    </p>
                  )}
                </div>
                {!other && mine[0] !== 'n/a' && (
                  <p className="type-tiny text-[var(--text-faint)] mt-1">
                    {same.length ? `Same as: ${same.map((g) => g.en).join(', ')}` : 'Unique in this family'}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      </section>
    </article>
  )
}

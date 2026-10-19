import EmptyState from '../ui/EmptyState'
import TwinCards from '../ui/TwinCard'

/** The twin cards under the page: the surah's groups first, then one set per twinned ayah. */
export default function SimilarCards({ lines, queries, surah, accent }) {
  if (surah.isPending || surah.isError) return <TwinCards mine={null} query={surah} accent={accent} />
  if (lines.length === 0) return <EmptyState>No similar verses recorded on this page.</EmptyState>
  return (
    <div className="space-y-4">
      {lines.map(({ line }, i) => (
        <TwinCards key={line.label} mine={{ key: line.label, text: line.arabic }} query={queries[i]} accent={accent} />
      ))}
    </div>
  )
}

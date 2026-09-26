import EmptyState from './ui/EmptyState'
import SectionHeader from './ui/SectionHeader'

export default function ColloquialPanel() {
  return (
    <div className="space-y-6">
      <SectionHeader title="Colloquial" arabic="عامية" subtitle="Spoken, everyday Arabic." />
      <EmptyState>Coming soon.</EmptyState>
    </div>
  )
}

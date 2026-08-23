import SchemaCanvas from '../components/Schema/SchemaCanvas'

export default function SchemaVisualizer({
  standalone = true,
  onClose = null
}) {
  return (
    <div className={`w-full h-full flex-1 flex flex-col relative overflow-hidden ${standalone ? '' : 'rounded-2xl border border-white/10 shadow-2xl bg-bg-canvas'}`}>
      <SchemaCanvas onClose={onClose} />
    </div>
  )
}

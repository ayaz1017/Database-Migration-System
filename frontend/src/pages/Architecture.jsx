import React, { useState } from 'react'
import PipelineMap from '../components/Architecture/PipelineMap'
import NodeInspectorPanel from '../components/Architecture/NodeInspectorPanel'

export default function Architecture() {
  const [activeNode, setActiveNode] = useState(null)

  return (
    <div className="h-screen bg-[#09090b] relative overflow-hidden flex flex-col pt-20 pb-6 px-6">
      {/* Main Map Container */}
      <div className="flex-1 relative z-10 flex flex-col min-h-0">
        <div className="flex-1 relative w-full h-full rounded-xl overflow-hidden shadow-xl border border-zinc-800 bg-zinc-950/80">
          <PipelineMap onNodeClick={setActiveNode} />
          <NodeInspectorPanel node={activeNode} onClose={() => setActiveNode(null)} />
        </div>
      </div>
    </div>
  )
}

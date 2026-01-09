import { useState } from 'react'
import ChatInterface from './components/Chat/ChatInterface'
import CausalGraph from './components/Graph/CausalGraph'
import TopicModal from './components/TopicModal'
import type { Claim } from './services/api'
import { Network } from 'lucide-react'

function App() {
  const [claims, setClaims] = useState<Claim[]>([])
  const [topic, setTopic] = useState<string | null>(null)

  const handleClaimsUpdate = (newClaims: Claim[]) => {
    console.log("App: handleClaimsUpdate called with", newClaims.length, "claims");
    setClaims(prev => {
      const prevIds = prev.map(c => c.id);
      const newIds = newClaims.map(c => c.id);
      console.log("App: Current claims IDs:", prevIds);
      console.log("App: Incoming claims IDs:", newIds);

      const existingIds = new Set(prevIds);
      const filteredNew = newClaims.filter(c => !existingIds.has(c.id));
      console.log(`App: merging. Prev: ${prev.length}, New: ${newClaims.length}, Filtered: ${filteredNew.length}. Result: ${prev.length + filteredNew.length}`);

      return [...prev, ...filteredNew];
    })
  }

  return (
    <div className="h-screen w-screen bg-slate-100 flex flex-col overflow-hidden">
      {!topic && <TopicModal onSubmit={setTopic} />}

      {/* Header */}
      <header className="h-16 bg-white border-b border-slate-200 flex items-center px-6 shadow-sm z-10 shrink-0 justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-700">
            <Network className="w-5 h-5" />
          </div>
          <h1 className="font-bold text-xl text-slate-800 tracking-tight">CAUSA <span className="text-slate-400 font-normal text-sm ml-2">Pilot Werkomgeving</span></h1>
        </div>
        {topic && (
          <div className="px-3 py-1 bg-indigo-50 border border-indigo-100 rounded-lg">
            <span className="text-xs font-semibold text-indigo-500 uppercase tracking-wide mr-2">Thema</span>
            <span className="text-sm font-medium text-slate-700">{topic}</span>
          </div>
        )}
      </header>

      {/* Main Content - Split Screen */}
      <main className="flex-1 flex overflow-hidden p-4 gap-4">

        {/* Left: Chat - 35% width */}
        <section className="w-[35%] min-w-[350px] flex flex-col h-full">
          <ChatInterface onClaimsUpdate={handleClaimsUpdate} topic={topic} />
        </section>

        {/* Right: Graph - remaining width */}
        <section className="flex-1 h-full bg-white rounded-xl shadow-sm border border-slate-200 relative">
          <div className="absolute top-4 left-4 z-10 bg-white/90 backdrop-blur-sm p-2 rounded-lg py-1 px-3 border border-slate-100 shadow-sm">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Visueel Model</span>
          </div>
          <CausalGraph claims={claims} />
        </section>

      </main>
    </div>
  )
}

export default App

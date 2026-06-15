import { useState, useEffect } from 'react'
import Header from './components/Header'
import SimulationCanvas from './components/SimulationCanvas'
import TokenDisplay from './components/TokenDisplay'
import { createSimulation, advanceSimulation } from './services/api'
import { useSessionStore } from './store/sessionStore'
import { useSimulationStore } from './store/simulationStore'
import './App.css'


function App() {
  const simulation = useSimulationStore(state => state.simulation)
  const fetchToken = useSessionStore(state => state.fetchToken)
  const token = useSessionStore(state => state.token)
  const setIsLoading = useSessionStore(state => state.setIsLoading)
  const error = useSessionStore(state => state.error)
  const setError = useSessionStore(state => state.setError)

  const [showTokenModal, setShowTokenModal] = useState(false)  
  
  const hasSimulation = simulation !== null



  const handleAdvanceSteps = async (steps: number) => {
    if (!simulation) return

    try {
      setIsLoading(true)
      setError('')

      console.log('=== ADVANCING SIMULATION ===')
      console.log('Current turn:', simulation.turn)
      console.log('Steps to advance:', steps)

      const sim = await advanceSimulation(steps)
      
      console.log('✅ Simulation advanced')
      console.log('New turn:', sim.turn)
      console.log('Drones in simulation:', sim.drones)
      
      // Keep the same token
      setsimulation({ data: sim, token: token })
    } catch (err: any) {
      setError(err.message || 'Failed to advance simulation')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchToken()
  }, [])

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header />
      {/* Main Layout */}
      <div className="relative bg-black">
        {error && <div className="error-message">{error}</div>}
        {/* Center Panel */}
        <main className="relative">
          {!hasSimulation ? (
            <div className="empty-state">
              <p>Upload a map file to begin</p>
            </div>
          ) : (
            <SimulationCanvas simulation={simulation} token={token} />
          )}
        </main>

        {/* Right Panel */}
        <aside className="absolute top-4 right-4 p-1 overflow-y-auto">
          {hasSimulation && (
            <div className="info-section">
              <h3>Network Status</h3>
              <div className="status-item">
                <span>Hubs:</span>
                <strong>{simulation!.hubs.length}</strong>
              </div>
              <div className="status-item">
                <span>Connections:</span>
                <strong>{simulation!.connections.length}</strong>
              </div>
              <div className="status-item">
                <span>Active Drones:</span>
                <strong>{simulation!.drones.length}</strong>
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* Token Modal */}
      {showTokenModal && (
        <div className="modal-overlay" onClick={() => setShowTokenModal(false)}>
          <TokenDisplay onClose={() => setShowTokenModal(false)} />
        </div>
      )}
    </div>
  )
}

export default App

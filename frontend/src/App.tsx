import { useState, useEffect } from 'react'
import MapUploader from './components/MapUploader'
import SimulationCanvas from './components/SimulationCanvas'
import Controls from './components/Controls'
import TokenDisplay from './components/TokenDisplay'
import { getSimulation, generateToken, createSimulation, advanceSimulation } from './services/api'
import type { ResponseSimulation } from './types'
import './App.css'

interface SimulationWithToken {
  data: ResponseSimulation
  token: string
}

function App() {
  const [token, setToken] = useState<string>('')
  const [simulationWithToken, setSimulationWithToken] = useState<SimulationWithToken | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [showTokenModal, setShowTokenModal] = useState(false)

  const hasSimulation = simulationWithToken !== null
  const currentTurn = simulationWithToken?.data.turn ?? 0

  const generateNewToken = async () => {
    try {
      const newToken = await generateToken()
      console.log('Generated new token:', newToken.substring(0, 10) + '...')
      setToken(newToken)
      setError('')
    } catch (err) {
      setError('Failed to generate token')
      console.error(err)
    }
  }

  const handleMapUploaded = async (file: File) => {
    try {
      setIsLoading(true)
      setError('')

      console.log('Creating simulation with token:', token.substring(0, 10) + '...')
      // Create simulation with the current token
      const sim = await createSimulation(token, file)
      console.log('Simulation created:', sim)
      
      // Store both simulation and token together to avoid desync
      setSimulationWithToken({ data: sim, token })
    } catch (err: any) {
      setError(err.message || 'Failed to create simulation')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAdvanceSteps = async (steps: number) => {
    if (!simulationWithToken) return

    try {
      setIsLoading(true)
      setError('')

      const simToken = simulationWithToken.token
      console.log('=== ADVANCING SIMULATION ===')
      console.log('Current turn:', simulationWithToken.data.turn)
      console.log('Steps to advance:', steps)
      console.log('Token:', simToken.substring(0, 10) + '...')
      
      const sim = await advanceSimulation(simToken, steps)
      
      console.log('✅ Simulation advanced')
      console.log('New turn:', sim.turn)
      console.log('Drones in simulation:', sim.drones)
      
      // Keep the same token
      setSimulationWithToken({ data: sim, token: simToken })
    } catch (err: any) {
      setError(err.message || 'Failed to advance simulation')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    console.log('App mounted, generating initial token')
    generateNewToken()
  }, [])

  return (
    <div className="ctc-interface">
      {/* Header */}
      <header className="header">
        <div className="header-title">
          <h1>Fly In Visualizer</h1>
          <p><a href='https://github.com/dde-fite'>dde-fite</a></p>
        </div>
        <div className="header-info">
          {hasSimulation && <span className="turn-display">Turn: {currentTurn}</span>}
          <button className="token-btn" onClick={() => setShowTokenModal(true)}>
            Token
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <div className="main-layout">
        {/* Left Panel */}
        <aside className="left-panel">
          <MapUploader onMapUploaded={handleMapUploaded} isLoading={isLoading} />

          {hasSimulation && (
            <Controls onAdvanceSteps={handleAdvanceSteps} isLoading={isLoading} />
          )}

          {error && <div className="error-message">{error}</div>}
        </aside>

        {/* Center Panel */}
        <main className="center-panel">
          {!hasSimulation ? (
            <div className="empty-state">
              <p>Upload a map file to begin</p>
            </div>
          ) : (
            <SimulationCanvas simulation={simulationWithToken!.data} token={simulationWithToken!.token} />
          )}
        </main>

        {/* Right Panel */}
        <aside className="right-panel">
          {hasSimulation && (
            <div className="info-section">
              <h3>Network Status</h3>
              <div className="status-item">
                <span>Hubs:</span>
                <strong>{simulationWithToken!.data.hubs.length}</strong>
              </div>
              <div className="status-item">
                <span>Connections:</span>
                <strong>{simulationWithToken!.data.connections.length}</strong>
              </div>
              <div className="status-item">
                <span>Active Drones:</span>
                <strong>{simulationWithToken!.data.drones.length}</strong>
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* Token Modal */}
      {showTokenModal && (
        <div className="modal-overlay" onClick={() => setShowTokenModal(false)}>
          <TokenDisplay token={token} onClose={() => setShowTokenModal(false)} />
        </div>
      )}
    </div>
  )
}

export default App

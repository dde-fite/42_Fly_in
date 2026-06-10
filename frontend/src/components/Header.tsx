import { useSessionStore } from '../store/sessionStore'
import MapUploader from './MapUploader'
import TurnControls from './TurnControls'

export default function Header(
    hasSimulation: boolean,
    currentTurn: number,
    handleMapUploaded: (file: File) => void,
    handleAdvanceSteps,
    setShowTokenModal: (arg0: boolean) => void,

) {
  const isLoading = useSessionStore(state => state.isLoading)
  return(
    <header className="h-24 grid grid-cols-7 grid-rows-1 gap-4 bg-linear-to-l from-fuchsia-600 to-gray-900 shadow-lg border-b border-gray-950">
        <div className='col-span-6 flex gap-10 items-center py-3 px-6'>
          <div>
            <h1 className="text-white text-2xl">Fly In Visualizer</h1>
            <a href='https://github.com/dde-fite'><p className="text-fuchsia-400 hover:underline">dde-fite</p></a>
          </div>
          <div className='flex gap-6'>
            <MapUploader onMapUploaded={handleMapUploaded} isLoading={isLoading} />
            <button
              className="relative overflow-hidden px-5 py-2.5 bg-gray-900 text-white rounded transition-all duration-300 cursor-pointer hover:bg-neutral-800 hover:ring-4 hover:ring-neutral-800 hover:ring-offset-1 active:ring-0" 
              onClick={() => setShowTokenModal(true)}
            >
              <span className="relative">Token</span>
            </button>
          </div>
        </div>
        <div className='col-start-7'>
          {hasSimulation && (
            <TurnControls currentTurn={currentTurn} onAdvanceSteps={handleAdvanceSteps} isLoading={isLoading} />
          )}
        </div>
    </header>
  )
}
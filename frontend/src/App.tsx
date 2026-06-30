import { useEffect } from "react"
import Header from "./components/Header"
import SimulationCanvas from "./components/SimulationCanvas"
import { useSessionStore } from "./store/sessionStore"
import { useSimulationStore } from "./store/simulationStore"

const RETRY_INTERVAL_MS = 5000

function App() {
	const simulation = useSimulationStore(state => state.simulation)
	const fetchToken = useSessionStore(state => state.fetchToken)
	const error = useSessionStore(state => state.error)
	const isOffline = useSessionStore(state => state.isOffline)

	useEffect(() => {
		fetchToken()
	}, [fetchToken])

	useEffect(() => {
		if (!isOffline) return
		const id = setInterval(fetchToken, RETRY_INTERVAL_MS)
		return () => clearInterval(id)
	}, [isOffline, fetchToken])

	return (
		<div className='flex flex-col h-screen overflow-hidden'>
			<Header />

			<div className='relative bg-black flex-1 overflow-hidden'>
				{isOffline && (
					<div className='bg-yellow-500/10 border border-yellow-500/60 text-yellow-300 px-3 py-3 rounded text-sm mt-4 mx-4 flex items-center gap-2'>
						<span className='inline-block w-2 h-2 rounded-full bg-yellow-400 animate-pulse' />
						Backend offline — retrying…
					</div>
				)}
				{error && (
					<div className='bg-red-500/10 border border-red-500 text-[#ff7961] px-3 py-3 rounded text-sm mt-4 mx-4'>
						{error}
					</div>
				)}

				<main className='relative h-full'>
					{!simulation ? (
						<div className='flex items-center justify-center h-full text-gray-500 text-xl'>
							<p>Upload a map file to begin</p>
						</div>
					) : (
						<SimulationCanvas simulation={simulation} />
					)}
				</main>
			</div>
		</div>
	)
}

export default App

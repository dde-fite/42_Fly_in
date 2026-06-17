import { useEffect } from "react"
import Header from "./components/Header"
import SimulationCanvas from "./components/SimulationCanvas"
import { useSessionStore } from "./store/sessionStore"
import { useSimulationStore } from "./store/simulationStore"

function App() {
	const simulation = useSimulationStore(state => state.simulation)
	const fetchToken = useSessionStore(state => state.fetchToken)
	const error = useSessionStore(state => state.error)

	useEffect(() => {
		fetchToken()
	}, [fetchToken])

	return (
		<div className='flex flex-col h-screen overflow-hidden'>
			<Header />

			<div className='relative bg-black flex-1 overflow-hidden'>
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

				{simulation && (
					<aside className='absolute top-4 right-4 p-1 overflow-y-auto'>
						<div className='bg-green-500/10 border border-green-900 rounded p-4'>
							<h3 className='m-0 mb-3 text-green-400 text-[0.95rem] uppercase tracking-widest'>
								Network Status
							</h3>
							<div className='flex justify-between py-2 border-b border-green-900/30 text-sm'>
								<span>Hubs:</span>
								<strong className='text-green-400 font-bold'>
									{Object.keys(simulation.hubs).length}
								</strong>
							</div>
							<div className='flex justify-between py-2 border-b border-green-900/30 text-sm'>
								<span>Connections:</span>
								<strong className='text-green-400 font-bold'>
									{Object.keys(simulation.connections).length}
								</strong>
							</div>
							<div className='flex justify-between py-2 text-sm'>
								<span>Active Drones:</span>
								<strong className='text-green-400 font-bold'>
									{Object.keys(simulation.drones).length}
								</strong>
							</div>
						</div>
					</aside>
				)}
			</div>
		</div>
	)
}

export default App

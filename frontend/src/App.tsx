import { useEffect } from "react";
import Header from "./components/Header";
import SimulationCanvas from "./components/SimulationCanvas";
import { useSessionStore } from "./store/sessionStore";
import { useSimulationStore } from "./store/simulationStore";

function App() {
	const simulation = useSimulationStore((state) => state.simulation);
	const fetchToken = useSessionStore((state) => state.fetchToken);
	const error = useSessionStore((state) => state.error);

	useEffect(() => {
		fetchToken();
	}, [fetchToken]);

	return (
		<div className="flex flex-col h-screen overflow-hidden">
			<Header />

			<div className="relative bg-black flex-1 overflow-hidden">
				{error && (
					<div className="bg-red-500/10 border border-red-500 text-[#ff7961] px-3 py-3 rounded text-sm mt-4 mx-4">
						{error}
					</div>
				)}

				<main className="relative h-full">
					{!simulation ? (
						<div className="flex items-center justify-center h-full text-gray-500 text-xl">
							<p>Upload a map file to begin</p>
						</div>
					) : (
						<SimulationCanvas simulation={simulation} />
					)}
				</main>
			</div>
		</div>
	);
}

export default App;

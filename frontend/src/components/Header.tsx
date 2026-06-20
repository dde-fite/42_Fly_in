import { useEffect, useRef, useState } from "react"
import useKeypress from "../hooks/useKeypress"
import { Player, usePlayback } from "../hooks/usePlayback"
import { useSessionStore } from "../store/sessionStore"
import { useSimulationStore } from "../store/simulationStore"
import AppMenuBar from "./header/AppMenuBar"
import type { Menu } from "./header/menuTypes"
import NetworkStatus from "./header/NetworkStatus"
import PlaybackControls from "./header/PlaybackControls"
import TokenDisplay from "./TokenDisplay"

export default function Header() {
	const [openMenu, setOpenMenu] = useState<string | null>(null)
	const [showToken, setShowToken] = useState(false)

	const simulation = useSimulationStore(state => state.simulation)
	const newSimulation = useSimulationStore(state => state.newSimulation)
	const clearSimulation = useSimulationStore(state => state.clearSimulation)
	const advanceSimulation = useSimulationStore(state => state.advanceSimulation)
	const requestFitView = useSimulationStore(state => state.requestFitView)
	const isLoading = useSessionStore(state => state.isLoading)

	const hasSimulation = simulation !== null
	const { player, setPlayer, togglePlay } = usePlayback(
		hasSimulation,
		advanceSimulation,
	)

	const fileInputRef = useRef<HTMLInputElement>(null)

	// Close menu on outside click
	useEffect(() => {
		if (!openMenu) return
		const close = () => setOpenMenu(null)
		document.addEventListener("click", close)
		return () => document.removeEventListener("click", close)
	}, [openMenu])

	useKeypress(
		" ",
		() => {
			if (!hasSimulation) return
			togglePlay()
		},
		{ preventDefault: true },
	)

	useKeypress(
		"ArrowRight",
		e => {
			if (!hasSimulation || isLoading) return
			advanceSimulation(e.shiftKey ? 10 : 1)
		},
		{ preventDefault: true },
	)

	useKeypress("f", () => {
		if (!hasSimulation) return
		requestFitView()
	})

	useKeypress("Escape", () => {
		if (showToken) setShowToken(false)
	})

	const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
		const file = e.currentTarget.files?.[0]
		if (file?.name.endsWith(".txt")) newSimulation(file)
		else if (file) alert("Please select a .txt file")
		e.currentTarget.value = ""
	}

	const close = (fn: () => void) => () => {
		fn()
		setOpenMenu(null)
	}

	const menus: Menu[] = [
		{
			id: "archivo",
			label: "Archivo",
			items: [
				{
					label: "Nueva simulación",
					shortcut: "Ctrl+O",
					onClick: close(() => fileInputRef.current?.click()),
				},
				{
					label: "Cerrar simulación",
					onClick: close(clearSimulation),
					disabled: !hasSimulation,
				},
				{ separator: true },
				{
					label: "Token…",
					onClick: close(() => setShowToken(true)),
				},
			],
		},
		{
			id: "simulacion",
			label: "Simulación",
			disabled: !hasSimulation,
			items: [
				{
					label: "Siguiente turno",
					shortcut: "→",
					onClick: close(() => advanceSimulation(1)),
					disabled: isLoading || !hasSimulation,
				},
				{
					label: "Avanzar 10 turnos",
					shortcut: "Shift+→",
					onClick: close(() => advanceSimulation(10)),
					disabled: isLoading || !hasSimulation,
				},
				{ separator: true },
				{
					label: player === Player.PAUSE ? "Reproducir" : "Pausar",
					shortcut: "Espacio",
					onClick: close(togglePlay),
					disabled: !hasSimulation,
				},
				{
					label: "Velocidad rápida",
					onClick: close(() => setPlayer(Player.FAST)),
					disabled: !hasSimulation,
				},
			],
		},
		{
			id: "vista",
			label: "Vista",
			disabled: !hasSimulation,
			items: [
				{
					label: "Ajustar vista",
					shortcut: "F",
					onClick: close(requestFitView),
					disabled: !hasSimulation,
				},
			],
		},
	]

	return (
		<>
			<header className='h-24 grid grid-cols-7 grid-rows-1 gap-4 bg-linear-to-l from-fuchsia-600 to-gray-900 shadow-lg border-b border-gray-950'>
				{/* Left: title + menu buttons */}
				<div className='col-span-6 flex gap-10 items-center py-3 px-6'>
					<div>
						<h1 className='text-white text-2xl'>Fly In Visualizer</h1>
						<a href='https://github.com/dde-fite'>
							<p className='text-fuchsia-400 hover:underline'>dde-fite</p>
						</a>
					</div>

					<AppMenuBar
						menus={menus}
						openMenu={openMenu}
						setOpenMenu={setOpenMenu}
					/>

					{hasSimulation && simulation && (
						<div className='ml-auto'>
							<NetworkStatus
								hubs={Object.keys(simulation.hubs).length}
								connections={Object.keys(simulation.connections).length}
								drones={Object.keys(simulation.drones).length}
							/>
						</div>
					)}
				</div>

				{/* Right: turn counter + playback controls */}
				<div className='col-start-7 flex items-center justify-center'>
					{hasSimulation && (
						<PlaybackControls
							turn={simulation.turn}
							player={player}
							setPlayer={setPlayer}
						/>
					)}
				</div>
			</header>

			{/* Hidden file input */}
			<input
				ref={fileInputRef}
				type='file'
				accept='.txt'
				onChange={handleFileSelect}
				style={{ display: "none" }}
			/>

			{/* Token modal */}
			{showToken && (
				<div className='fixed inset-0 bg-black/70 flex items-center justify-center z-[1000]'>
					<button
						type='button'
						aria-label='Cerrar'
						className='absolute inset-0 cursor-default'
						onClick={() => setShowToken(false)}
					/>
					<div className='relative z-10'>
						<TokenDisplay onClose={() => setShowToken(false)} />
					</div>
				</div>
			)}
		</>
	)
}

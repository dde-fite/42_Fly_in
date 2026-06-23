interface NetworkStatusProps {
	hubs: number
	connections: number
	drones: number
}

function Stat({ label, value }: { label: string; value: number }) {
	return (
		<div className='flex flex-col items-center leading-tight'>
			<span className='text-fuchsia-300 text-2xl font-bold'>{value}</span>
			<span className='text-fuchsia-100/70 text-[0.65rem] uppercase tracking-widest'>
				{label}
			</span>
		</div>
	)
}

// Compact network counters shown in the header (replaces the old canvas-overlay
// Network Status panel).
export default function NetworkStatus({
	hubs,
	connections,
	drones,
}: NetworkStatusProps) {
	return (
		<div className='flex items-center gap-6'>
			<Stat
				label='Hubs'
				value={hubs}
			/>
			<Stat
				label='Conns'
				value={connections}
			/>
			<Stat
				label='Drones'
				value={drones}
			/>
		</div>
	)
}

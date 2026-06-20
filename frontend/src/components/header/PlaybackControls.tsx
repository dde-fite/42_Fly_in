import {
	IconPlayerPauseFilled,
	IconPlayerPlayFilled,
	IconPlayerTrackNextFilled,
} from "@tabler/icons-react"
import { useId } from "react"
import { Player } from "../../hooks/usePlayback"

interface PlaybackControlsProps {
	turn: number
	player: Player
	setPlayer: (player: Player) => void
}

const labelClass =
	"flex items-center justify-center p-2 rounded peer-checked:bg-gray-900 hover:bg-neutral-800 hover:ring-3 hover:ring-neutral-800 hover:ring-offset-2 active:ring-0 transition-all duration-300 cursor-pointer"

const OPTIONS = [
	{ id: "pause", value: Player.PAUSE, Icon: IconPlayerPauseFilled },
	{ id: "play", value: Player.PLAY, Icon: IconPlayerPlayFilled },
	{ id: "fast", value: Player.FAST, Icon: IconPlayerTrackNextFilled },
] as const

export default function PlaybackControls({
	turn,
	player,
	setPlayer,
}: PlaybackControlsProps) {
	const uid = useId()
	return (
		<div className='flex flex-col items-center justify-center px-5 py-2.5 bg-gray-950/45'>
			<div className='flex items-center gap-2'>
				<p className='text-white text-sm'>Turno</p>
				<p className='text-white text-2xl'>{turn}</p>
			</div>
			<div className='flex gap-4'>
				{OPTIONS.map(({ id, value, Icon }) => (
					<div key={id}>
						<input
							className='hidden peer'
							type='radio'
							name={`player-${uid}`}
							id={`${uid}-${id}`}
							checked={player === value}
							onChange={() => setPlayer(value)}
						/>
						<label
							className={labelClass}
							htmlFor={`${uid}-${id}`}>
							<Icon />
						</label>
					</div>
				))}
			</div>
		</div>
	)
}

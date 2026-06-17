import {
	IconPlayerPauseFilled,
	IconPlayerPlayFilled,
	IconPlayerTrackNextFilled,
} from "@tabler/icons-react"
import { Player } from "../../hooks/usePlayback"

interface PlaybackControlsProps {
	turn: number
	player: Player
	setPlayer: (player: Player) => void
}

const labelClass =
	"flex items-center justify-center p-2 rounded peer-checked:bg-gray-900 hover:bg-neutral-800 hover:ring-3 hover:ring-neutral-800 hover:ring-offset-2 active:ring-0 transition-all duration-300 cursor-pointer"

export default function PlaybackControls({
	turn,
	player,
	setPlayer,
}: PlaybackControlsProps) {
	return (
		<div className='flex flex-col items-center justify-center px-5 py-2.5 bg-gray-950/45'>
			<div className='flex items-center gap-2'>
				<p className='text-white text-sm'>Turno</p>
				<p className='text-white text-2xl'>{turn}</p>
			</div>
			<div className='flex gap-4'>
				<div>
					<input
						className='hidden peer'
						type='radio'
						name='player'
						id='pause'
						checked={player === Player.PAUSE}
						onChange={() => setPlayer(Player.PAUSE)}
					/>
					<label
						className={labelClass}
						htmlFor='pause'>
						<IconPlayerPauseFilled />
					</label>
				</div>
				<div>
					<input
						className='hidden peer'
						type='radio'
						name='player'
						id='play'
						checked={player === Player.PLAY}
						onChange={() => setPlayer(Player.PLAY)}
					/>
					<label
						className={labelClass}
						htmlFor='play'>
						<IconPlayerPlayFilled />
					</label>
				</div>
				<div>
					<input
						className='hidden peer'
						type='radio'
						name='player'
						id='fast'
						checked={player === Player.FAST}
						onChange={() => setPlayer(Player.FAST)}
					/>
					<label
						className={labelClass}
						htmlFor='fast'>
						<IconPlayerTrackNextFilled />
					</label>
				</div>
			</div>
		</div>
	)
}

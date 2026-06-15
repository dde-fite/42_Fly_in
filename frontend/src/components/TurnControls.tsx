import { useEffect, useState } from 'react'
import { IconPlayerPauseFilled, IconPlayerPlayFilled, IconPlayerTrackNextFilled } from '@tabler/icons-react';
import { useSessionStore } from '../store/sessionStore';
import { useSimulationStore } from '../store/simulationStore'
import useKeypress from '../hooks/useKeypress';

const TURN_DELAY = 1000

enum PlayerStates {
  PAUSE = "pause",
  PLAY = "play",
  FAST_PLAY = "fast_play"
}

enum StatesMultiplier {
  "pause" = 0,
  "play" = 1,
  "fast_play" = 3
}

interface ControlsProps {
  onAdvanceSteps: (steps: number) => void
}

export default function TurnControls({ onAdvanceSteps }: ControlsProps) {
  const isLoading = useSessionStore(state => state.isLoading)
  const simulation = useSimulationStore(state => state.simulation)
  const currentTurn = simulation?.data.turn ?? 0

  const [player, setPlayer] = useState<PlayerStates>(PlayerStates.PAUSE)

  const handleChange = (e) => {
    setPlayer(e.target.value)
  }

  const handleToggle = () => {
    if (player === PlayerStates.PAUSE) {
      setPlayer(PlayerStates.PLAY)
    }
    else {
      setPlayer(PlayerStates.PAUSE)
    }
  }

  useKeypress(" ", handleToggle)

  useEffect(() => {
    if (player === PlayerStates.PAUSE) return
    if (isLoading) return

    const multiplier = StatesMultiplier[player]
    const delay = TURN_DELAY / multiplier

    const timeout = setTimeout(() => {
      onAdvanceSteps(1)
    }, delay)

    return () => clearTimeout(timeout)
  }, [player, isLoading])

  return (
    <div className="flex flex-col items-center justify-center px-5 py-2.5 bg-gray-950/45">
      <div className='flex items-center gap-2'>
        <p>Turn</p>
        <p className='text-2xl'>{currentTurn}</p>
      </div>
      <div className="flex gap-4">
      <div>
        <input
          className="hidden peer"
          type="radio"
          name="player"
          id={PlayerStates.PAUSE}
          value={PlayerStates.PAUSE}
          checked={player === PlayerStates.PAUSE}
          onChange={handleChange}
        />
        <label
          className="flex items-center justify-center p-2 rounded peer-checked:bg-gray-900 peer-hover:bg-neutral-800 peer-hover:ring-3 peer-hover:ring-offset-2 peer-hover:ring-neutral-800 peer-active:ring-0  transition-all duration-300 cursor-pointer"
          htmlFor={PlayerStates.PAUSE}
        >
          <IconPlayerPauseFilled />
        </label>
      </div>
      <div>
        <input
          className="hidden peer"
          type="radio"
          name="player"
          id={PlayerStates.PLAY}
          value={PlayerStates.PLAY}
          checked={player === PlayerStates.PLAY}
          onChange={handleChange}
        />
        <label
          className="flex items-center justify-center p-2 rounded peer-checked:bg-gray-900 peer-hover:bg-neutral-800 peer-hover:ring-3 peer-hover:ring-offset-2 peer-hover:ring-neutral-800 peer-active:ring-0  transition-all duration-300 cursor-pointer"
          htmlFor={PlayerStates.PLAY}
        >
          <IconPlayerPlayFilled />
        </label>
      </div>
      <div>
        <input
          className="hidden peer"
          type="radio"
          name="player"
          id={PlayerStates.FAST_PLAY}
          value={PlayerStates.FAST_PLAY}
          checked={player === PlayerStates.FAST_PLAY}
          onChange={handleChange}
        />
        <label
          className="flex items-center justify-center p-2 rounded peer-checked:bg-gray-900 peer-hover:bg-neutral-800 peer-hover:ring-3 peer-hover:ring-offset-2 peer-hover:ring-neutral-800 peer-active:ring-0  transition-all duration-300 cursor-pointer"
          htmlFor={PlayerStates.FAST_PLAY}
        >
          <IconPlayerTrackNextFilled />
        </label>
      </div>
    </div>
    </div>
  )
}

import { IconMaximize, IconZoomIn, IconZoomOut } from "@tabler/icons-react"

interface CanvasToolbarProps {
	scale: number
	onFit: () => void
	onZoomIn: () => void
	onZoomOut: () => void
}

const iconButton =
	"flex items-center justify-center text-amber-200 p-1.5 rounded cursor-pointer border-none bg-zinc-800 hover:bg-zinc-700 hover:text-amber-300 hover:shadow-[0_0_8px_rgba(255,213,79,0.35)] transition-all"

export default function CanvasToolbar({
	scale,
	onFit,
	onZoomIn,
	onZoomOut,
}: CanvasToolbarProps) {
	return (
		<div className='absolute bottom-4 right-4 flex gap-2 items-center bg-[#1a1a1a]/80 p-2 border border-amber-500/50 rounded backdrop-blur-sm z-10'>
			<div className='text-amber-300 text-sm font-bold min-w-20 text-right pr-1'>
				{scale.toFixed(0)}x
			</div>
			<button
				className={iconButton}
				onClick={onZoomOut}
				title='Zoom out'
				type='button'>
				<IconZoomOut size={18} />
			</button>
			<button
				className={iconButton}
				onClick={onZoomIn}
				title='Zoom in'
				type='button'>
				<IconZoomIn size={18} />
			</button>
			<button
				className={iconButton}
				onClick={onFit}
				title='Fit to view'
				type='button'>
				<IconMaximize size={18} />
			</button>
		</div>
	)
}

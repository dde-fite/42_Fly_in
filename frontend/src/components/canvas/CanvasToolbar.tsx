import { IconMaximize, IconZoomIn, IconZoomOut } from "@tabler/icons-react"

interface CanvasToolbarProps {
	scale: number
	onFit: () => void
	onZoomIn: () => void
	onZoomOut: () => void
}

const iconButton =
	"flex items-center justify-center text-amber-200 p-1.5 rounded cursor-pointer border-none bg-zinc-800 hover:bg-zinc-700 hover:text-amber-300 hover:shadow-[0_0_8px_rgba(255,213,79,0.35)] transition-all"

const BUTTONS = [
	{ Icon: IconZoomOut, title: "Zoom out", action: "zoomOut" },
	{ Icon: IconZoomIn, title: "Zoom in", action: "zoomIn" },
	{ Icon: IconMaximize, title: "Fit to view", action: "fit" },
] as const

export default function CanvasToolbar({
	scale,
	onFit,
	onZoomIn,
	onZoomOut,
}: CanvasToolbarProps) {
	const handlers = { zoomOut: onZoomOut, zoomIn: onZoomIn, fit: onFit }
	return (
		<div className='absolute bottom-4 right-4 flex gap-2 items-center bg-[#1a1a1a]/80 p-2 border border-amber-500/50 rounded backdrop-blur-sm z-10'>
			<div className='text-amber-300 text-sm font-bold min-w-20 text-right pr-1'>
				{scale.toFixed(0)}x
			</div>
			{BUTTONS.map(({ Icon, title, action }) => (
				<button
					key={title}
					className={iconButton}
					onClick={handlers[action]}
					title={title}
					aria-label={title}
					type='button'>
					<Icon size={18} />
				</button>
			))}
		</div>
	)
}

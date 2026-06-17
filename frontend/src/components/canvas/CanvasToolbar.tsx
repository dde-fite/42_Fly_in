interface CanvasToolbarProps {
	scale: number
	onFit: () => void
}

export default function CanvasToolbar({ scale, onFit }: CanvasToolbarProps) {
	return (
		<div className='absolute top-4 left-4 flex gap-2 items-center bg-[#1a1a1a]/80 p-2 border border-green-900 rounded backdrop-blur-sm z-10'>
			<button
				className='bg-green-900 text-white px-3 py-1.5 rounded text-sm font-bold cursor-pointer hover:bg-green-500 hover:shadow-[0_0_8px_rgba(76,175,80,0.3)] transition-all border-none'
				onClick={onFit}
				title='Fit to view'
				type='button'>
				Fit
			</button>
			<div className='text-green-400 text-sm font-bold min-w-20'>
				Scale: {scale.toFixed(0)}x
			</div>
		</div>
	)
}

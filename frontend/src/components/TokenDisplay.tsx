import { useState } from "react"
import { useSessionStore } from "../store/sessionStore"

interface TokenDisplayProps {
	onClose: () => void
}

export default function TokenDisplay({ onClose }: TokenDisplayProps) {
	const [copied, setCopied] = useState(false)
	const token = useSessionStore(state => state.token) ?? ""

	const copyToClipboard = async () => {
		try {
			await navigator.clipboard.writeText(token)
			setCopied(true)
			setTimeout(() => setCopied(false), 2000)
		} catch (err) {
			console.error("Failed to copy:", err)
		}
	}

	return (
		<div
			className='bg-black/70 rounded max-w-lg w-[90%] backdrop-blur-sm'
			onClick={e => e.stopPropagation()}>
			<div className='bg-gradient-to-br from-[#1a1a1a] to-[#0a0a0a] border-2 border-green-900 rounded overflow-hidden'>
				<div className='bg-gradient-to-br from-green-900 to-green-950 px-4 py-4 border-b border-green-950 flex justify-between items-center'>
					<h2 className='m-0 text-white text-xl tracking-wide'>
						Session Token
					</h2>
					<button
						type='button'
						className='bg-transparent border-none text-white text-2xl cursor-pointer hover:scale-110 transition-transform leading-none'
						onClick={onClose}>
						✕
					</button>
				</div>

				<div className='p-6'>
					<p className='mb-3 text-green-400 text-sm uppercase tracking-wide'>
						Current Token:
					</p>
					<div className='bg-[#0a0a0a] border border-green-900 rounded p-4 mb-4 flex gap-2 items-center'>
						<code className='flex-1 text-green-400 font-mono text-sm break-all leading-relaxed select-all'>
							{token}
						</code>
						<button
							type='button'
							className='bg-green-900 text-white border-none px-3 py-2 rounded text-sm font-bold whitespace-nowrap cursor-pointer hover:bg-green-400 hover:text-black transition-all'
							onClick={copyToClipboard}>
							{copied ? "✓ Copied" : "Copy"}
						</button>
					</div>
					<p className='text-sm text-gray-400 leading-relaxed'>
						This token identifies your simulation session. Use it to continue
						working with the same map and drone configuration.
					</p>
				</div>

				<div className='px-4 py-4 border-t border-green-900 flex justify-end'>
					<button
						type='button'
						className='bg-gradient-to-br from-green-400 to-green-900 text-black border-none px-6 py-2 rounded font-bold text-sm uppercase tracking-wide cursor-pointer hover:shadow-[0_0_10px_rgba(76,175,80,0.3)] transition-all'
						onClick={onClose}>
						OK
					</button>
				</div>
			</div>
		</div>
	)
}

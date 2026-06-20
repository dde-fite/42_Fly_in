import type { CSSProperties, ReactNode } from "react"
import {
	closeButton,
	detailHeader,
	detailLabel,
	detailPanel,
	detailRow,
	detailValue,
} from "./panelStyles"

interface DetailPanelProps {
	title: string
	onClose: () => void
	// Position utilities, e.g. "right-4 top-4".
	position: string
	panelStyle?: CSSProperties
	headerClassName?: string
	headerStyle?: CSSProperties
	titleClassName?: string
	children: ReactNode
}

// Floating detail-panel shell shared by the hub and connection panels: outer
// frame, coloured header with title + close button, and a padded body.
export default function DetailPanel({
	title,
	onClose,
	position,
	panelStyle,
	headerClassName = detailHeader,
	headerStyle,
	titleClassName = "",
	children,
}: DetailPanelProps) {
	return (
		<div
			className={`${detailPanel} ${position}`}
			style={panelStyle}>
			<div
				className={headerClassName}
				style={headerStyle}>
				<h4
					className={`m-0 text-white text-[0.95rem] tracking-wide ${titleClassName}`}>
					{title}
				</h4>
				<button
					className={closeButton}
					onClick={onClose}
					type='button'
					aria-label='Close'>
					<span aria-hidden='true'>✕</span>
				</button>
			</div>
			<div className='p-3'>{children}</div>
		</div>
	)
}

// A single label/value line inside a detail panel.
export function DetailRow({
	label,
	value,
}: {
	label: string
	value: ReactNode
}) {
	return (
		<div className={detailRow}>
			<span className={detailLabel}>{label}</span>
			<strong className={detailValue}>{value}</strong>
		</div>
	)
}

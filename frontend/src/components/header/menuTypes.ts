type MenuOptionItem = {
	label: string
	shortcut?: string
	onClick: () => void
	disabled?: boolean
}
type SeparatorItem = { separator: true }
export type MenuItem = MenuOptionItem | SeparatorItem

export type Menu = {
	id: string
	label: string
	disabled?: boolean
	items: MenuItem[]
}

export function isSeparator(item: MenuItem): item is SeparatorItem {
	return "separator" in item
}

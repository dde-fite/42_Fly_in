import { isSeparator, type Menu } from "./menuTypes"

interface AppMenuBarProps {
	menus: Menu[]
	openMenu: string | null
	setOpenMenu: (id: string | null) => void
}

export default function AppMenuBar({
	menus,
	openMenu,
	setOpenMenu,
}: AppMenuBarProps) {
	return (
		<div className='flex gap-3'>
			{menus.map(menu => (
				<div
					key={menu.id}
					className='relative'
					onClick={e => e.stopPropagation()}>
					<button
						type='button'
						className='relative overflow-hidden px-5 py-2.5 bg-gray-900 text-white rounded transition-all duration-300 cursor-pointer hover:bg-neutral-800 hover:ring-4 hover:ring-neutral-800 hover:ring-offset-1 active:ring-0 disabled:opacity-40 disabled:cursor-default disabled:ring-0'
						disabled={menu.disabled}
						onClick={() => setOpenMenu(openMenu === menu.id ? null : menu.id)}>
						<span className='relative flex items-center gap-1.5'>
							{menu.label}
							<svg
								width='10'
								height='6'
								viewBox='0 0 10 6'
								fill='currentColor'
								className='opacity-60'>
								<path d='M0 0l5 6 5-6z' />
							</svg>
						</span>
					</button>

					{openMenu === menu.id && (
						<div className='absolute top-[calc(100%+6px)] left-0 min-w-[220px] bg-zinc-900 border border-zinc-700 rounded-md shadow-[0_8px_24px_rgba(0,0,0,0.7)] z-[200] py-1'>
							{menu.items.map((item, i) =>
								isSeparator(item) ? (
									<div
										key={i}
										className='h-px bg-zinc-800 my-1 mx-2'
									/>
								) : (
									<button
										key={i}
										type='button'
										className='group flex items-center w-full px-4 py-1.5 text-[13.5px] text-zinc-200 bg-transparent border-none cursor-pointer text-left whitespace-nowrap hover:bg-violet-700 hover:text-white disabled:text-zinc-600 disabled:cursor-default transition-colors duration-75'
										disabled={item.disabled}
										onClick={item.onClick}>
										{item.label}
										{item.shortcut && (
											<span className='ml-auto pl-6 text-[11.5px] text-zinc-500 group-hover:text-white/55'>
												{item.shortcut}
											</span>
										)}
									</button>
								),
							)}
						</div>
					)}
				</div>
			))}
		</div>
	)
}

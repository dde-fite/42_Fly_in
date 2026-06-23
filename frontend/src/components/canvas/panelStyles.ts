// Shared Tailwind class strings for the floating detail panels.
export const detailPanel =
	"absolute bg-gradient-to-br from-[#1a1a1a] to-[#0a0a0a] border-2 border-fuchsia-900 rounded w-[280px] shadow-[0_0_20px_rgba(192,38,211,0.25)] z-20"
// Default header: the app header's purple, a bit blacker. HubDetailPanel
// overrides this with the station's own colour when the API specifies one.
export const detailHeader =
	"px-3 py-3 flex justify-between items-center border-b border-black/40 bg-gradient-to-br from-fuchsia-950 to-black"
export const detailRow =
	"flex justify-between py-2 border-b border-fuchsia-900/30 text-sm last:border-b-0"
export const detailLabel = "text-fuchsia-300 uppercase tracking-wide"
export const detailValue = "text-white wrap-break-word text-right"
export const closeButton =
	"bg-transparent border-none text-white text-xl cursor-pointer hover:scale-110 transition-transform p-0 leading-none"

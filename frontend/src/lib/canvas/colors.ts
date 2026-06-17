// Stable per-drone color, derived from a hash of the drone id and memoized so a
// drone keeps the same color across redraws.
export function createDroneColorCache(): (droneId: string) => string {
	const cache = new Map<string, string>()
	return (droneId: string): string => {
		const cached = cache.get(droneId)
		if (cached) return cached

		let hash = 0
		for (let i = 0; i < droneId.length; i++) {
			const char = droneId.charCodeAt(i)
			hash = (hash << 5) - hash + char
			hash = hash & hash
		}
		const hue = Math.abs(hash) % 360
		const saturation = 70 + (Math.abs(hash) % 30)
		const color = `hsl(${hue}, ${saturation}%, 50%)`
		cache.set(droneId, color)
		return color
	}
}

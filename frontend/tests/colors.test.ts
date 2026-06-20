import { describe, expect, it } from "vitest"
import { createDroneColorCache } from "../src/canvas/colors"

describe("createDroneColorCache", () => {
	it("returns a stable colour for the same id", () => {
		const colorOf = createDroneColorCache()
		const first = colorOf("drone-1")
		expect(colorOf("drone-1")).toBe(first)
	})

	it("derives the colour deterministically from the id hash", () => {
		expect(createDroneColorCache()("a")).toBe("hsl(97, 77%, 50%)")
	})

	it("is deterministic across cache instances", () => {
		expect(createDroneColorCache()("x")).toBe(createDroneColorCache()("x"))
	})
})

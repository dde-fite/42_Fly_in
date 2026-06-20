import { describe, expect, it } from "vitest"
import { INFO, isRainbow, resolveHubColor } from "../src/canvas/palette"

describe("resolveHubColor", () => {
	it("falls back to the info colour when unset", () => {
		expect(resolveHubColor(undefined)).toBe(INFO)
	})

	it("passes a plain colour through unchanged", () => {
		expect(resolveHubColor("#abcdef")).toBe("#abcdef")
	})

	it("animates the rainbow keyword in any case", () => {
		expect(resolveHubColor("rainbow")).toMatch(/^hsl\(/)
		expect(resolveHubColor("RAINBOW")).toMatch(/^hsl\(/)
	})
})

describe("isRainbow", () => {
	it("detects the rainbow keyword case-insensitively", () => {
		expect(isRainbow("rainbow")).toBe(true)
		expect(isRainbow("RaInBoW")).toBe(true)
	})

	it("is false for other values", () => {
		expect(isRainbow(undefined)).toBe(false)
		expect(isRainbow("#fff")).toBe(false)
	})
})

import { defineConfig } from "vitest/config"

// Standalone test config (kept separate from vite.config.ts so the app build's
// plugin types stay untouched). The suite covers the pure canvas/view/model
// logic, which needs no DOM or JSX transform, so the default "node" environment
// keeps it fast and no Vite plugins are required.
export default defineConfig({
	test: {
		environment: "node",
		include: ["src/**/*.test.ts"],
	},
})

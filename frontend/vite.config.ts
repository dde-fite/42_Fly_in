import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the
  // `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react(), tailwindcss()],
    define: {
      // Provide an explicit app-level constant derived from an env var.
      __FRONTEND_URL__: JSON.stringify(env.FRONTEND_URL),
    },
    // Example: use an env var to set the dev server port conditionally.
    server: {
      port: env.FRONTEND_URL ? Number(env.FRONTEND_URL) : 3000,
    },
  }
})
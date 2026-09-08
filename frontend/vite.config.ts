import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    // Vite's dev server rejects unknown Host headers by default (DNS-rebinding
    // protection). We reach it through Cloudflare Tunnel using a real domain,
    // so that host needs to be explicitly allowed.
    allowedHosts: ["jgms.imjemin.co.kr"],
  },
})

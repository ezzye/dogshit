import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// CI or Docker environments set the CI/E2E flag so the dev server
// only accepts requests from the "frontend" hostname. Local runs can
// use localhost or disable the check.
const inCi = process.env.CI || process.env.E2E;
const allowedHosts = inCi ? ['frontend'] : ['localhost'];

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // or '0.0.0.0'
    port: 5174,
    strictPort: true,
    allowedHosts,
  }
});

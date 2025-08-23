import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './cypress',
  use: {
    baseURL: 'http://localhost:5174',
    headless: true,
  },
  webServer: {
    command: 'npm run dev',
    port: 5174,
    reuseExistingServer: !process.env.CI,
  },
});

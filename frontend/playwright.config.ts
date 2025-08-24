import { defineConfig } from '@playwright/test';

const port = Number(process.env.PORT) || 5174;

export default defineConfig({
  testDir: './playwright',
  use: {
    baseURL: `http://localhost:${port}`,
    headless: true,
  },
  webServer: {
    command: 'npm run dev',
    port,
    reuseExistingServer: !process.env.CI,
  },
});

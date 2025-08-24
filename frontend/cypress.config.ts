import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl:
      process.env.CYPRESS_BASE_URL ||
      `http://localhost:${process.env.PORT || 5174}`,
    supportFile: false,
    specPattern: 'cypress/**/*.spec.ts',
  },
});

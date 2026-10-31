import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import cypress from 'cypress';
import { createServer } from 'vite';

export async function runTests({
  port = process.env.PORT || 0,
  runCypress = (options) => cypress.run(options),
} = {}) {
  if (!/^\d+$/.test(String(port)) || Number(port) > 65535) {
    throw new Error('PORT must be an integer between 0 and 65535.');
  }

  const server = await createServer({
    server: {
      host: '127.0.0.1',
      port: Number(port) || 5174,
      strictPort: Number(port) !== 0,
      open: false,
    },
  });
  const previousBaseUrl = process.env.CYPRESS_BASE_URL;

  try {
    // Listen first: a different process must never satisfy test readiness.
    await server.listen();
    const baseUrl = `http://127.0.0.1:${server.httpServer.address().port}`;
    process.env.CYPRESS_BASE_URL = baseUrl;
    console.log(`Running Cypress against ${baseUrl}`);
    const result = await runCypress({ config: { baseUrl } });
    if (result.status === 'failed' || result.failures) {
      throw new Error(result.message || 'Cypress could not start the test run.');
    }
    return result.totalFailed > 0 ? 1 : 0;
  } finally {
    if (previousBaseUrl === undefined) {
      delete process.env.CYPRESS_BASE_URL;
    } else {
      process.env.CYPRESS_BASE_URL = previousBaseUrl;
    }
    await server.close();
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    process.exitCode = await runTests();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

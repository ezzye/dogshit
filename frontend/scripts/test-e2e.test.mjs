import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { test } from 'node:test';
import { runTests } from './test-e2e.mjs';

async function occupyPort(t, port = 0) {
  const server = createServer((_req, res) => res.end('existing service'));
  server.listen(port, '127.0.0.1');
  await once(server, 'listening');
  t.after(() => new Promise((resolve) => server.close(resolve)));
  return server.address().port;
}

test('starts its own app despite an existing service and stale Cypress URL', async (t) => {
  const occupiedPort = await occupyPort(t, 5174).catch((error) => {
    if (error.code !== 'EADDRINUSE') throw error;
    return occupyPort(t);
  });
  const existingUrl = `http://127.0.0.1:${occupiedPort}`;
  const previousPort = process.env.PORT;
  delete process.env.PORT;
  const previousBaseUrl = process.env.CYPRESS_BASE_URL;
  process.env.CYPRESS_BASE_URL = existingUrl;
  let baseUrl;
  try {
    assert.equal(await runTests({
      runCypress: async ({ config }) => {
        baseUrl = config.baseUrl;
        assert.notEqual(new URL(baseUrl).port, '5174');
        assert.notEqual(new URL(baseUrl).port, String(occupiedPort));
        assert.equal(process.env.CYPRESS_BASE_URL, baseUrl);
        const response = await fetch(baseUrl);
        assert.equal(response.status, 200);
        assert.match(await response.text(), /\/src\/main.tsx/);
        return { totalFailed: 0 };
      },
    }), 0);
    assert.equal(process.env.CYPRESS_BASE_URL, existingUrl);
    assert.equal(await (await fetch(existingUrl)).text(), 'existing service');
    await assert.rejects(fetch(baseUrl));
  } finally {
    if (previousPort === undefined) delete process.env.PORT;
    else process.env.PORT = previousPort;
    if (previousBaseUrl === undefined) delete process.env.CYPRESS_BASE_URL;
    else process.env.CYPRESS_BASE_URL = previousBaseUrl;
  }
});

test('refuses an occupied explicit port without launching Cypress', async (t) => {
  const port = await occupyPort(t);
  let called = false;
  await assert.rejects(runTests({
    port,
    runCypress: async () => { called = true; },
  }), /already in use/);
  assert.equal(called, false);
  assert.equal(await (await fetch(`http://127.0.0.1:${port}`)).text(), 'existing service');
});

test('uses the requested port and propagates failed tests', async () => {
  const reservation = createServer();
  reservation.listen(0, '127.0.0.1');
  await once(reservation, 'listening');
  const port = reservation.address().port;
  await new Promise((resolve) => reservation.close(resolve));
  const previousPort = process.env.PORT;
  process.env.PORT = String(port);
  try {
    assert.equal(await runTests({
      runCypress: async ({ config }) => {
        assert.equal(config.baseUrl, `http://127.0.0.1:${port}`);
        return { totalFailed: 1 };
      },
    }), 1);
  } finally {
    if (previousPort === undefined) delete process.env.PORT;
    else process.env.PORT = previousPort;
  }
  await assert.rejects(fetch(`http://127.0.0.1:${port}`));
});

test('closes the test server when Cypress cannot start', async () => {
  let baseUrl;
  await assert.rejects(runTests({
    port: 0,
    runCypress: async ({ config }) => {
      baseUrl = config.baseUrl;
      return { status: 'failed', message: 'Cypress could not start' };
    },
  }), /Cypress could not start/);
  await assert.rejects(fetch(baseUrl));
});

test('closes the test server when Cypress throws', async () => {
  let baseUrl;
  await assert.rejects(runTests({
    port: 0,
    runCypress: async ({ config }) => {
      baseUrl = config.baseUrl;
      throw new Error('browser crashed');
    },
  }), /browser crashed/);
  await assert.rejects(fetch(baseUrl));
});

test('reports Cypress startup failures without a message', async () => {
  await assert.rejects(runTests({
    port: 0,
    runCypress: async () => ({ failures: 1 }),
  }), /Cypress could not start the test run/);
});

test('rejects invalid ports before launching Cypress', async () => {
  for (const port of ['invalid', -1, 1.5, 65536]) {
    await assert.rejects(runTests({ port }), /PORT must be an integer/);
  }
});

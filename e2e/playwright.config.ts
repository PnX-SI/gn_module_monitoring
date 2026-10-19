import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.GN_BASE_URL ?? 'http://127.0.0.1:4200';

export default defineConfig({
  testDir: './tests',
  // Un compte de test par worker (voir tests/fixtures.ts) : chaque test pose ses propres droits
  // et crée ses données, les tests sont donc indépendants.
  fullyParallel: true,
  workers: Number(process.env.GN_WORKERS ?? 4),
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  timeout: 45_000,
  expect: { timeout: 7_000 },
  use: {
    baseURL,
    locale: 'fr-FR',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'setup', testMatch: /\.setup\.ts/ },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
  ],
});

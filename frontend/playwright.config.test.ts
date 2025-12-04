import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E tests with isolated test environment.
 * Uses different ports to avoid conflicts with development servers.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  timeout: 60000, // 60 seconds per test (for slow-mo videos)
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: 'http://localhost:5174',  // Test frontend port
    trace: 'on-first-retry',
    video: 'on', // Record video for all tests
    screenshot: 'only-on-failure',
    launchOptions: {
      slowMo: 1000, // 1000ms delay between actions (100% slower)
    },
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Don't start servers automatically - the run-e2e-tests.ps1 script handles this
  // webServer: undefined,
});


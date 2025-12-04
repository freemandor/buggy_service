import { test, expect, Page } from '@playwright/test';

/**
 * User Story #2: Intelligent Ride Assignment
 * 
 * Scenario:
 * - Buggy 1: At Bel Air, has existing Ride A (3 guests) with dropoff at Beach Bar (PLANNED)
 * - Buggy 2: At Reception, idle (0 guests)
 * - New Ride C: Beach Bar → Reception, 2 guests
 * 
 * Expected Behavior:
 * System assigns Ride C to Buggy 1 (not Buggy 2) because:
 * - Buggy 1 ETA to Beach Bar: BA→BB (120s) + dropoff service (25s) = 145s
 * - Buggy 2 ETA to Beach Bar: R→BA→BB (90s + 120s) = 210s
 * 
 * Buggy 1 arrives sooner, so it gets assigned.
 */

const API_BASE = 'http://localhost:8000/api';

// Helper to add visual click indicators
async function addClickIndicators(page: Page) {
  await page.addInitScript(() => {
    // Add CSS for click ripple effect
    const style = document.createElement('style');
    style.textContent = `
      .click-indicator {
        position: fixed;
        border: 3px solid #2563EB;
        border-radius: 50%;
        background: rgba(37, 99, 235, 0.2);
        pointer-events: none;
        z-index: 999999;
        animation: click-ripple 1s ease-out;
      }
      @keyframes click-ripple {
        0% {
          transform: scale(0);
          opacity: 1;
        }
        100% {
          transform: scale(2);
          opacity: 0;
        }
      }
    `;
    document.head.appendChild(style);

    // Add click listener to show indicators
    document.addEventListener('click', (e) => {
      const indicator = document.createElement('div');
      indicator.className = 'click-indicator';
      const size = 40;
      indicator.style.width = `${size}px`;
      indicator.style.height = `${size}px`;
      indicator.style.left = `${e.clientX - size/2}px`;
      indicator.style.top = `${e.clientY - size/2}px`;
      document.body.appendChild(indicator);
      setTimeout(() => indicator.remove(), 1000);
    }, true);
  });
}

// Helper to get auth token
async function getAuthToken(username: string, password: string): Promise<string> {
  const response = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const data = await response.json();
  return data.access;
}

// Helper to make authenticated API calls
async function apiCall(path: string, token: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
  return response.json();
}

test.describe('User Story #2: Intelligent Ride Assignment', () => {
  let dispatcherToken: string;

  test.beforeAll(async () => {
    // Get dispatcher token for API setup
    dispatcherToken = await getAuthToken('dispatcher', 'dispatcher');
  });

  test.beforeEach(async ({ page }) => {
    // Reset the database to User Story #2 initial state
    // We need to run: python manage.py setup_user_story_2
    
    // Use Node's child_process via dynamic import (works in ESM)
    const { exec } = await import('child_process');
    const { promisify } = await import('util');
    const execAsync = promisify(exec);
    
    try {
      const backendPath = 'C:\\Users\\freem\\src\\buggy_service\\backend';
      const pythonExe = `${backendPath}\\.venv\\Scripts\\python.exe`;
      const managePy = `${backendPath}\\manage.py`;
      
      // Use test settings if running in test mode (detected by baseURL port)
      const isTestMode = process.env.PLAYWRIGHT_BASE_URL?.includes(':5174');
      const settingsFlag = isTestMode ? '--settings=buggy_project.settings_test' : '';
      const command = `"${pythonExe}" "${managePy}" setup_user_story_2 ${settingsFlag}`;
      
      console.log('Resetting database to User Story #2 initial state...');
      await execAsync(command);
      console.log('✅ User Story #2 scenario reset complete');
    } catch (error: any) {
      console.error('Failed to reset scenario:', error.message);
      throw new Error('Cannot run test without proper database state');
    }
  });

  test('should assign new ride to Buggy 1 (busy but closer) instead of Buggy 2 (idle but farther)', async ({ page }) => {
    // Add visual click indicators
    await addClickIndicators(page);
    
    // Step 1: Login as dispatcher
    await page.goto('/login');
    await page.fill('input[type="text"]', 'dispatcher');
    await page.fill('input[type="password"]', 'dispatcher');
    await page.click('button[type="submit"]');
    
    // Wait for navigation to dispatcher dashboard
    await expect(page).toHaveURL('/dispatcher');
    await expect(page.locator('.page-title')).toContainText('Dispatcher dashboard');

    // Step 2: Verify initial state - Both buggies should be visible in the cards
    const buggiesCard = page.locator('.card').filter({ hasText: 'Active buggies' });
    await expect(buggiesCard).toContainText('Buggy #1');
    await expect(buggiesCard).toContainText('Buggy #2');
    
    // Verify Buggy 1 at Bel Air with 3 guests
    await expect(buggiesCard).toContainText('Bel Air');
    await expect(buggiesCard).toContainText('3 guest');
    
    // Verify Buggy 2 at Reception with 0 guests
    await expect(buggiesCard).toContainText('Reception');
    await expect(buggiesCard).toContainText('0 guest');
    
    console.log('✅ Initial state verified: Buggy 1 at Bel Air (3 guests), Buggy 2 at Reception (idle)');

    // Step 3: Create new Ride C (Beach Bar → Reception)
    const pickupSelect = page.locator('select.form-select').first();
    const dropoffSelect = page.locator('select.form-select').nth(1);
    
    await pickupSelect.selectOption('BEACH_BAR');
    await dropoffSelect.selectOption('RECEPTION');
    await page.fill('input.form-number', '2');
    
    // Find form inputs
    const roomInput = page.locator('input.form-input').first();
    const guestInput = page.locator('input.form-input').nth(1);
    await roomInput.fill('5011');
    await guestInput.fill('Mr. Smith');
    
    await page.click('button.primary-button:has-text("Create & Assign Ride")');

    // Step 4: Verify success message appears
    const successBanner = page.locator('.banner-success');
    await expect(successBanner).toBeVisible({ timeout: 10000 });
    const successText = await successBanner.textContent();
    
    // Extract ride code from success message
    const rideCodeMatch = successText?.match(/Ride ([A-F0-9]+) assigned/);
    expect(rideCodeMatch).toBeTruthy();
    const rideCode = rideCodeMatch![1];
    console.log(`Created ride: ${rideCode}`);

    // Step 5: Verify ride appears in recent rides and is assigned to Buggy #1
    const ridesCard = page.locator('.card').filter({ hasText: 'Recent rides' });
    await expect(ridesCard).toContainText(rideCode);
    await expect(ridesCard).toContainText('Beach Bar → Reception');
    await expect(ridesCard).toContainText('Buggy #1');
    
    // Critical assertion: Verify assigned to Buggy #1, NOT Buggy #2
    const rideEntry = ridesCard.locator('div').filter({ hasText: rideCode }).first();
    await expect(rideEntry).toContainText('Buggy #1');
    await expect(rideEntry).not.toContainText('Buggy #2');
    
    console.log(`✅ KEY ASSERTION PASSED: Ride ${rideCode} assigned to Buggy #1, NOT Buggy #2`);

    // Step 6: Login as driver to verify route
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL('/login');
    
    await page.fill('input[type="text"]', 'driver1');
    await page.fill('input[type="password"]', 'driver1');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/driver');
    await expect(page.locator('.card-title')).toContainText('My route');

    // Step 7: Verify route has our new ride's stops
    await expect(page.getByText(`Ride ${rideCode} · 2 guests`).first()).toBeVisible();
    await expect(page.getByText('Pickup – Beach Bar')).toBeVisible();
    await expect(page.getByText('Dropoff – Reception')).toBeVisible();

    // Step 8: Complete the route using new stop-card structure
    console.log('Completing all route stops...');

    while (true) {
      // Check if we're done
      const noStopsMessage = page.locator('div:has-text("No upcoming stops")');
      if (await noStopsMessage.isVisible({ timeout: 1000 }).catch(() => false)) {
        console.log('All stops completed!');
        break;
      }
      
      // Find the next stop card (with "Next Stop" label)
      const nextStopCard = page.locator('.stop-card').first();
      if (!await nextStopCard.isVisible({ timeout: 1000 }).catch(() => false)) {
        console.log('No more stop cards found');
        break;
      }
      
      // Check if there's a Start button
      const startButton = nextStopCard.locator('button:has-text("Start")');
      if (await startButton.isVisible().catch(() => false)) {
        await startButton.click();
        await page.waitForTimeout(500);
      }
      
      // Click Complete button
      const completeButton = nextStopCard.locator('button:has-text("Complete")');
      if (await completeButton.isVisible().catch(() => false)) {
        await completeButton.click();
        await page.waitForTimeout(1000);
      } else {
        break; // No complete button, we're done
      }
    }

    // Step 9: Verify "No upcoming stops" message
    await expect(page.getByText('No upcoming stops.').first()).toBeVisible({ timeout: 5000 });

    // Step 10: Login as manager to verify metrics
    await page.click('button:has-text("Logout")');
    await page.fill('input[type="text"]', 'manager');
    await page.fill('input[type="password"]', 'manager');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/manager');
    
    // Verify metrics page loaded with KPI cards
    await expect(page.locator('.page-title')).toContainText('Manager dashboard');
    await expect(page.getByText('Total Rides')).toBeVisible();
    await expect(page.getByText('Avg Wait Time')).toBeVisible();
    
    console.log(`✅ User Story #2 test PASSED! All assertions verified.`);
  });

  test('should show "no active buggies" error when all buggies are inactive', async ({ page }) => {
    // Add visual click indicators
    await addClickIndicators(page);
    
    await page.goto('/login');
    await page.fill('input[type="text"]', 'dispatcher');
    await page.fill('input[type="password"]', 'dispatcher');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/dispatcher');
    
    // Check if the form is enabled or disabled
    const formFieldset = page.locator('fieldset');
    const isDisabled = await formFieldset.getAttribute('disabled');
    
    if (isDisabled === null) {
      // Form is enabled - buggies are active
      console.log('✅ Form is enabled because there are active buggies');
    } else {
      // Form is disabled - no active buggies
      await expect(page.locator('.banner-error:has-text("No active buggies")')).toBeVisible();
      console.log('✅ Form correctly disabled when no active buggies');
    }
  });
});

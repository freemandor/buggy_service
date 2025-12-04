import { test, expect, Page } from '@playwright/test';

// Helper to add visual click indicators
async function addClickIndicators(page: Page) {
  await page.addInitScript(() => {
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
  const apiBase = 'http://localhost:8000/api';
  const response = await fetch(`${apiBase}/auth/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });
  
  if (!response.ok) {
    throw new Error(`Login failed: ${response.statusText}`);
  }
  
  const data = await response.json();
  return data.access;
}

// Helper to fetch driver route
async function fetchDriverRoute(token: string): Promise<any[]> {
  const apiBase = 'http://localhost:8000/api';
  const response = await fetch(`${apiBase}/driver/my-route/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to fetch route: ${JSON.stringify(error)}`);
  }
  
  return await response.json();
}

// Helper to start a stop via API
async function startStop(token: string, stopId: number): Promise<void> {
  const apiBase = 'http://localhost:8000/api';
  const response = await fetch(`${apiBase}/driver/stops/${stopId}/start/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to start stop: ${JSON.stringify(error)}`);
  }
}

// Helper to complete a stop via API
async function completeStop(token: string, stopId: number): Promise<void> {
  const apiBase = 'http://localhost:8000/api';
  const response = await fetch(`${apiBase}/driver/stops/${stopId}/complete/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to complete stop: ${JSON.stringify(error)}`);
  }
}

test.describe('Dispatcher SSE Real-time Updates', () => {
  test.beforeEach(async ({ page }) => {
    // Reset database
    const { exec } = await import('child_process');
    const { promisify } = await import('util');
    const execAsync = promisify(exec);
    
    try {
      const backendPath = 'C:\\Users\\freem\\src\\buggy_service\\backend';
      const pythonExe = `${backendPath}\\.venv\\Scripts\\python.exe`;
      const managePy = `${backendPath}\\manage.py`;
      const command = `"${pythonExe}" "${managePy}" setup_user_story_2`;
      
      console.log('Resetting database to test state...');
      await execAsync(command);
      console.log('✅ Database reset complete');
    } catch (error: any) {
      console.error('Failed to reset database:', error.message);
      throw new Error('Cannot run test without proper database state');
    }
  });

  test('should auto-update dispatcher page when driver completes stop via API', async ({ page }) => {
    // Capture console logs for debugging
    page.on('console', msg => console.log('Browser:', msg.text()));
    
    // Add visual indicators
    await addClickIndicators(page);
    
    // Step 1: Login as dispatcher
    await page.goto('/login');
    await page.fill('input[type="text"]', 'dispatcher');
    await page.fill('input[type="password"]', 'dispatcher');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/dispatcher');
    await expect(page.getByText('New ride request').first()).toBeVisible();
    
    console.log('✅ Dispatcher logged in and viewing dashboard');
    
    // Step 2: Verify initial state
    await page.waitForTimeout(2000); // Allow data to load
    
    // Get initial buggy location (should be at Bel Air)
    const buggy1Section = page.locator('div').filter({ hasText: 'Buggy #1' }).first();
    await expect(buggy1Section).toContainText('Bel Air', { timeout: 10000 });
    
    console.log('✅ Initial state verified: Buggy #1 at Bel Air');
    
    // Step 3: Get driver auth token
    const driverToken = await getAuthToken('driver1', 'driver1');
    console.log('✅ Got driver auth token');
    
    // Step 4: Complete the dropoff stop via API (simulating driver action)
    console.log('📡 Fetching driver route via API...');
    const driverRoute = await fetchDriverRoute(driverToken);
    console.log(`✅ Driver has ${driverRoute.length} stop(s) in route`);
    
    if (driverRoute.length === 0) {
      throw new Error('Driver has no stops in route');
    }
    
    // Get the first stop (should be dropoff at Beach Lounge)
    const stopId = driverRoute[0].id;
    console.log(`📡 Completing stop ${stopId} via API (as driver)...`);
    
    // Start and complete the stop
    await startStop(driverToken, stopId);
    console.log('✅ Stop started via API');
    
    await completeStop(driverToken, stopId);
    console.log('✅ Stop completed via API');
    
    // Step 5: Wait for the dispatcher page to auto-update (via SSE)
    console.log('⏳ Waiting for SSE event and page update...');
    await page.waitForTimeout(3000); // Give SSE time to deliver event and page to update
    
    // Verify buggy location updated to Beach Lounge
    await expect(buggy1Section).toContainText('Beach Lounge', { timeout: 15000 });
    
    console.log('✅ KEY ASSERTION: Dispatcher page auto-updated via SSE!');
    console.log('✅ Buggy location updated without manual refresh');
  });
});


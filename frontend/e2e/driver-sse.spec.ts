import { test, expect, Page } from '@playwright/test';

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

// Helper to create and assign a ride via API
async function createAndAssignRide(
  token: string,
  pickup: string,
  dropoff: string,
  numGuests: number,
  roomNumber: string,
  guestName: string
): Promise<string> {
  const apiBase = 'http://localhost:8000/api';
  const response = await fetch(`${apiBase}/rides/create-and-assign/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      pickup_poi_code: pickup,
      dropoff_poi_code: dropoff,
      num_guests: numGuests,
      room_number: roomNumber,
      guest_name: guestName,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to create ride: ${JSON.stringify(error)}`);
  }
  
  const data = await response.json();
  return data.ride.public_code;
}

test.describe('Driver SSE Real-time Updates', () => {
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

  test('should auto-update driver page when dispatcher assigns new ride via API', async ({ page }) => {
    // Capture console logs for debugging
    page.on('console', msg => console.log('Browser:', msg.text()));
    
    // Add visual indicators
    await addClickIndicators(page);
    
    // Step 1: Login as driver1
    await page.goto('/login');
    await page.fill('input[type="text"]', 'driver1');
    await page.fill('input[type="password"]', 'driver1');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/driver');
    await expect(page.locator('.card-title')).toContainText('My route');
    
    console.log('✅ Driver logged in and viewing route page');
    
    // Step 2: Verify initial state - should have 1 stop (dropoff at Beach Lounge)
    await expect(page.locator('.stop-card')).toHaveCount(1);
    await expect(page.locator('.stop-card')).toContainText('Beach Lounge');
    
    console.log('✅ Initial route loaded: 1 stop');
    
    // Step 3: Get dispatcher auth token
    const dispatcherToken = await getAuthToken('dispatcher', 'dispatcher');
    console.log('✅ Got dispatcher auth token');
    
    // Step 4: Create and assign new ride via API (simulating dispatcher action)
    console.log('📡 Creating new ride via API...');
    const rideCode = await createAndAssignRide(
      dispatcherToken,
      'BEACH_BAR',
      'RECEPTION',
      2,
      '201',
      'API Test Guest'
    );
    
    console.log(`✅ Created ride ${rideCode} via API`);
    
    // Step 5: Wait for the new ride to appear automatically (via SSE)
    // The page should update without manual refresh
    console.log('⏳ Waiting for SSE event and page update...');
    
    // Give SSE more time to establish connection, receive event, and update page
    await page.waitForTimeout(5000);
    
    // Verify page now shows 3 stops (original dropoff + new pickup + new dropoff)
    await expect(page.locator('.stop-card')).toHaveCount(3, { timeout: 15000 });
    
    // Verify new ride appears
    await expect(page.getByText(`Ride ${rideCode}`).first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Pickup – Beach Bar')).toBeVisible();
    await expect(page.getByText('Dropoff – Reception')).toBeVisible();
    
    console.log('✅ KEY ASSERTION: Driver page auto-updated with new ride via SSE!');
    console.log('✅ New ride stops appear without manual refresh');
  });
});


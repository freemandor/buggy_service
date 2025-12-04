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

test.describe('Manager CRUD Operations', () => {
  test.beforeEach(async ({ page }) => {
    // Reset the database to clean state
    const { exec } = await import('child_process');
    const { promisify } = await import('util');
    const execAsync = promisify(exec);
    
    try {
      const backendPath = 'C:\\Users\\freem\\src\\buggy_service\\backend';
      const pythonExe = `${backendPath}\\.venv\\Scripts\\python.exe`;
      const managePy = `${backendPath}\\manage.py`;
      const command = `"${pythonExe}" "${managePy}" reset_for_tests`;
      
      console.log('Resetting database to clean state...');
      await execAsync(command);
      console.log('✅ Database reset complete');
    } catch (error: any) {
      console.error('Failed to reset database:', error.message);
      throw new Error('Cannot run test without clean database state');
    }
    
    // Add visual click indicators
    await addClickIndicators(page);
    
    // Login as manager
    await page.goto('/login');
    await page.fill('input[type="text"]', 'manager');
    await page.fill('input[type="password"]', 'manager');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/manager');
  });

  test('should create a new buggy and verify it appears in list', async ({ page }) => {
    // Navigate to Buggies tab
    await page.click('button:has-text("Buggies")');
    await page.waitForTimeout(500);
    
    // Click Create New Buggy
    await page.click('button:has-text("Create New Buggy")');
    await page.waitForTimeout(500);
    
    // Fill in form
    const codeInput = page.locator('label:has-text("Code")').locator('..').locator('input');
    const displayNameInput = page.locator('label:has-text("Display Name")').locator('..').locator('input');
    const capacityInput = page.locator('label:has-text("Capacity")').locator('..').locator('input');
    
    await codeInput.fill('TEST_BUGGY_1');
    await displayNameInput.fill('Test Buggy #1');
    await capacityInput.fill('6');
    
    // Submit form
    await page.click('button[type="submit"]:has-text("Create")');
    
    // Verify success message
    await expect(page.locator('.banner-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.banner-success')).toContainText('Buggy created successfully');
    
    // Verify buggy appears in table
    await expect(page.locator('table.table-lite')).toContainText('TEST_BUGGY_1');
    await expect(page.locator('table.table-lite')).toContainText('Test Buggy #1');
  });

  test('should create a new driver and verify it appears', async ({ page }) => {
    // Navigate to Drivers tab
    await page.click('button:has-text("Drivers")');
    await page.waitForTimeout(500);
    
    // Click Create New Driver
    await page.click('button:has-text("Create New Driver")');
    await page.waitForTimeout(500);
    
    // Fill in form
    const usernameInput = page.locator('label:has-text("Username")').locator('..').locator('input');
    const passwordInput = page.locator('label:has-text("Password")').locator('..').locator('input');
    const firstNameInput = page.locator('label:has-text("First Name")').locator('..').locator('input');
    const lastNameInput = page.locator('label:has-text("Last Name")').locator('..').locator('input');
    
    await usernameInput.fill('testdriver1');
    await passwordInput.fill('password123');
    await firstNameInput.fill('Test');
    await lastNameInput.fill('Driver');
    
    // Submit form
    await page.click('button[type="submit"]:has-text("Create")');
    
    // Verify success message
    await expect(page.locator('.banner-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.banner-success')).toContainText('Driver created successfully');
    
    // Verify driver appears in table
    await expect(page.locator('table.table-lite')).toContainText('testdriver1');
    await expect(page.locator('table.table-lite')).toContainText('Test');
    await expect(page.locator('table.table-lite')).toContainText('Driver');
  });

  test('should create a new POI and verify it appears in dispatcher dropdown', async ({ page }) => {
    // Navigate to POIs tab
    await page.click('button:has-text("POIs")');
    await page.waitForTimeout(500);
    
    // Click Create New POI
    await page.click('button:has-text("Create New POI")');
    await page.waitForTimeout(500);
    
    // Fill in form
    const codeInput = page.locator('label:has-text("Code")').locator('..').locator('input');
    const nameInput = page.locator('label:has-text("Name")').locator('..').locator('input');
    
    await codeInput.fill('TEST_POI_1');
    await nameInput.fill('Test Location 1');
    
    // Submit form
    await page.click('button[type="submit"]:has-text("Create")');
    
    // Verify success message
    await expect(page.locator('.banner-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.banner-success')).toContainText('POI created successfully');
    
    // Verify POI appears in table
    await expect(page.locator('table.table-lite').first()).toContainText('TEST_POI_1');
    await expect(page.locator('table.table-lite').first()).toContainText('Test Location 1');
    
    // Logout and login as dispatcher
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL('/login');
    
    await page.fill('input[type="text"]', 'dispatcher');
    await page.fill('input[type="password"]', 'dispatcher');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dispatcher');
    
    // Verify POI appears in pickup dropdown
    const pickupSelect = page.locator('select.form-select').first();
    await expect(pickupSelect).toContainText('Test Location 1');
  });

  test('should create a new POI edge via drill-down and verify it appears on both POIs', async ({ page }) => {
    // First, create two new POIs to connect
    await page.click('button:has-text("POIs")');
    await page.waitForTimeout(500);
    
    // Create first POI
    await page.click('button:has-text("Create New POI")');
    await page.waitForTimeout(500);
    
    let codeInput = page.locator('label:has-text("Code")').locator('..').locator('input');
    let nameInput = page.locator('label:has-text("Name")').locator('..').locator('input');
    
    await codeInput.fill('TEST_EDGE_A');
    await nameInput.fill('Test Edge Point A');
    await page.click('button[type="submit"]:has-text("Create")');
    await expect(page.locator('.banner-success')).toBeVisible({ timeout: 5000 });
    await page.waitForTimeout(500);
    
    // Create second POI
    await page.click('button:has-text("Create New POI")');
    await page.waitForTimeout(500);
    
    codeInput = page.locator('label:has-text("Code")').locator('..').locator('input');
    nameInput = page.locator('label:has-text("Name")').locator('..').locator('input');
    
    await codeInput.fill('TEST_EDGE_B');
    await nameInput.fill('Test Edge Point B');
    await page.click('button[type="submit"]:has-text("Create")');
    await expect(page.locator('.banner-success')).toBeVisible({ timeout: 5000 });
    await page.waitForTimeout(500);
    
    // Click "View Details" on the first POI
    const firstPOIRow = page.locator('tr:has-text("TEST_EDGE_A")');
    await firstPOIRow.locator('button:has-text("View Details")').click();
    
    // Should navigate to POI detail page
    await expect(page).toHaveURL(/\/manager\/pois\/\d+/);
    await expect(page.locator('.page-title')).toContainText('Test Edge Point A');
    
    // Create a connection to Test Edge Point B
    await page.click('button:has-text("Create New Connection")');
    await page.waitForTimeout(500);
    
    const toSelect = page.locator('label:has-text("To POI")').locator('..').locator('select');
    const travelTimeInput = page.locator('label:has-text("Travel Time")').locator('..').locator('input');
    
    await toSelect.selectOption({ label: 'Test Edge Point B' });
    await travelTimeInput.fill('180');
    
    // Submit form
    await page.click('button[type="submit"]:has-text("Create")');
    
    // Verify success message
    await expect(page.locator('.banner-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.banner-success')).toContainText('Connection created successfully');
    
    // Verify edge appears in connections table
    await expect(page.locator('table.table-lite')).toContainText('Test Edge Point B');
    await expect(page.locator('table.table-lite')).toContainText('180s');
    
    // Go back to POIs tab
    await page.click('button:has-text("Back to POIs")');
    await expect(page).toHaveURL('/manager');
    
    // Make sure we're on the POIs tab
    await page.click('button:has-text("POIs")');
    await page.waitForTimeout(500);
    
    // Now check Test Edge Point B - the edge should appear there too!
    const secondPOIRow = page.locator('tr:has-text("TEST_EDGE_B")');
    await secondPOIRow.locator('button:has-text("View Details")').click();
    
    await expect(page).toHaveURL(/\/manager\/pois\/\d+/);
    await expect(page.locator('.page-title')).toContainText('Test Edge Point B');
    
    // The connection to Test Edge Point A should appear here
    await expect(page.locator('table.table-lite')).toContainText('Test Edge Point A');
    await expect(page.locator('table.table-lite')).toContainText('180s');
    
    console.log('✅ KEY ASSERTION: Edge appears in BOTH POI drill-downs!');
  });

  test('should edit existing buggy and verify changes', async ({ page }) => {
    // First, create a buggy to edit
    await page.click('button:has-text("Buggies")');
    await page.waitForTimeout(500);
    
    await page.click('button:has-text("Create New Buggy")');
    await page.waitForTimeout(500);
    
    const codeInput = page.locator('label:has-text("Code")').locator('..').locator('input');
    const displayNameInput = page.locator('label:has-text("Display Name")').locator('..').locator('input');
    const capacityInput = page.locator('label:has-text("Capacity")').locator('..').locator('input');
    
    await codeInput.fill('EDIT_TEST');
    await displayNameInput.fill('Original Name');
    await capacityInput.fill('4');
    await page.click('button[type="submit"]:has-text("Create")');
    
    await expect(page.locator('.banner-success')).toBeVisible({ timeout: 5000 });
    await page.waitForTimeout(500);
    
    // Now find and edit the buggy
    const editButton = page.locator('tr:has-text("EDIT_TEST")').locator('button:has-text("Edit")');
    await editButton.click();
    await page.waitForTimeout(500);
    
    // Modify display name
    const displayNameInputEdit = page.locator('label:has-text("Display Name")').locator('..').locator('input');
    await displayNameInputEdit.clear();
    await displayNameInputEdit.fill('Updated Buggy Name');
    
    // Submit form
    await page.click('button[type="submit"]:has-text("Update")');
    
    // Verify success message
    await expect(page.locator('.banner-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.banner-success')).toContainText('Buggy updated successfully');
    
    // Verify changes appear in table
    await expect(page.locator('table.table-lite')).toContainText('Updated Buggy Name');
  });

  test('should delete buggy and verify it is removed', async ({ page }) => {
    // First, create a test buggy to delete
    await page.click('button:has-text("Buggies")');
    await page.waitForTimeout(500);
    
    await page.click('button:has-text("Create New Buggy")');
    await page.waitForTimeout(500);
    
    const codeInput = page.locator('label:has-text("Code")').locator('..').locator('input');
    const displayNameInput = page.locator('label:has-text("Display Name")').locator('..').locator('input');
    const capacityInput = page.locator('label:has-text("Capacity")').locator('..').locator('input');
    
    await codeInput.fill('DELETE_ME');
    await displayNameInput.fill('Buggy To Delete');
    await capacityInput.fill('4');
    await page.click('button[type="submit"]:has-text("Create")');
    
    await expect(page.locator('.banner-success')).toBeVisible({ timeout: 5000 });
    await page.waitForTimeout(500);
    
    // Now find and delete it
    const deleteRow = page.locator('tr:has-text("DELETE_ME")');
    await expect(deleteRow).toBeVisible();
    
    // Mock the confirm dialog to auto-accept
    page.on('dialog', dialog => dialog.accept());
    
    const deleteButton = deleteRow.locator('button:has-text("Delete")');
    await deleteButton.click();
    
    // Verify success message
    await expect(page.locator('.banner-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.banner-success')).toContainText('Buggy deleted successfully');
    
    // Verify buggy is removed from table
    await expect(page.locator('table.table-lite')).not.toContainText('DELETE_ME');
  });
});


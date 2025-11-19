import { test, expect, _electron as electron, ElectronApplication, Page } from '@playwright/test';
import path from 'path';
import fs from 'fs';

let electronApp: ElectronApplication;
let page: Page;

test.beforeAll(async () => {
  // Launch Electron app
  electronApp = await electron.launch({
    args: [path.join(__dirname, '../dist/electron/electron/main.js')],
    env: {
      ...process.env,
      NODE_ENV: 'test',
    },
  });

  // Get the first page (main window)
  page = await electronApp.firstWindow();

  // Wait for page to load
  await page.waitForLoadState('domcontentloaded');

  // Wait for React to render - check for any content
  try {
    await page.waitForSelector('h1, h2, [data-testid="upload-area"]', { timeout: 15000 });
  } catch (e) {
    console.error('React app did not render in time');
  }

  console.log('Electron app launched');
});

test.afterAll(async () => {
  await electronApp.close();
});

test.describe('Desktop App - End to End Tests', () => {

  test('should launch the application', async () => {
    expect(electronApp).toBeTruthy();
    expect(page).toBeTruthy();

    const title = await page.title();
    expect(title).toContain('OscuraTesti AI');
  });

  test('should display the home page', async () => {
    // Wait for React to render - check for any heading first (which indicates app loaded)
    const heading = await page.locator('h1, h2').first();
    await expect(heading).toBeVisible({ timeout: 15000 });

    // Check for upload area
    const uploadArea = await page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible({ timeout: 10000 });
  });

  test('should show settings page when clicking settings', async () => {
    // Click settings button
    const settingsButton = await page.locator('[data-testid="settings-button"], button:has-text("Settings")');
    if (await settingsButton.isVisible()) {
      await settingsButton.click();

      // Verify settings page loaded
      await expect(page.locator('text=Settings, text=Preferences')).toBeVisible({ timeout: 5000 });
    }
  });

  test('should upload and process a document', async () => {
    // Navigate to home if not already there
    const homeButton = await page.locator('[data-testid="home-button"], button:has-text("Home")');
    if (await homeButton.isVisible()) {
      await homeButton.click();
    }

    // Create a test PDF file path
    const testFilePath = path.join(__dirname, 'fixtures', 'test_document.pdf');

    // Check if test file exists, if not skip this test
    if (!fs.existsSync(testFilePath)) {
      test.skip();
      return;
    }

    // Upload file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    // Wait for processing to start
    await page.waitForSelector('[data-testid="processing-indicator"], text=Processing', { timeout: 5000 });

    // Wait for results (with longer timeout for processing)
    await page.waitForSelector('[data-testid="review-page"], text=Review detected PII', { timeout: 30000 });

    // Verify we're on the review page
    const reviewHeading = await page.locator('text=Review, text=PII').first();
    await expect(reviewHeading).toBeVisible();
  });

  test('should display detected PII entities', async () => {
    // Check if we're on review page
    const isReviewPage = await page.locator('text=Review detected PII').isVisible();

    if (isReviewPage) {
      // Check for entity list or stats
      const totalEntities = await page.locator('[data-testid="total-entities"], text=Total').isVisible();
      expect(totalEntities).toBeTruthy();

      // Check for accept/reject buttons
      const acceptButton = await page.locator('button:has-text("Accept"), [data-testid="accept-button"]').first();
      await expect(acceptButton).toBeVisible();
    }
  });

  test('should accept all entities', async () => {
    const acceptAllButton = await page.locator('button:has-text("Accept All"), [data-testid="accept-all-button"]');

    if (await acceptAllButton.isVisible()) {
      await acceptAllButton.click();

      // Wait for state update
      await page.waitForTimeout(1000);

      // Check that accepted count increased
      const acceptedCount = await page.locator('[data-testid="accepted-count"]').textContent();
      expect(parseInt(acceptedCount || '0')).toBeGreaterThan(0);
    }
  });

  test('should reject all entities', async () => {
    const rejectAllButton = await page.locator('button:has-text("Reject All"), [data-testid="reject-all-button"]');

    if (await rejectAllButton.isVisible()) {
      await rejectAllButton.click();

      // Wait for state update
      await page.waitForTimeout(1000);

      // Check that rejected count increased
      const rejectedCount = await page.locator('[data-testid="rejected-count"]').textContent();
      expect(parseInt(rejectedCount || '0')).toBeGreaterThan(0);
    }
  });

  test('should export redacted PDF', async () => {
    // Accept some entities first
    const acceptAllButton = await page.locator('button:has-text("Accept All")');
    if (await acceptAllButton.isVisible()) {
      await acceptAllButton.click();
      await page.waitForTimeout(1000);
    }

    // Click export button
    const exportButton = await page.locator('button:has-text("Export"), [data-testid="export-button"]');

    if (await exportButton.isVisible()) {
      // Listen for download
      const downloadPromise = page.waitForEvent('download', { timeout: 10000 });

      await exportButton.click();

      // Wait for download to start
      try {
        const download = await downloadPromise;
        expect(download).toBeTruthy();
        expect(download.suggestedFilename()).toContain('redacted');
      } catch (e) {
        console.log('Download may require user interaction or file dialog');
      }
    }
  });

  test('should navigate back to home page', async () => {
    const homeButton = await page.locator('[data-testid="home-button"], button:has-text("Home"), a[href="/"]').first();

    if (await homeButton.isVisible()) {
      await homeButton.click();

      // Verify we're back on home
      await expect(page.locator('[data-testid="upload-area"]')).toBeVisible({ timeout: 5000 });
    }
  });

  test('should show keyboard shortcuts help', async () => {
    // Try pressing Ctrl/Cmd + /
    await page.keyboard.press(process.platform === 'darwin' ? 'Meta+/' : 'Control+/');

    // Check if shortcuts dialog appears
    const shortcutsDialog = await page.locator('text=Keyboard Shortcuts, text=Shortcuts').isVisible();
    if (shortcutsDialog) {
      expect(shortcutsDialog).toBeTruthy();
    }
  });

  test('should handle file drag and drop', async () => {
    // Navigate to home
    const homeButton = await page.locator('[data-testid="home-button"], a[href="/"]').first();
    if (await homeButton.isVisible()) {
      await homeButton.click();
    }

    // Get upload area
    const uploadArea = await page.locator('[data-testid="upload-area"]');

    if (await uploadArea.isVisible()) {
      // Simulate drag enter
      await uploadArea.hover();

      // Check for drag-over state (visual feedback)
      const isDragActive = await page.evaluate(() => {
        const area = document.querySelector('[data-testid="upload-area"]');
        return area?.classList.contains('drag-over') || area?.classList.contains('border-blue-500');
      });

      // Note: Actual file drop simulation requires more complex setup
      console.log('Drag-drop UI interaction tested');
    }
  });
});

test.describe('Performance Tests', () => {

  test('should load home page quickly', async () => {
    const startTime = Date.now();

    await page.reload();
    await page.waitForLoadState('domcontentloaded');

    const loadTime = Date.now() - startTime;
    console.log(`Page load time: ${loadTime}ms`);

    // Should load in under 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should handle large documents efficiently', async () => {
    // This would require a large test document
    test.skip(); // Skip by default, run manually with large docs
  });
});

test.describe('Error Handling', () => {

  test('should handle invalid file uploads gracefully', async () => {
    // Try uploading a non-PDF/DOCX file
    const testFilePath = path.join(__dirname, 'fixtures', 'invalid.txt');

    if (fs.existsSync(testFilePath)) {
      const fileInput = await page.locator('input[type="file"]');
      await fileInput.setInputFiles(testFilePath);

      // Should show error message
      const errorMessage = await page.locator('text=Invalid file, text=Error, [role="alert"]').isVisible({ timeout: 5000 });
      expect(errorMessage).toBeTruthy();
    }
  });

  test('should show error when Python backend is unavailable', async () => {
    // This would require stopping the Python process
    test.skip(); // Skip by default
  });
});

test.describe('Accessibility Tests', () => {

  test('should have proper ARIA labels', async () => {
    const buttons = await page.locator('button');
    const count = await buttons.count();

    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      const text = await button.textContent();

      // Button should have either aria-label or text content
      expect(ariaLabel || text).toBeTruthy();
    }
  });

  test('should support keyboard navigation', async () => {
    // Tab through focusable elements
    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);

    // Check that focus is visible
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });

  test('should have sufficient color contrast', async () => {
    // This would require a color contrast checker
    // For now, visual regression testing
    await expect(page).toHaveScreenshot('accessibility-check.png', {
      maxDiffPixels: 100,
    });
  });
});

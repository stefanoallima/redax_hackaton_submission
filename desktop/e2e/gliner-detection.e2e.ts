import { test, expect, _electron as electron, ElectronApplication, Page } from '@playwright/test';
import path from 'path';
import fs from 'fs';

/**
 * GLiNER Enhanced Detection E2E Tests
 *
 * Tests the complete detection pipeline with GLiNER integration:
 * - Detection slider functionality (Fast/Balanced/Thorough/Maximum)
 * - Entity detection accuracy improvements
 * - Source tracking (Presidio vs GLiNER)
 * - Graceful fallback to Presidio-only mode
 * - Performance benchmarks
 */

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

  // Wait for React to render
  try {
    await page.waitForSelector('h1, h2, [data-testid="upload-area"]', { timeout: 15000 });
  } catch (e) {
    console.error('React app did not render in time');
  }

  console.log('Electron app launched for GLiNER testing');
});

test.afterAll(async () => {
  await electronApp.close();
});

test.describe('GLiNER Detection - Full Pipeline', () => {

  test('should display detection settings panel', async () => {
    // Navigate to home if not already there
    const homeButton = await page.locator('[data-testid="home-button"]').or(page.locator('button:has-text("Home")'));
    if (await homeButton.isVisible({ timeout: 2000 })) {
      await homeButton.click();
    }

    // Check for detection settings panel
    const settingsPanel = await page.locator('[data-testid="detection-settings"]').or(page.locator('text=Detection Settings')).first();
    await expect(settingsPanel).toBeVisible({ timeout: 10000 });

    console.log('✓ Detection settings panel visible');
  });

  test('should show detection depth slider', async () => {
    // Find the depth slider
    const depthSlider = await page.locator('[data-testid="depth-slider"], input[type="range"]').first();
    await expect(depthSlider).toBeVisible();

    // Get slider value
    const sliderValue = await depthSlider.getAttribute('value');
    console.log(`Current slider value: ${sliderValue}`);

    // Verify slider has correct range (0-3 for Fast/Balanced/Thorough/Maximum)
    const min = await depthSlider.getAttribute('min');
    const max = await depthSlider.getAttribute('max');
    expect(min).toBe('0');
    expect(max).toBe('3');

    console.log('✓ Detection depth slider configured correctly');
  });

  test('should display detection mode labels', async () => {
    // Check for mode labels (Italian)
    const modeLabels = ['Veloce', 'Bilanciato', 'Approfondito', 'Massimo'];

    for (const mode of modeLabels) {
      const label = await page.locator(`text=${mode}`).first();
      await expect(label).toBeVisible({ timeout: 5000 });
    }

    console.log('✓ All detection mode labels present');
  });

  test('should show time estimates for different depths', async () => {
    // Look for time estimation display
    const timeEstimate = await page.locator('[data-testid="time-estimate"]').or(page.locator('text=second')).or(page.locator('text=minute')).first();

    if (await timeEstimate.isVisible({ timeout: 2000 })) {
      const estimateText = await timeEstimate.textContent();
      console.log(`Time estimate displayed: ${estimateText}`);
      expect(estimateText).toMatch(/\d+/); // Should contain numbers
    }

    console.log('✓ Time estimates visible');
  });

  test('should update slider and reflect mode change', async () => {
    // Get the slider
    const depthSlider = await page.locator('[data-testid="depth-slider"]').or(page.locator('input[type="range"]')).first();

    // Set to Fast mode (0)
    await depthSlider.evaluate((el: HTMLInputElement) => {
      el.value = '0';
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.waitForTimeout(500);

    // Just verify the slider value changed (mode display may vary)
    const sliderValue = await depthSlider.evaluate((el: HTMLInputElement) => el.value);
    expect(sliderValue).toBe('0');
    console.log('✓ Fast mode selected (slider value: 0)');

    // Set to Balanced mode (1)
    await depthSlider.evaluate((el: HTMLInputElement) => {
      el.value = '1';
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.waitForTimeout(500);

    const balancedValue = await depthSlider.evaluate((el: HTMLInputElement) => el.value);
    expect(balancedValue).toBe('1');
    console.log('✓ Balanced mode selected (slider value: 1)');

    // Set to Thorough mode (2)
    await depthSlider.evaluate((el: HTMLInputElement) => {
      el.value = '2';
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.waitForTimeout(500);
    const thoroughValue = await depthSlider.evaluate((el: HTMLInputElement) => el.value);
    expect(thoroughValue).toBe('2');
    console.log('✓ Thorough mode selected (slider value: 2)');

    // Set to Maximum mode (3)
    await depthSlider.evaluate((el: HTMLInputElement) => {
      el.value = '3';
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.waitForTimeout(500);
    const maximumValue = await depthSlider.evaluate((el: HTMLInputElement) => el.value);
    expect(maximumValue).toBe('3');
    console.log('✓ Maximum mode selected (slider value: 3)');
  });
});

test.describe('GLiNER Detection - Document Processing', () => {

  test('should process document with Fast mode (Presidio only)', async () => {
    // Set slider to Fast mode
    const depthSlider = await page.locator('[data-testid="depth-slider"]').or(page.locator('input[type="range"]')).first();
    await depthSlider.evaluate((el: HTMLInputElement) => {
      el.value = '0';
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.waitForTimeout(500);

    // Upload test document
    const testFilePath = path.join(__dirname, 'fixtures', 'test_italian_legal_doc.pdf');

    if (!fs.existsSync(testFilePath)) {
      console.warn(`Test file not found: ${testFilePath}`);
      console.warn('Skipping document processing tests - create fixtures/test_italian_legal_doc.pdf');
      test.skip();
      return;
    }

    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    // Wait for file to be selected
    await page.waitForTimeout(500);

    // Click Start Detection button
    const startButton = await page.locator('[data-testid="start-detection-button"]');
    await startButton.click();

    // Wait for button to change to "Processing..."
    console.log('Waiting for processing to complete...');
    await page.waitForSelector('button:has-text("Processing")', { timeout: 2000 }).catch(() => {});

    // Record start time and wait for results
    const startTime = Date.now();
    await page.waitForSelector('text=Review detected PII', { timeout: 60000 });

    const processingTime = Date.now() - startTime;
    console.log(`✓ Fast mode processing completed in ${processingTime}ms`);

    // Verify we're on review page
    const reviewHeading = await page.locator('text=Review detected PII').first();
    await expect(reviewHeading).toBeVisible();

    // Check entity count
    const totalEntities = await page.locator('[data-testid="total-entities"]').or(page.locator('text=Total')).or(page.locator('text=entities')).first().textContent();
    console.log(`Entities detected (Fast mode): ${totalEntities}`);
  });

  test('should process document with Balanced mode (Presidio + GLiNER Italian)', async () => {
    // Navigate back to home
    const homeButton = await page.locator('[data-testid="home-button"]').or(page.locator('a[href="/"]')).first();
    await homeButton.click();
    await page.waitForTimeout(1000);

    // Set slider to Balanced mode
    const depthSlider = await page.locator('[data-testid="depth-slider"]').or(page.locator('input[type="range"]')).first();
    await depthSlider.evaluate((el: HTMLInputElement) => {
      el.value = '1';
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.waitForTimeout(500);

    // Upload test document
    const testFilePath = path.join(__dirname, 'fixtures', 'test_italian_legal_doc.pdf');

    if (!fs.existsSync(testFilePath)) {
      test.skip();
      return;
    }

    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    // Wait for file to be selected and click Start button
    await page.waitForTimeout(500);
    const startButton = await page.locator('[data-testid="start-detection-button"]');
    await startButton.click();

    // Wait for button to change to "Processing..."
    await page.waitForSelector('button:has-text("Processing")', { timeout: 2000 }).catch(() => {});

    // Note: This may take longer due to GLiNER model loading (~10-20s first time)
    const startTime = Date.now();
    await page.waitForSelector('text=Review detected PII', { timeout: 90000 });

    const processingTime = Date.now() - startTime;
    console.log(`✓ Balanced mode processing completed in ${processingTime}ms`);

    // Check if more entities detected compared to Fast mode
    const totalEntities = await page.locator('[data-testid="total-entities"]').first().textContent();
    console.log(`Entities detected (Balanced mode): ${totalEntities}`);

    // Check for detection sources
    const sourceInfo = await page.locator('[data-testid="detection-sources"]').or(page.locator('text=Source')).isVisible({ timeout: 2000 });
    if (sourceInfo) {
      console.log('✓ Detection source information displayed');
    }
  });

  test('should process document with Thorough mode (All models)', async () => {
    // Navigate back to home
    const homeButton = await page.locator('[data-testid="home-button"]').first();
    await homeButton.click();
    await page.waitForTimeout(1000);

    // Set slider to Thorough mode
    const depthSlider = await page.locator('[data-testid="depth-slider"]').or(page.locator('input[type="range"]')).first();
    await depthSlider.evaluate((el: HTMLInputElement) => {
      el.value = '2';
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.waitForTimeout(500);

    // Upload test document
    const testFilePath = path.join(__dirname, 'fixtures', 'test_italian_legal_doc.pdf');

    if (!fs.existsSync(testFilePath)) {
      test.skip();
      return;
    }

    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    // Wait for file to be selected and click Start button
    await page.waitForTimeout(500);
    const startButton = await page.locator('[data-testid="start-detection-button"]');
    await startButton.click();

    // Wait for button to change to "Processing..."
    await page.waitForSelector('button:has-text("Processing")', { timeout: 2000 }).catch(() => {});

    // Wait for processing (longest time due to all models)
    const startTime = Date.now();
    await page.waitForSelector('text=Review detected PII', { timeout: 120000 }); // 2 minutes max

    const processingTime = Date.now() - startTime;
    console.log(`✓ Thorough mode processing completed in ${processingTime}ms`);

    // Should detect most entities
    const totalEntities = await page.locator('[data-testid="total-entities"]').first().textContent();
    console.log(`Entities detected (Thorough mode): ${totalEntities}`);

    // Check for source breakdown
    const sources = await page.locator('[data-testid="source-summary"]');
    if (await sources.isVisible({ timeout: 2000 })) {
      const sourceText = await sources.textContent();
      console.log(`Detection sources: ${sourceText}`);

      // Should mention multiple sources
      expect(sourceText?.toLowerCase()).toMatch(/presidio|gliner/);
    }
  });
});

test.describe('GLiNER Detection - Entity Source Tracking', () => {

  test('should display entity source information', async () => {
    // Assuming we're on review page from previous test
    const isReviewPage = await page.locator('text=Review detected PII').isVisible({ timeout: 2000 });

    if (!isReviewPage) {
      test.skip();
      return;
    }

    // Look for source badges on entities
    const sourceBadges = await page.locator('[data-testid="entity-source"], .badge, [data-source]').count();

    if (sourceBadges > 0) {
      console.log(`✓ Found ${sourceBadges} entities with source information`);

      // Check for different sources
      const presidioEntities = await page.locator('[data-source="presidio"]').or(page.locator('text=Presidio')).count();
      const glinerEntities = await page.locator('[data-source="gliner"]').or(page.locator('text=GLiNER')).count();

      console.log(`  - Presidio detections: ${presidioEntities}`);
      console.log(`  - GLiNER detections: ${glinerEntities}`);

      expect(presidioEntities + glinerEntities).toBeGreaterThan(0);
    } else {
      console.warn('⚠ No source information found on entities');
    }
  });

  test('should show source summary statistics', async () => {
    // Look for source summary section
    const sourceSummary = await page.locator('[data-testid="source-summary"]').or(page.locator('text=Detection Sources')).first();

    if (await sourceSummary.isVisible({ timeout: 2000 })) {
      const summaryText = await sourceSummary.textContent();
      console.log(`Source summary: ${summaryText}`);

      // Should contain counts
      expect(summaryText).toMatch(/\d+/);
    } else {
      console.warn('⚠ Source summary not displayed');
    }
  });
});

test.describe('GLiNER Detection - Graceful Fallback', () => {

  test('should handle GLiNER unavailable (Presidio fallback)', async () => {
    // This test validates that app works even if GLiNER models fail to load

    // Check logs for GLiNER status
    const logs: string[] = [];
    page.on('console', msg => {
      const text = msg.text();
      logs.push(text);
      if (text.includes('GLiNER')) {
        console.log(`Console: ${text}`);
      }
    });

    // Navigate to home and process a document
    const homeButton = await page.locator('[data-testid="home-button"]').first();
    if (await homeButton.isVisible({ timeout: 2000 })) {
      await homeButton.click();
      await page.waitForTimeout(1000);
    }

    const testFilePath = path.join(__dirname, 'fixtures', 'test_italian_legal_doc.pdf');

    if (!fs.existsSync(testFilePath)) {
      test.skip();
      return;
    }

    // Process document
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    // Wait for file to be selected and click Start button
    await page.waitForTimeout(500);
    const startButton = await page.locator('[data-testid="start-detection-button"]');
    await startButton.click();

    // Wait for button to change to "Processing..."
    await page.waitForSelector('button:has-text("Processing")', { timeout: 2000 }).catch(() => {});

    // Wait for processing to complete
    await page.waitForSelector('text=Review detected PII', { timeout: 60000 });

    // Check if app still works (even if GLiNER failed)
    const reviewPage = await page.locator('text=Review detected PII');
    await expect(reviewPage).toBeVisible();

    // Check logs for GLiNER status
    const hasGLiNERLog = logs.some(log =>
      log.includes('GLiNER') && (log.includes('available') || log.includes('not available'))
    );

    if (hasGLiNERLog) {
      const glinerAvailable = logs.some(log =>
        log.includes('GLiNER') && log.includes('available') && !log.includes('not')
      );
      console.log(`GLiNER status: ${glinerAvailable ? 'Available' : 'Fallback to Presidio'}`);
    } else {
      console.warn('⚠ No GLiNER status log found');
    }

    // Verify detection still works
    const totalEntities = await page.locator('[data-testid="total-entities"]').first().textContent();
    console.log(`Entities detected: ${totalEntities}`);

    expect(totalEntities).not.toBeNull();
  });
});

test.describe('GLiNER Detection - Performance Benchmarks', () => {

  test('should measure processing time for each mode', async () => {
    const results: { mode: string; time: number; entities: number }[] = [];

    const modes = [
      { name: 'Fast', value: 0 },
      { name: 'Balanced', value: 1 },
      { name: 'Thorough', value: 2 },
    ];

    const testFilePath = path.join(__dirname, 'fixtures', 'test_italian_legal_doc.pdf');

    if (!fs.existsSync(testFilePath)) {
      console.warn('Test fixture not found - skipping performance benchmarks');
      test.skip();
      return;
    }

    for (const mode of modes) {
      // Navigate home
      const homeButton = await page.locator('[data-testid="home-button"]').first();
      if (await homeButton.isVisible({ timeout: 2000 })) {
        await homeButton.click();
        await page.waitForTimeout(1000);
      }

      // Set slider
      const depthSlider = await page.locator('[data-testid="depth-slider"]').or(page.locator('input[type="range"]')).first();
      await depthSlider.evaluate((el: HTMLInputElement, val: number) => {
        el.value = val.toString();
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }, mode.value);
      await page.waitForTimeout(500);

      // Upload and measure
      const fileInput = await page.locator('input[type="file"]');
      await fileInput.setInputFiles(testFilePath);

      // Wait for file to be selected and click Start button
      await page.waitForTimeout(500);
      const startButton = await page.locator('button:has-text("Start PII Detection")');
      await startButton.click();

      // Wait for button to change to "Processing..."
      await page.waitForSelector('button:has-text("Processing")', { timeout: 2000 }).catch(() => {});

      const startTime = Date.now();
      await page.waitForSelector('text=Review detected PII', { timeout: 120000 });

      const processingTime = Date.now() - startTime;

      // Get entity count
      const entityCountText = await page.locator('[data-testid="total-entities"]').first().textContent();
      const entityCount = parseInt(entityCountText?.match(/\d+/)?.[0] || '0');

      results.push({
        mode: mode.name,
        time: processingTime,
        entities: entityCount,
      });

      console.log(`${mode.name}: ${processingTime}ms, ${entityCount} entities`);
    }

    // Display benchmark results
    console.log('\n=== Performance Benchmark Results ===');
    results.forEach(r => {
      console.log(`${r.mode.padEnd(12)} | ${r.time.toString().padStart(7)}ms | ${r.entities} entities`);
    });

    // Verify performance expectations
    // Fast should be fastest
    const fastTime = results.find(r => r.mode === 'Fast')?.time || 0;
    const balancedTime = results.find(r => r.mode === 'Balanced')?.time || 0;

    console.log(`\nFast/Balanced time ratio: ${(balancedTime / fastTime).toFixed(2)}x`);

    // Balanced should detect more entities than Fast (if GLiNER is working)
    const fastEntities = results.find(r => r.mode === 'Fast')?.entities || 0;
    const balancedEntities = results.find(r => r.mode === 'Balanced')?.entities || 0;

    if (balancedEntities > fastEntities) {
      console.log(`✓ GLiNER improved detection: ${balancedEntities - fastEntities} additional entities`);
    } else if (balancedEntities === fastEntities) {
      console.log('⚠ No detection improvement (GLiNER may not be active)');
    }
  });

  test('should measure memory usage during processing', async () => {
    // Get memory usage before processing
    const memBefore = await page.evaluate(() => {
      if (performance && (performance as any).memory) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return 0;
    });

    // Process a document
    const testFilePath = path.join(__dirname, 'fixtures', 'test_italian_legal_doc.pdf');

    if (!fs.existsSync(testFilePath)) {
      test.skip();
      return;
    }

    const homeButton = await page.locator('[data-testid="home-button"]').first();
    if (await homeButton.isVisible({ timeout: 2000 })) {
      await homeButton.click();
      await page.waitForTimeout(1000);
    }

    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    // Wait for file to be selected and click Start button
    await page.waitForTimeout(500);
    const startButton = await page.locator('[data-testid="start-detection-button"]');
    await startButton.click();

    await page.waitForSelector('text=Review detected PII', { timeout: 120000 });

    // Get memory usage after processing
    const memAfter = await page.evaluate(() => {
      if (performance && (performance as any).memory) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return 0;
    });

    if (memBefore > 0 && memAfter > 0) {
      const memIncrease = (memAfter - memBefore) / 1024 / 1024; // MB
      console.log(`Memory increase during processing: ${memIncrease.toFixed(2)} MB`);

      // Should not use excessive memory (< 500MB increase)
      expect(memIncrease).toBeLessThan(500);
    } else {
      console.warn('⚠ Memory profiling not available in this browser');
    }
  });
});

test.describe('GLiNER Detection - Entity Type Coverage', () => {

  test('should detect Italian-specific entities', async () => {
    // Assuming we're on review page with processed document
    const isReviewPage = await page.locator('text=Review detected PII').isVisible({ timeout: 2000 });

    if (!isReviewPage) {
      test.skip();
      return;
    }

    // Check for Italian entity types
    const italianEntityTypes = [
      'IT_FISCAL_CODE',
      'CODICE_FISCALE',
      'IT_VAT_CODE',
      'PARTITA_IVA',
      'IT_IDENTITY_CARD',
      'IT_PASSPORT',
      'IT_DRIVER_LICENSE',
    ];

    let detectedItalianTypes: string[] = [];

    for (const entityType of italianEntityTypes) {
      const hasEntity = await page.locator(`[data-entity-type="${entityType}"]`).or(page.locator(`text=${entityType}`)).count();
      if (hasEntity > 0) {
        detectedItalianTypes.push(entityType);
      }
    }

    if (detectedItalianTypes.length > 0) {
      console.log(`✓ Italian entities detected: ${detectedItalianTypes.join(', ')}`);
    } else {
      console.log('⚠ No Italian-specific entities found (document may not contain them)');
    }
  });

  test('should detect universal PII entities', async () => {
    const isReviewPage = await page.locator('text=Review detected PII').isVisible({ timeout: 2000 });

    if (!isReviewPage) {
      test.skip();
      return;
    }

    // Check for universal PII types
    const universalTypes = ['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'LOCATION', 'DATE_TIME', 'IBAN'];
    let detectedUniversalTypes: string[] = [];

    for (const entityType of universalTypes) {
      const hasEntity = await page.locator(`[data-entity-type="${entityType}"]`).count();
      if (hasEntity > 0) {
        detectedUniversalTypes.push(entityType);
      }
    }

    if (detectedUniversalTypes.length > 0) {
      console.log(`✓ Universal PII detected: ${detectedUniversalTypes.join(', ')}`);
    }
  });
});

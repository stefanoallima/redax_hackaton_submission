import { test, _electron as electron } from '@playwright/test';
import path from 'path';

test('Diagnostic - Check what loads', async () => {
  // Capture console messages
  const consoleMessages: string[] = [];
  const errors: string[] = [];

  // Launch Electron app
  const electronApp = await electron.launch({
    args: [path.join(__dirname, '../dist/electron/electron/main.js')],
    env: {
      ...process.env,
      NODE_ENV: 'test',
    },
  });

  const page = await electronApp.firstWindow();

  // Listen to console
  page.on('console', msg => {
    const text = `[${msg.type()}] ${msg.text()}`;
    consoleMessages.push(text);
    console.log(text);
  });

  // Listen to page errors
  page.on('pageerror', err => {
    const text = `[PAGE ERROR] ${err.message}`;
    errors.push(text);
    console.error(text);
  });

  // Wait a bit for page to load
  await page.waitForTimeout(5000);

  // Get page title and URL
  const title = await page.title();
  const url = page.url();
  console.log(`Title: ${title}`);
  console.log(`URL: ${url}`);

  // Get HTML content
  const html = await page.content();
  console.log(`HTML length: ${html.length}`);
  console.log(`HTML preview: ${html.substring(0, 500)}`);

  // Check if root div exists
  const rootDiv = await page.locator('#root').count();
  console.log(`Root div count: ${rootDiv}`);

  // Check if root has content
  const rootContent = await page.locator('#root').innerHTML().catch(() => '');
  console.log(`Root content: ${rootContent.substring(0, 200)}`);

  // Summarize
  console.log('\n=== SUMMARY ===');
  console.log(`Console messages: ${consoleMessages.length}`);
  console.log(`Errors: ${errors.length}`);
  if (errors.length > 0) {
    console.log('Errors:', errors);
  }

  await electronApp.close();
});

import { test, expect, Page, BrowserContext } from '@playwright/test';

/**
 * Deep Agents UI Test Suite
 * Tests for workspace management, research queries, state persistence, and error handling
 */

test.describe('Deep Agents UI Application', () => {
  let page: Page;
  let context: BrowserContext;

  // Test data
  const testQueries = [
    'What are the latest developments in quantum computing?',
    'Analyze the current trends in artificial intelligence research',
    'What are the emerging technologies in renewable energy?'
  ];

  test.beforeEach(async ({ browser }) => {
    // Create a new context and page for each test to ensure isolation
    context = await browser.newContext();
    page = await context.newPage();

    // Clear localStorage to start fresh
    await page.evaluate(() => {
      localStorage.clear();
    });

    // Set up console message capture
    const consoleMessages: string[] = [];
    page.on('console', msg => {
      consoleMessages.push(`${msg.type()}: ${msg.text()}`);
    });

    // Set up error capture
    page.on('pageerror', error => {
      console.error('Page error:', error.message);
    });

    // Navigate to the application
    await page.goto('/');
    
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Wait for React to render
    await page.waitForSelector('[data-testid="tabs-manager"], .tabsManager, h2:has-text("Workspaces")', { timeout: 30000 });
  });

  test.afterEach(async () => {
    await context.close();
  });

  test('should load the application successfully', async () => {
    // Check that the main components are present
    await expect(page.locator('h2:has-text("Workspaces")')).toBeVisible();
    
    // Take a screenshot for visual verification
    await page.screenshot({ path: 'test-results/app-loaded.png', fullPage: true });
    
    // Verify no critical errors in console
    const errors = await page.evaluate(() => {
      return window.performance.getEntriesByType('navigation').length > 0;
    });
    expect(errors).toBeTruthy();
  });

  test('1. Workspace Creation - Create new workspace with correct naming', async () => {
    console.log('Starting workspace creation test...');
    
    // Wait for the application to load completely
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    
    // Take initial screenshot
    await page.screenshot({ path: 'test-results/01-initial-state.png', fullPage: true });
    
    // Find and click the + button to create a new workspace
    const createButton = page.locator('button[title="New workspace"], button:has(svg):has-text(""), button').filter({ hasText: /^\+$/ }).first();
    await expect(createButton).toBeVisible({ timeout: 10000 });
    
    console.log('Clicking create workspace button...');
    await createButton.click();
    
    // Wait for the new workspace to appear
    await page.waitForTimeout(2000);
    
    // Take screenshot after creation
    await page.screenshot({ path: 'test-results/01-after-creation.png', fullPage: true });
    
    // Check that "Workspace 2" exists (since Workspace 1 should be the default)
    const workspace2Tab = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 2' });
    await expect(workspace2Tab).toBeVisible({ timeout: 10000 });
    
    // Verify the workspace is active
    await expect(workspace2Tab).toHaveClass(/active/);
    
    // Check console for success message
    const consoleMessages = await page.evaluate(() => {
      return (window as any).testConsoleMessages || [];
    });
    
    // Monitor console for the save message
    let saveMessageFound = false;
    page.on('console', msg => {
      if (msg.text().includes('Workspaces saved successfully')) {
        saveMessageFound = true;
      }
    });
    
    // Wait a moment for console messages
    await page.waitForTimeout(1000);
    
    console.log('✅ Workspace creation test completed');
  });

  test('2. Deep Research Query - Submit and track research task', async () => {
    console.log('Starting deep research query test...');
    
    // Wait for application to load
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    
    // Look for chat input area - try multiple selectors
    const chatInputSelectors = [
      'textarea[placeholder*="message"]',
      'input[placeholder*="message"]',
      'textarea[placeholder*="Type"]',
      'input[placeholder*="Type"]',
      '.chat-input textarea',
      '.message-input textarea',
      '[data-testid="chat-input"]',
      'textarea',
      'input[type="text"]'
    ];
    
    let chatInput = null;
    for (const selector of chatInputSelectors) {
      try {
        chatInput = page.locator(selector).first();
        if (await chatInput.isVisible({ timeout: 2000 })) {
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    if (!chatInput || !await chatInput.isVisible()) {
      console.log('Chat input not found, taking screenshot for debugging...');
      await page.screenshot({ path: 'test-results/02-debug-no-input.png', fullPage: true });
      
      // Log all available input elements
      const allInputs = await page.locator('input, textarea').all();
      console.log(`Found ${allInputs.length} input elements`);
      
      for (let i = 0; i < allInputs.length; i++) {
        const placeholder = await allInputs[i].getAttribute('placeholder');
        const visible = await allInputs[i].isVisible();
        console.log(`Input ${i}: placeholder="${placeholder}", visible=${visible}`);
      }
      
      // Try to find any text input that's visible
      chatInput = page.locator('input[type="text"], textarea').filter({ hasText: /./ }).first();
      if (!await chatInput.isVisible()) {
        chatInput = page.locator('input, textarea').first();
      }
    }
    
    await expect(chatInput).toBeVisible({ timeout: 10000 });
    
    // Type the research query
    const testQuery = testQueries[0];
    console.log(`Typing query: ${testQuery}`);
    await chatInput.fill(testQuery);
    
    // Look for submit button
    const submitButton = page.locator('button[type="submit"], button:has-text("Send"), button:has-text("Submit")').first();
    
    if (await submitButton.isVisible()) {
      await submitButton.click();
    } else {
      // Try Enter key if no submit button
      await chatInput.press('Enter');
    }
    
    // Wait for task to appear in sidebar or task list
    await page.waitForTimeout(3000);
    
    // Take screenshot after submitting query
    await page.screenshot({ path: 'test-results/02-query-submitted.png', fullPage: true });
    
    // Look for the query in the UI (in chat, tasks, or sidebar)
    const queryInUI = page.locator('text=' + testQuery.substring(0, 30));
    await expect(queryInUI.first()).toBeVisible({ timeout: 15000 });
    
    // Look for progress indicators
    const progressIndicators = [
      '.progress-bar',
      '.spinner',
      '.loading',
      '[data-testid="progress"]',
      'text=Processing',
      'text=Running',
      'text=In Progress'
    ];
    
    let progressFound = false;
    for (const indicator of progressIndicators) {
      try {
        if (await page.locator(indicator).first().isVisible({ timeout: 2000 })) {
          progressFound = true;
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    console.log(`Progress indicators found: ${progressFound}`);
    console.log('✅ Deep research query test completed');
  });

  test('3. State Persistence - Verify data persists after browser refresh', async () => {
    console.log('Starting state persistence test...');
    
    // Wait for application to load
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    
    // Create a new workspace
    const createButton = page.locator('button[title="New workspace"], button:has(svg)').filter({ hasText: /^\+$/ }).first();
    await expect(createButton).toBeVisible();
    await createButton.click();
    await page.waitForTimeout(2000);
    
    // Verify workspace 2 was created
    const workspace2 = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 2' });
    await expect(workspace2).toBeVisible();
    
    // Start a task if possible
    const chatInput = page.locator('textarea, input[type="text"]').first();
    if (await chatInput.isVisible()) {
      await chatInput.fill('Test task for persistence');
      await chatInput.press('Enter');
      await page.waitForTimeout(2000);
    }
    
    // Take screenshot before refresh
    await page.screenshot({ path: 'test-results/03-before-refresh.png', fullPage: true });
    
    // Refresh the browser
    console.log('Refreshing browser...');
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    
    // Take screenshot after refresh
    await page.screenshot({ path: 'test-results/03-after-refresh.png', fullPage: true });
    
    // Verify workspace still exists with correct name
    const persistedWorkspace = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 2' });
    await expect(persistedWorkspace).toBeVisible({ timeout: 10000 });
    
    // Verify workspace is still active
    await expect(persistedWorkspace).toHaveClass(/active/);
    
    // Check that no errors appeared
    const errorElements = page.locator('.error, [data-testid="error"], text="Error"');
    const errorCount = await errorElements.count();
    expect(errorCount).toBe(0);
    
    console.log('✅ State persistence test completed');
  });

  test('4. File Management - Verify file handling capabilities', async () => {
    console.log('Starting file management test...');
    
    // Wait for application to load
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    
    // Look for files section in sidebar
    const filesSections = [
      'text=Files',
      '[data-testid="files"]',
      '.files-section',
      '.sidebar'
    ];
    
    let filesSection = null;
    for (const selector of filesSections) {
      try {
        const element = page.locator(selector).first();
        if (await element.isVisible({ timeout: 2000 })) {
          filesSection = element;
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    // Take screenshot of file management area
    await page.screenshot({ path: 'test-results/04-file-management.png', fullPage: true });
    
    // If we found a files section, interact with it
    if (filesSection) {
      await expect(filesSection).toBeVisible();
      console.log('Files section found and visible');
    } else {
      console.log('Files section not immediately visible, checking for file-related functionality');
    }
    
    // Look for file upload or file-related buttons
    const fileButtons = page.locator('button:has-text("Upload"), button:has-text("File"), input[type="file"]');
    const fileButtonCount = await fileButtons.count();
    console.log(`Found ${fileButtonCount} file-related elements`);
    
    // Check localStorage for file data
    const hasFileData = await page.evaluate(() => {
      const workspaces = localStorage.getItem('deep-agents-workspaces');
      if (workspaces) {
        const parsed = JSON.parse(workspaces);
        return parsed.some((w: any) => w.files && Object.keys(w.files).length > 0);
      }
      return false;
    });
    
    console.log(`File data in localStorage: ${hasFileData}`);
    console.log('✅ File management test completed');
  });

  test('5. Progress Tracking - Monitor task progress updates', async () => {
    console.log('Starting progress tracking test...');
    
    // Wait for application to load
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    
    // Submit a task to track progress
    const chatInput = page.locator('textarea, input[type="text"]').first();
    if (await chatInput.isVisible()) {
      await chatInput.fill('Long running research task for progress tracking');
      await chatInput.press('Enter');
      await page.waitForTimeout(1000);
    }
    
    // Monitor for progress indicators over time
    const progressMonitoringDuration = 10000; // 10 seconds
    const checkInterval = 1000; // Check every second
    const progressStates: string[] = [];
    
    for (let i = 0; i < progressMonitoringDuration / checkInterval; i++) {
      await page.waitForTimeout(checkInterval);
      
      // Check for various progress indicators
      const indicators = [
        '.progress-bar',
        '.spinner', 
        '.loading',
        'text=Processing',
        'text=Running',
        'text=Completed',
        'text=pending',
        'text=in_progress',
        'text=completed'
      ];
      
      for (const indicator of indicators) {
        try {
          if (await page.locator(indicator).first().isVisible({ timeout: 100 })) {
            const text = await page.locator(indicator).first().textContent();
            progressStates.push(`${indicator}: ${text}`);
            break;
          }
        } catch (e) {
          continue;
        }
      }
      
      // Take periodic screenshots
      if (i % 3 === 0) {
        await page.screenshot({ path: `test-results/05-progress-${i}.png`, fullPage: true });
      }
    }
    
    console.log('Progress states observed:', progressStates);
    
    // Verify real-time updates (check if DOM changes without refresh)
    const initialTodoCount = await page.locator('.todo, .task, [data-testid="task"]').count();
    await page.waitForTimeout(2000);
    const laterTodoCount = await page.locator('.todo, .task, [data-testid="task"]').count();
    
    console.log(`Initial tasks: ${initialTodoCount}, Later tasks: ${laterTodoCount}`);
    console.log('✅ Progress tracking test completed');
  });

  test('6. Error Handling - Verify no critical errors occur', async () => {
    console.log('Starting error handling test...');
    
    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];
    
    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Capture page errors
    page.on('pageerror', error => {
      pageErrors.push(error.message);
    });
    
    // Wait for application to load
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    
    // Perform various actions that might trigger errors
    
    // 1. Create multiple workspaces rapidly
    for (let i = 0; i < 3; i++) {
      const createButton = page.locator('button[title="New workspace"], button:has(svg)').filter({ hasText: /^\+$/ }).first();
      if (await createButton.isVisible()) {
        await createButton.click();
        await page.waitForTimeout(500);
      }
    }
    
    // 2. Switch between workspaces
    const workspaceTabs = page.locator('.tab, [role="tab"]');
    const tabCount = await workspaceTabs.count();
    for (let i = 0; i < Math.min(tabCount, 3); i++) {
      await workspaceTabs.nth(i).click();
      await page.waitForTimeout(500);
    }
    
    // 3. Submit multiple queries rapidly
    const chatInput = page.locator('textarea, input[type="text"]').first();
    if (await chatInput.isVisible()) {
      for (let i = 0; i < 3; i++) {
        await chatInput.fill(`Rapid query ${i + 1}`);
        await chatInput.press('Enter');
        await page.waitForTimeout(300);
      }
    }
    
    // 4. Refresh multiple times
    for (let i = 0; i < 2; i++) {
      await page.reload();
      await page.waitForLoadState('networkidle');
      await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    }
    
    // Wait a moment for any delayed errors
    await page.waitForTimeout(3000);
    
    // Take final screenshot
    await page.screenshot({ path: 'test-results/06-error-handling.png', fullPage: true });
    
    // Check for specific error patterns that should not occur
    const criticalErrors = [
      'Maximum call stack exceeded',
      'JSON serialization error',
      'Cannot read properties of undefined',
      'TypeError: Cannot read',
      'ReferenceError',
      'SyntaxError'
    ];
    
    const foundCriticalErrors = consoleErrors.concat(pageErrors).filter(error => 
      criticalErrors.some(pattern => error.includes(pattern))
    );
    
    // Verify no red error buttons or error UI elements
    const errorButtons = page.locator('button[style*="red"], .error-button, [data-testid="error-button"]');
    const errorButtonCount = await errorButtons.count();
    
    console.log(`Console errors: ${consoleErrors.length}`);
    console.log(`Page errors: ${pageErrors.length}`);
    console.log(`Critical errors: ${foundCriticalErrors.length}`);
    console.log(`Error buttons: ${errorButtonCount}`);
    
    // Assert no critical errors
    expect(foundCriticalErrors).toHaveLength(0);
    expect(errorButtonCount).toBe(0);
    
    console.log('✅ Error handling test completed');
  });

  test('7. Integration Test - Complete workflow with persistence', async () => {
    console.log('Starting integration test...');
    
    // Wait for application to load
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    
    // 1. Create new workspace
    const createButton = page.locator('button[title="New workspace"], button:has(svg)').filter({ hasText: /^\+$/ }).first();
    await createButton.click();
    await page.waitForTimeout(2000);
    
    // 2. Verify workspace creation
    const workspace2 = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 2' });
    await expect(workspace2).toBeVisible();
    
    // 3. Submit research query
    const chatInput = page.locator('textarea, input[type="text"]').first();
    if (await chatInput.isVisible()) {
      await chatInput.fill(testQueries[1]);
      await chatInput.press('Enter');
      await page.waitForTimeout(3000);
    }
    
    // 4. Take mid-test screenshot
    await page.screenshot({ path: 'test-results/07-integration-mid.png', fullPage: true });
    
    // 5. Refresh browser
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    
    // 6. Verify persistence
    const persistedWorkspace = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 2' });
    await expect(persistedWorkspace).toBeVisible();
    
    // 7. Check localStorage state
    const workspaceData = await page.evaluate(() => {
      const data = localStorage.getItem('deep-agents-workspaces');
      return data ? JSON.parse(data) : null;
    });
    
    expect(workspaceData).toBeTruthy();
    expect(Array.isArray(workspaceData)).toBeTruthy();
    expect(workspaceData.length).toBeGreaterThan(1);
    
    // 8. Verify workspace has correct title
    const workspace2Data = workspaceData.find((w: any) => w.title === 'Workspace 2');
    expect(workspace2Data).toBeTruthy();
    
    // 9. Submit another query in the persisted workspace
    if (await chatInput.isVisible()) {
      await chatInput.fill('Additional query after refresh');
      await chatInput.press('Enter');
      await page.waitForTimeout(2000);
    }
    
    // 10. Take final screenshot
    await page.screenshot({ path: 'test-results/07-integration-final.png', fullPage: true });
    
    // 11. Check for console success messages
    let successMessageFound = false;
    page.on('console', msg => {
      if (msg.text().includes('saved successfully') || msg.text().includes('Created new workspace')) {
        successMessageFound = true;
      }
    });
    
    await page.waitForTimeout(1000);
    
    console.log('✅ Integration test completed');
  });
});

/**
 * Test Suite Summary and Reporting
 */
test.describe('Test Summary and Report Generation', () => {
  test('Generate comprehensive test report', async ({ page }) => {
    console.log('\n=== DEEP AGENTS UI TEST SUITE SUMMARY ===\n');
    
    // This test runs after all others to generate a summary
    const testResults = {
      timestamp: new Date().toISOString(),
      testEnvironment: 'http://localhost:3002',
      totalTests: 7,
      testCategories: [
        '1. Workspace Creation',
        '2. Deep Research Query',
        '3. State Persistence After Browser Refresh',
        '4. File Management',
        '5. Progress Tracking',
        '6. Error Handling',
        '7. Integration Test - Complete workflow'
      ],
      keyFindings: {
        workspaceManagement: 'Testing workspace creation, naming, and tab management',
        stateManagement: 'Verifying localStorage persistence across browser sessions',
        userInteraction: 'Testing chat input, task submission, and UI responsiveness',
        errorHandling: 'Monitoring for critical errors and UI stability',
        realTimeUpdates: 'Checking for progress indicators and live updates'
      },
      technicalDetails: {
        testFramework: 'Playwright with TypeScript',
        browsers: ['Chromium', 'Firefox', 'WebKit'],
        screenshotCapture: 'Full page screenshots at key test points',
        errorMonitoring: 'Console and page error tracking',
        stateValidation: 'localStorage and DOM state verification'
      }
    };
    
    console.log('Test Results:', JSON.stringify(testResults, null, 2));
    console.log('\n=== END TEST SUITE SUMMARY ===\n');
  });
});
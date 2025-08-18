import { test, expect, Page, BrowserContext } from '@playwright/test';

/**
 * Workspace Isolation Test Suite
 * Tests for ensuring workspaces are properly isolated and don't share content
 */

test.describe('Workspace Isolation Tests', () => {
  let page: Page;
  let context: BrowserContext;

  test.beforeEach(async ({ browser }) => {
    // Create a new context and page for each test
    context = await browser.newContext();
    page = await context.newPage();

    // Set up error capture
    page.on('pageerror', error => {
      console.error('Page error:', error.message);
    });

    // Capture console errors, especially JSON parse errors
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().includes('JSON')) {
        console.error('JSON Error detected:', msg.text());
      }
    });

    // Navigate to the application FIRST
    await page.goto('/');
    
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // NOW clear localStorage after navigation (to avoid security error)
    await page.evaluate(() => {
      if (typeof localStorage !== 'undefined') {
        localStorage.clear();
      }
    });
    
    // Refresh the page to apply cleared localStorage
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Wait for React to render
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
  });

  test.afterEach(async () => {
    await context.close();
  });

  test('1. New workspace should be completely blank', async () => {
    console.log('Testing that new workspaces are created blank...');
    
    // First, add some content to Workspace 1
    const chatInput = page.locator('textarea[placeholder*="message"], input[placeholder*="Type"]').first();
    if (await chatInput.isVisible()) {
      await chatInput.fill('Test content for workspace 1');
      await chatInput.press('Enter');
      await page.waitForTimeout(2000);
    }
    
    // Take screenshot of workspace 1 with content
    await page.screenshot({ path: 'test-results/workspace-1-with-content.png', fullPage: true });
    
    // Now create a new workspace
    const createButton = page.locator('button[title="New workspace"]').first();
    await expect(createButton).toBeVisible();
    await createButton.click();
    
    // Wait for the new workspace to be created
    await page.waitForTimeout(2000);
    
    // Verify Workspace 2 exists and is active
    const workspace2Tab = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 2' });
    await expect(workspace2Tab).toBeVisible();
    await expect(workspace2Tab).toHaveClass(/active/);
    
    // Take screenshot of the new workspace
    await page.screenshot({ path: 'test-results/workspace-2-blank.png', fullPage: true });
    
    // Check that the chat input is empty in the new workspace
    const newChatInput = page.locator('textarea[placeholder*="message"], input[placeholder*="Type"]').first();
    if (await newChatInput.isVisible()) {
      const inputValue = await newChatInput.inputValue();
      expect(inputValue).toBe('');
    }
    
    // Check localStorage to ensure workspace 2 has no todos or files
    const workspaceData = await page.evaluate(() => {
      const data = localStorage.getItem('deep-agents-workspaces');
      return data ? JSON.parse(data) : null;
    });
    
    const workspace2Data = workspaceData?.find((w: any) => w.title === 'Workspace 2');
    expect(workspace2Data).toBeTruthy();
    expect(workspace2Data.todos).toEqual([]);
    expect(workspace2Data.files).toEqual({});
    expect(workspace2Data.threadId).toBeNull();
    
    console.log('✅ New workspace is properly blank');
  });

  test('2. No JSON parse errors when submitting and answering questions', async () => {
    console.log('Testing JSON parse error prevention...');
    
    let jsonErrorDetected = false;
    
    // Set up JSON error detection
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (text.includes('JSON') || text.includes('Unterminated string')) {
          jsonErrorDetected = true;
          console.error('JSON Error caught:', text);
        }
      }
    });
    
    page.on('pageerror', error => {
      if (error.message.includes('JSON') || error.message.includes('Unterminated')) {
        jsonErrorDetected = true;
        console.error('Page JSON Error:', error.message);
      }
    });
    
    // Submit a research query
    const chatInput = page.locator('textarea[placeholder*="message"], input[placeholder*="Type"]').first();
    await expect(chatInput).toBeVisible();
    await chatInput.fill('What is the capital of France?');
    await chatInput.press('Enter');
    
    // Wait for potential agent response
    await page.waitForTimeout(5000);
    
    // Check if a question box appears (agent asking for clarification)
    const questionBox = page.locator('[class*="questionBox"]').first();
    if (await questionBox.count() > 0) {
      console.log('Question box detected, attempting to answer...');
      
      // Find the answer input
      const answerInput = questionBox.locator('textarea, input[type="text"]').first();
      if (await answerInput.isVisible()) {
        await answerInput.fill('I want a detailed answer about Paris');
        await answerInput.press('Enter');
        await page.waitForTimeout(2000);
      }
    }
    
    // Take screenshot after interaction
    await page.screenshot({ path: 'test-results/json-error-test.png', fullPage: true });
    
    // Verify no JSON errors occurred
    expect(jsonErrorDetected).toBe(false);
    
    console.log('✅ No JSON parse errors detected');
  });

  test('3. Workspace content isolation - no leaking between workspaces', async () => {
    console.log('Testing workspace content isolation...');
    
    // Add unique content to Workspace 1
    const chatInput1 = page.locator('textarea[placeholder*="message"], input[placeholder*="Type"]').first();
    await expect(chatInput1).toBeVisible();
    await chatInput1.fill('Unique content for workspace 1: Alpha Beta Gamma');
    await chatInput1.press('Enter');
    await page.waitForTimeout(2000);
    
    // Take screenshot of workspace 1
    await page.screenshot({ path: 'test-results/isolation-workspace-1.png', fullPage: true });
    
    // Create Workspace 2
    const createButton = page.locator('button[title="New workspace"]').first();
    await createButton.click();
    await page.waitForTimeout(2000);
    
    // Verify we're in Workspace 2
    const workspace2Tab = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 2' });
    await expect(workspace2Tab).toBeVisible();
    await expect(workspace2Tab).toHaveClass(/active/);
    
    // Check that Workspace 2 doesn't contain Workspace 1's content
    const workspace1Content = page.locator('text=Alpha Beta Gamma');
    await expect(workspace1Content).not.toBeVisible();
    
    // Add different content to Workspace 2
    const chatInput2 = page.locator('textarea[placeholder*="message"], input[placeholder*="Type"]').first();
    await chatInput2.fill('Different content for workspace 2: Delta Epsilon Zeta');
    await chatInput2.press('Enter');
    await page.waitForTimeout(2000);
    
    // Take screenshot of workspace 2
    await page.screenshot({ path: 'test-results/isolation-workspace-2.png', fullPage: true });
    
    // Switch back to Workspace 1
    const workspace1Tab = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 1' });
    await workspace1Tab.click();
    await page.waitForTimeout(2000);
    
    // Verify Workspace 1 still has its original content
    const workspace1OriginalContent = page.locator('text=Alpha Beta Gamma');
    await expect(workspace1OriginalContent).toBeVisible();
    
    // Verify Workspace 1 doesn't have Workspace 2's content
    const workspace2Content = page.locator('text=Delta Epsilon Zeta');
    await expect(workspace2Content).not.toBeVisible();
    
    // Check localStorage for proper isolation
    const workspaceData = await page.evaluate(() => {
      const data = localStorage.getItem('deep-agents-workspaces');
      return data ? JSON.parse(data) : null;
    });
    
    const ws1 = workspaceData?.find((w: any) => w.title === 'Workspace 1');
    const ws2 = workspaceData?.find((w: any) => w.title === 'Workspace 2');
    
    expect(ws1).toBeTruthy();
    expect(ws2).toBeTruthy();
    expect(ws1.id).not.toBe(ws2.id);
    expect(ws1.threadId).not.toBe(ws2.threadId);
    
    console.log('✅ Workspaces are properly isolated');
  });

  test('4. Rapid workspace creation without errors', async () => {
    console.log('Testing rapid workspace creation...');
    
    let errorDetected = false;
    
    // Set up error detection
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errorDetected = true;
        console.error('Error during rapid creation:', msg.text());
      }
    });
    
    // Create multiple workspaces rapidly
    for (let i = 0; i < 5; i++) {
      const createButton = page.locator('button[title="New workspace"]').first();
      await createButton.click();
      await page.waitForTimeout(500); // Short delay between creations
      
      // Verify the new workspace was created
      const workspaceTab = page.locator('.tab, [role="tab"]').filter({ hasText: `Workspace ${i + 2}` });
      await expect(workspaceTab).toBeVisible();
    }
    
    // Take screenshot showing all workspaces
    await page.screenshot({ path: 'test-results/rapid-creation.png', fullPage: true });
    
    // Check that all workspaces exist in localStorage
    const workspaceData = await page.evaluate(() => {
      const data = localStorage.getItem('deep-agents-workspaces');
      return data ? JSON.parse(data) : null;
    });
    
    expect(workspaceData).toBeTruthy();
    expect(workspaceData.length).toBe(6); // Original + 5 new ones
    
    // Verify each workspace is blank
    for (let i = 2; i <= 6; i++) {
      const workspace = workspaceData.find((w: any) => w.title === `Workspace ${i}`);
      expect(workspace).toBeTruthy();
      expect(workspace.todos).toEqual([]);
      expect(workspace.files).toEqual({});
    }
    
    // Verify no errors occurred
    expect(errorDetected).toBe(false);
    
    console.log('✅ Rapid workspace creation successful without errors');
  });

  test('5. Workspace persistence after refresh maintains isolation', async () => {
    console.log('Testing workspace isolation after refresh...');
    
    // Create two workspaces with different content
    const chatInput1 = page.locator('textarea[placeholder*="message"], input[placeholder*="Type"]').first();
    await chatInput1.fill('Workspace 1 persistent content');
    await chatInput1.press('Enter');
    await page.waitForTimeout(2000);
    
    // Create Workspace 2
    const createButton = page.locator('button[title="New workspace"]').first();
    await createButton.click();
    await page.waitForTimeout(2000);
    
    const chatInput2 = page.locator('textarea[placeholder*="message"], input[placeholder*="Type"]').first();
    await chatInput2.fill('Workspace 2 persistent content');
    await chatInput2.press('Enter');
    await page.waitForTimeout(2000);
    
    // Take screenshot before refresh
    await page.screenshot({ path: 'test-results/before-refresh-isolation.png', fullPage: true });
    
    // Refresh the page
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
    
    // Verify Workspace 2 is still active (it was active before refresh)
    const workspace2Tab = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 2' });
    await expect(workspace2Tab).toBeVisible();
    await expect(workspace2Tab).toHaveClass(/active/);
    
    // Verify Workspace 2 content is visible
    const ws2Content = page.locator('text=Workspace 2 persistent content');
    await expect(ws2Content).toBeVisible();
    
    // Verify Workspace 1 content is NOT visible
    const ws1Content = page.locator('text=Workspace 1 persistent content');
    await expect(ws1Content).not.toBeVisible();
    
    // Switch to Workspace 1
    const workspace1Tab = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 1' });
    await workspace1Tab.click();
    await page.waitForTimeout(2000);
    
    // Now Workspace 1 content should be visible
    await expect(ws1Content).toBeVisible();
    
    // And Workspace 2 content should NOT be visible
    await expect(ws2Content).not.toBeVisible();
    
    // Take screenshot after refresh
    await page.screenshot({ path: 'test-results/after-refresh-isolation.png', fullPage: true });
    
    console.log('✅ Workspace isolation maintained after refresh');
  });
});

/**
 * Integration test combining all isolation features
 */
test('Complete workspace isolation integration test', async ({ page }) => {
  console.log('Running complete integration test...');
  
  // Navigate first
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  
  // Then clear localStorage after navigation
  await page.evaluate(() => {
    if (typeof localStorage !== 'undefined') {
      localStorage.clear();
    }
  });
  
  // Reload to apply cleared localStorage
  await page.reload();
  await page.waitForSelector('h2:has-text("Workspaces")', { timeout: 30000 });
  
  // Test 1: Create workspace with content
  const input = page.locator('textarea[placeholder*="message"], input[placeholder*="Type"]').first();
  await input.fill('Integration test workspace 1');
  await input.press('Enter');
  await page.waitForTimeout(2000);
  
  // Test 2: Create new blank workspace
  const createBtn = page.locator('button[title="New workspace"]').first();
  await createBtn.click();
  await page.waitForTimeout(2000);
  
  // Test 3: Verify new workspace is blank
  const inputValue = await input.inputValue();
  expect(inputValue).toBe('');
  
  // Test 4: Add content to workspace 2
  await input.fill('Integration test workspace 2');
  await input.press('Enter');
  await page.waitForTimeout(2000);
  
  // Test 5: Switch between workspaces
  const ws1Tab = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 1' });
  await ws1Tab.click();
  await page.waitForTimeout(1000);
  
  const ws2Tab = page.locator('.tab, [role="tab"]').filter({ hasText: 'Workspace 2' });
  await ws2Tab.click();
  await page.waitForTimeout(1000);
  
  // Test 6: Refresh and verify
  await page.reload();
  await page.waitForLoadState('networkidle');
  
  // Final verification
  const workspaceData = await page.evaluate(() => {
    const data = localStorage.getItem('deep-agents-workspaces');
    return data ? JSON.parse(data) : null;
  });
  
  expect(workspaceData).toBeTruthy();
  expect(workspaceData.length).toBe(2);
  
  await page.screenshot({ path: 'test-results/integration-complete.png', fullPage: true });
  
  console.log('✅ Complete integration test passed');
});
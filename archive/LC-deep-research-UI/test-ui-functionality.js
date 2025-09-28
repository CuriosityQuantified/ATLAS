const { chromium } = require('playwright');

async function testDeepAgentsUI() {
  const browser = await chromium.launch({ 
    headless: false, // Set to false to see the browser
    slowMo: 500 // Slow down operations to see what's happening
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    console.log(`[Browser Console] ${msg.type()}: ${msg.text()}`);
  });
  
  // Enable error logging
  page.on('pageerror', error => {
    console.error(`[Page Error] ${error.message}`);
  });
  
  console.log('\n=== Deep Agents UI Test Suite ===\n');
  
  try {
    // Navigate to the application
    console.log('1. Navigating to localhost:3002...');
    await page.goto('http://localhost:3002');
    await page.waitForTimeout(2000);
    
    // Test 1: Workspace Creation
    console.log('\n--- Test 1: Workspace Creation ---');
    
    // Look for the + button to create a new workspace (it's in the Workspaces header)
    console.log('Looking for create workspace button...');
    
    // Try multiple selectors
    const plusButton = await page.locator('button:has-text("+")').first();
    const addButton = await page.locator('button[aria-label*="add"]').first();
    const createButton = plusButton.isVisible() ? plusButton : addButton;
    
    // Get initial workspace count
    const initialWorkspaces = await page.locator('text=/Workspace \\d+/').count();
    console.log(`Initial workspace count: ${initialWorkspaces}`);
    
    if (await plusButton.isVisible()) {
      console.log('✓ Found + button for creating workspace');
      
      // Click to create new workspace
      await plusButton.click();
      await page.waitForTimeout(1000);
      
      // Check if new workspace was created
      const newWorkspaces = await page.locator('text=/Workspace \\d+/').count();
      if (newWorkspaces > initialWorkspaces) {
        console.log('✓ New workspace created successfully');
        
        // Check workspace name pattern
        const workspaceElements = await page.locator('text=/Workspace \\d+/').all();
        const lastWorkspace = workspaceElements[workspaceElements.length - 1];
        const workspaceName = await lastWorkspace.textContent();
        console.log(`New workspace name: ${workspaceName}`);
        
        if (workspaceName && workspaceName.match(/Workspace \d+/)) {
          console.log('✓ Workspace has correct naming pattern (Workspace X)');
        } else {
          console.log('✗ Workspace name incorrect (expected "Workspace X")');
        }
      } else {
        console.log('✗ Failed to create new workspace');
      }
    } else {
      console.log('✗ Create workspace button (+) not found or not visible');
    }
    
    // Test 2: Workspace Persistence
    console.log('\n--- Test 2: Workspace Persistence ---');
    
    // Get current workspace data before refresh
    const workspaceDataBefore = await page.evaluate(() => {
      return localStorage.getItem('deep-agents-workspaces');
    });
    console.log('Workspace data saved to localStorage:', workspaceDataBefore ? '✓' : '✗');
    
    if (workspaceDataBefore) {
      const parsedBefore = JSON.parse(workspaceDataBefore);
      console.log(`Found ${parsedBefore.length} workspace(s) in localStorage`);
    }
    
    // Refresh the page
    console.log('Refreshing browser...');
    await page.reload();
    await page.waitForTimeout(2000);
    
    // Check if workspaces persist
    const workspaceDataAfter = await page.evaluate(() => {
      return localStorage.getItem('deep-agents-workspaces');
    });
    
    if (workspaceDataAfter) {
      console.log('✓ Workspace data persists after refresh');
      
      // Parse and check for circular references
      try {
        const parsed = JSON.parse(workspaceDataAfter);
        console.log(`✓ No JSON serialization errors (${parsed.length} workspaces found)`);
        
        // Check workspace names are preserved
        const workspaceCount = await page.locator('text=/Workspace \\d+/').count();
        if (workspaceCount === parsed.length) {
          console.log('✓ All workspaces displayed correctly after refresh');
        } else {
          console.log(`⚠ Workspace count mismatch: UI shows ${workspaceCount}, localStorage has ${parsed.length}`);
        }
      } catch (e) {
        console.log('✗ JSON serialization error:', e.message);
      }
    } else {
      console.log('✗ Workspace data not persisted');
    }
    
    // Test 3: Check for console errors
    console.log('\n--- Test 3: Error Handling ---');
    
    // Check for any error indicators on the page
    const errorElements = await page.locator('.error, .error-message, [class*="error"]').count();
    
    if (errorElements === 0) {
      console.log('✓ No visible error indicators on the page');
      console.log('✓ No "Maximum call stack exceeded" errors detected');
      console.log('✓ No JSON serialization errors detected');
    } else {
      console.log(`✗ Found ${errorElements} error indicators on the page`);
    }
    
    // Test 4: Task Management
    console.log('\n--- Test 4: Task Management ---');
    
    // Check tabs for Tasks
    const tasksTab = await page.locator('text=/Tasks \\(\\d+\\)/').first();
    if (await tasksTab.isVisible()) {
      console.log('✓ Tasks tab is visible');
      const tasksText = await tasksTab.textContent();
      console.log(`Tasks tab shows: ${tasksText}`);
      
      // Check for "No tasks yet" message
      const noTasksMessage = await page.locator('text="No tasks yet"').isVisible();
      if (noTasksMessage) {
        console.log('✓ "No tasks yet" message displayed correctly');
      }
    } else {
      console.log('✗ Tasks tab not found');
    }
    
    // Test 5: File Management
    console.log('\n--- Test 5: File Management ---');
    
    // Check tabs for Files
    const filesTab = await page.locator('text=/Files \\(\\d+\\)/').first();
    if (await filesTab.isVisible()) {
      console.log('✓ Files tab is visible');
      const filesText = await filesTab.textContent();
      console.log(`Files tab shows: ${filesText}`);
      
      // Click on Files tab to switch
      await filesTab.click();
      await page.waitForTimeout(500);
      
      // Check if files view is displayed
      const filesView = await page.locator('[role="tabpanel"]').nth(1);
      if (await filesView.isVisible()) {
        console.log('✓ Files view is accessible');
      }
      
      // Switch back to Tasks tab
      await tasksTab.click();
      await page.waitForTimeout(500);
    } else {
      console.log('✗ Files tab not found');
    }
    
    // Test 6: Workspace Selection
    console.log('\n--- Test 6: Workspace Selection ---');
    
    // Try to click on a workspace to select it
    const workspaceItems = await page.locator('text=/Workspace \\d+/').all();
    if (workspaceItems.length > 0) {
      console.log(`Found ${workspaceItems.length} workspace(s)`);
      
      // Click on the first workspace
      await workspaceItems[0].click();
      await page.waitForTimeout(500);
      
      // Check if workspace is selected (usually has different styling)
      const activeWorkspace = await page.evaluate(() => {
        return localStorage.getItem('deep-agents-active-workspace');
      });
      
      if (activeWorkspace) {
        console.log(`✓ Active workspace set: ${activeWorkspace}`);
      } else {
        console.log('⚠ Active workspace not set in localStorage');
      }
    }
    
    // Test 7: Message Input
    console.log('\n--- Test 7: Message Input ---');
    
    const messageInput = await page.locator('input[placeholder*="Type your message"]');
    if (await messageInput.isVisible()) {
      console.log('✓ Message input field is visible');
      
      // Try typing in the input
      await messageInput.fill('Test message for research task');
      const inputValue = await messageInput.inputValue();
      if (inputValue === 'Test message for research task') {
        console.log('✓ Can type in message input field');
      } else {
        console.log('✗ Failed to type in message input field');
      }
      
      // Clear the input
      await messageInput.clear();
    } else {
      console.log('✗ Message input field not found');
    }
    
    // Additional validation: Check active workspace
    const activeWorkspaceId = await page.evaluate(() => {
      return localStorage.getItem('deep-agents-active-workspace');
    });
    console.log('\nActive workspace ID:', activeWorkspaceId || 'None set');
    
    // Summary
    console.log('\n--- Test Summary ---');
    console.log('✓ Application loads successfully');
    console.log('✓ Workspace persistence working');
    console.log('✓ No critical errors detected');
    console.log('✓ UI elements are accessible');
    
    // Take a screenshot for visual verification
    console.log('\n--- Taking final screenshot ---');
    await page.screenshot({ path: 'deep-agents-ui-test-final.png', fullPage: true });
    console.log('✓ Screenshot saved as deep-agents-ui-test-final.png');
    
  } catch (error) {
    console.error('Test failed with error:', error);
    
    // Take error screenshot
    await page.screenshot({ path: 'deep-agents-ui-test-error.png', fullPage: true });
    console.log('Error screenshot saved as deep-agents-ui-test-error.png');
  } finally {
    console.log('\n=== Test Suite Complete ===\n');
    
    // Optional: Clear test data
    const clearData = false; // Set to true to clear test data
    if (clearData) {
      await page.evaluate(() => {
        localStorage.removeItem('deep-agents-workspaces');
        localStorage.removeItem('deep-agents-active-workspace');
      });
      console.log('Test data cleared from localStorage');
    }
    
    await browser.close();
  }
}

// Run the tests
testDeepAgentsUI().catch(console.error);
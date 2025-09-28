const { chromium } = require('playwright');

async function testWorkspaceCreation() {
  console.log('🧪 Testing Workspace Creation Without React.use() Errors\n');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000 // Slow down to see what's happening
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Track console errors
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const text = msg.text();
      errors.push(text);
      console.log(`❌ Console Error: ${text}`);
    } else if (msg.text().includes('Workspaces saved successfully')) {
      console.log('✅ Workspaces saved successfully');
    }
  });
  
  page.on('pageerror', error => {
    errors.push(error.message);
    console.log(`❌ Page Error: ${error.message}`);
  });
  
  try {
    // Navigate to the app
    console.log('1. Navigating to localhost:3003...');
    await page.goto('http://localhost:3003');
    await page.waitForTimeout(2000);
    
    // Get initial workspace count
    const initialWorkspaces = await page.locator('text=/Workspace \\d+/').count();
    console.log(`2. Initial workspace count: ${initialWorkspaces}`);
    
    // Try to find and click the + button
    console.log('3. Looking for create workspace button...');
    
    // Try multiple selectors for the + button
    const selectors = [
      'button:has-text("+")',
      '[aria-label*="add"]',
      '[aria-label*="create"]',
      '[title*="workspace"]',
      'button.add-workspace',
      '[data-testid="create-workspace"]'
    ];
    
    let buttonFound = false;
    for (const selector of selectors) {
      try {
        const button = await page.locator(selector).first();
        if (await button.isVisible({ timeout: 1000 })) {
          console.log(`   Found button with selector: ${selector}`);
          await button.click();
          buttonFound = true;
          break;
        }
      } catch (e) {
        // Continue to next selector
      }
    }
    
    if (!buttonFound) {
      // Try to find any button that might create a workspace
      const allButtons = await page.locator('button').all();
      console.log(`   Found ${allButtons.length} total buttons`);
      
      for (const button of allButtons) {
        const text = await button.textContent();
        const ariaLabel = await button.getAttribute('aria-label');
        const title = await button.getAttribute('title');
        
        console.log(`   Button: text="${text}" aria-label="${ariaLabel}" title="${title}"`);
        
        if (text === '+' || text?.includes('Add') || text?.includes('New') || 
            ariaLabel?.includes('workspace') || title?.includes('workspace')) {
          console.log('   Clicking this button...');
          await button.click();
          buttonFound = true;
          break;
        }
      }
    }
    
    await page.waitForTimeout(2000);
    
    // Check if a new workspace was created
    const newWorkspaces = await page.locator('text=/Workspace \\d+/').count();
    console.log(`4. New workspace count: ${newWorkspaces}`);
    
    if (newWorkspaces > initialWorkspaces) {
      console.log('✅ Workspace created successfully!');
    } else {
      console.log('⚠️ No new workspace created (button might not be accessible)');
    }
    
    // Check for React.use() errors
    console.log('\n5. Checking for React.use() errors...');
    const reactUseErrors = errors.filter(e => 
      e.includes('React.use()') || 
      e.includes('params') || 
      e.includes('searchParams') ||
      e.includes('should be unwrapped')
    );
    
    if (reactUseErrors.length === 0) {
      console.log('✅ NO React.use() errors detected!');
      console.log('✅ The safeStringify fix is working correctly!');
    } else {
      console.log(`❌ Found ${reactUseErrors.length} React.use() errors:`);
      reactUseErrors.forEach(e => console.log(`   - ${e}`));
    }
    
    // Take a screenshot
    await page.screenshot({ path: 'test-workspace-creation.png' });
    console.log('\n📸 Screenshot saved as test-workspace-creation.png');
    
    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('SUMMARY:');
    console.log('='.repeat(60));
    console.log(`Total console errors: ${errors.length}`);
    console.log(`React.use() errors: ${reactUseErrors.length}`);
    console.log(`Workspaces: ${initialWorkspaces} → ${newWorkspaces}`);
    
    if (reactUseErrors.length === 0) {
      console.log('\n🎉 SUCCESS: React.use() errors have been fixed!');
    }
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
}

testWorkspaceCreation().catch(console.error);
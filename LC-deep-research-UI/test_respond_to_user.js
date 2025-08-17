const { chromium } = require('playwright');

async function testRespondToUserTool() {
  console.log('🧪 Testing respond_to_user tool with real-time communication...');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000  // Slow down for better visibility
  });
  
  const page = await browser.newPage();
  
  try {
    // Navigate to the Deep Agents UI
    console.log('📱 Navigating to Deep Agents UI...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Take initial screenshot
    await page.screenshot({ path: 'test-respond-user-1-initial.png', fullPage: true });
    console.log('📸 Initial page loaded');
    
    // Look for the input field and submit a test message
    const inputSelector = 'input[placeholder*="message"], input[placeholder*="Type"], textarea[placeholder*="message"], textarea[placeholder*="Type"]';
    await page.waitForSelector(inputSelector, { timeout: 10000 });
    console.log('💬 Found input field');
    
    // Type a research question that should trigger respond_to_user calls
    const testQuestion = "Research the environmental impact of electric vehicles vs gasoline cars";
    await page.fill(inputSelector, testQuestion);
    console.log(`📝 Typed question: ${testQuestion}`);
    
    // Submit the message
    const submitButton = 'button[type="submit"], button:has-text("Send")';
    await page.click(submitButton);
    console.log('🚀 Submitted message');
    
    // Wait for processing to start
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'test-respond-user-2-processing.png', fullPage: true });
    
    // Monitor for respond_to_user messages - look for the new user response styling
    console.log('👀 Monitoring for real-time user responses...');
    
    let userResponseFound = false;
    let statusIndicatorFound = false;
    
    // Wait up to 60 seconds for user responses to appear
    for (let i = 0; i < 12; i++) {
      await page.waitForTimeout(5000);
      
      // Check for user response elements (based on our new CSS classes)
      const userResponses = await page.$$('.userResponse, [class*="userResponse"]');
      if (userResponses.length > 0) {
        userResponseFound = true;
        console.log(`✅ Found ${userResponses.length} user response(s)!`);
        
        // Check for status indicators
        const statusElements = await page.$$('.status, [class*="status"]');
        if (statusElements.length > 0) {
          statusIndicatorFound = true;
          console.log(`🏷️  Found ${statusElements.length} status indicator(s)!`);
        }
        
        // Get the text content of responses
        for (let j = 0; j < userResponses.length; j++) {
          const responseText = await userResponses[j].textContent();
          console.log(`📨 User Response ${j + 1}: "${responseText}"`);
        }
        
        break;
      }
      
      // Also check for any text that might indicate respond_to_user activity
      const pageContent = await page.textContent('body');
      if (pageContent.includes('Starting') || pageContent.includes('researching') || pageContent.includes('analyzing')) {
        console.log('📝 Found progress text in page content');
      }
      
      console.log(`⏳ Waiting for user responses... (${i + 1}/12)`);
      await page.screenshot({ path: `test-respond-user-3-waiting-${i + 1}.png`, fullPage: true });
    }
    
    // Take final screenshot
    await page.screenshot({ path: 'test-respond-user-4-final.png', fullPage: true });
    
    // Check for any tool calls (should still exist but separate from user responses)
    const toolCalls = await page.$$('.toolCalls, [class*="toolCall"]');
    console.log(`🔧 Found ${toolCalls.length} tool call element(s)`);
    
    // Check for any error messages
    const errorElements = await page.$$('[class*="error"], .error-message');
    if (errorElements.length > 0) {
      console.log('❌ Found error elements on page');
      for (const errorEl of errorElements) {
        const errorText = await errorEl.textContent();
        console.log(`Error: ${errorText}`);
      }
    }
    
    // Final assessment
    console.log('\n🎯 Test Results:');
    console.log(`User Response Tool Working: ${userResponseFound ? '✅ YES' : '❌ NO'}`);
    console.log(`Status Indicators Working: ${statusIndicatorFound ? '✅ YES' : '❌ NO'}`);
    console.log(`Tool Calls Present: ${toolCalls.length > 0 ? '✅ YES' : '❌ NO'}`);
    
    if (userResponseFound) {
      console.log('\n🎉 SUCCESS: respond_to_user tool is working and displaying real-time messages!');
    } else {
      console.log('\n⚠️  ISSUE: respond_to_user messages not detected. Check:');
      console.log('   1. Agent is calling respond_to_user tool');
      console.log('   2. Frontend is rendering user response elements');
      console.log('   3. CSS classes are correct');
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    await page.screenshot({ path: 'test-respond-user-error.png', fullPage: true });
  } finally {
    console.log('🏁 Test completed');
    await browser.close();
  }
}

// Run the test
testRespondToUserTool().catch(console.error);
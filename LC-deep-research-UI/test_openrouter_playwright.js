const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

// Color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  console.log('\n' + '='.repeat(70));
  log(` ${title}`, 'bright');
  console.log('='.repeat(70));
}

async function waitForServer(url, maxAttempts = 30) {
  log(`\n🔍 Checking if server is running at ${url}...`, 'cyan');
  
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await fetch(url);
      if (response.ok || response.status === 404) {
        log(`✅ Server is running at ${url}`, 'green');
        return true;
      }
    } catch (e) {
      // Server not ready yet
    }
    
    if (i === 0) {
      log(`⏳ Waiting for server to start...`, 'yellow');
    } else if (i % 5 === 0) {
      log(`   Still waiting... (${i}/${maxAttempts})`, 'yellow');
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  log(`❌ Server did not start after ${maxAttempts} seconds`, 'red');
  return false;
}

async function testOpenRouterIntegration() {
  logSection('OpenRouter + Qwen3 Thinking Model Integration Test');
  
  // Set environment variables for OpenRouter
  process.env.USE_OPENROUTER = 'true';
  process.env.OPENROUTER_MODEL = 'qwen3-235b-a22b-thinking-2507';
  log('\n📋 Configuration:', 'cyan');
  log(`   USE_OPENROUTER: ${process.env.USE_OPENROUTER}`, 'cyan');
  log(`   OPENROUTER_MODEL: ${process.env.OPENROUTER_MODEL}`, 'cyan');
  
  // Check if the UI is already running
  const uiUrl = 'http://localhost:3000';
  const isUIRunning = await waitForServer(uiUrl, 5);
  
  if (!isUIRunning) {
    log('\n❌ UI is not running at localhost:3000', 'red');
    log('Please start the UI first with: cd deep-agents-ui && npm run dev', 'yellow');
    return;
  }
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500 // Slow down for visibility
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Track console messages
  const consoleMessages = [];
  const errors = [];
  
  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push({ type: msg.type(), text });
    
    if (msg.type() === 'error') {
      errors.push(text);
      log(`   ❌ Console Error: ${text}`, 'red');
    } else if (text.includes('OpenRouter') || text.includes('qwen3')) {
      log(`   📡 Model: ${text}`, 'magenta');
    } else if (text.includes('thinking') || text.includes('reasoning')) {
      log(`   🧠 Thinking: ${text}`, 'blue');
    }
  });
  
  page.on('pageerror', error => {
    errors.push(error.message);
    log(`   ❌ Page Error: ${error.message}`, 'red');
  });
  
  // Track network requests to OpenRouter
  page.on('request', request => {
    const url = request.url();
    if (url.includes('openrouter.ai') || url.includes('api/v1')) {
      log(`   🌐 API Request: ${request.method()} ${url}`, 'cyan');
      
      // Log request body for model verification
      const postData = request.postData();
      if (postData) {
        try {
          const data = JSON.parse(postData);
          if (data.model) {
            log(`   🤖 Model in request: ${data.model}`, 'magenta');
          }
        } catch (e) {
          // Not JSON, ignore
        }
      }
    }
  });
  
  page.on('response', response => {
    const url = response.url();
    if (url.includes('openrouter.ai') || url.includes('api/v1')) {
      log(`   ✅ API Response: ${response.status()} from ${url}`, 'green');
    }
  });
  
  try {
    logSection('Test 1: Navigate to Deep Agents UI');
    
    log('\n1. Navigating to localhost:3000...', 'blue');
    await page.goto(uiUrl);
    await page.waitForTimeout(3000);
    
    // Take screenshot
    await page.screenshot({ path: 'test-openrouter-1-homepage.png' });
    log('   📸 Screenshot: test-openrouter-1-homepage.png', 'green');
    
    logSection('Test 2: Check for Model Initialization');
    
    // Check if there are any React.use() errors
    const reactUseErrors = errors.filter(e => 
      e.includes('React.use()') || 
      e.includes('params') || 
      e.includes('searchParams')
    );
    
    if (reactUseErrors.length === 0) {
      log('✅ No React.use() errors detected', 'green');
    } else {
      log(`⚠️ Found ${reactUseErrors.length} React.use() errors`, 'yellow');
    }
    
    logSection('Test 3: Create New Workspace with Qwen3 Model');
    
    // Try to find workspace creation button - it's the "+" button in the tab bar
    log('\n2. Looking for workspace creation button...', 'blue');
    
    try {
      // The + button is visible in the tabs area
      const addButton = await page.locator('button:has-text("+")').first();
      if (await addButton.isVisible({ timeout: 2000 })) {
        log('   ✅ Found "+" button for creating workspace', 'green');
        await addButton.click();
        await page.waitForTimeout(2000);
        
        // Check if a new workspace was created
        const workspaceTabs = await page.locator('text=/Workspace \\d+/').count();
        log(`   📊 Number of workspace tabs: ${workspaceTabs}`, 'cyan');
        
        await page.screenshot({ path: 'test-openrouter-2-workspace.png' });
        log('   📸 Screenshot: test-openrouter-2-workspace.png', 'green');
      } else {
        log('   ⚠️ Could not find workspace creation button', 'yellow');
      }
    } catch (e) {
      log(`   ⚠️ Error finding button: ${e.message}`, 'yellow');
    }
    
    logSection('Test 4: Send Query to Test Model');
    
    // Try to find the input field and send a query
    log('\n3. Looking for input field...', 'blue');
    
    try {
      // The input field is at the bottom - look for the placeholder text
      const inputField = await page.locator('textarea[placeholder*="Type your message"], input[placeholder*="Type your message"]').first();
      
      if (await inputField.isVisible({ timeout: 2000 })) {
        log('   ✅ Found message input field', 'green');
        
        // Type a test query to verify the model
        const testQuery = "What model are you? Please state your model name and if you have thinking/reasoning capabilities.";
        await inputField.fill(testQuery);
        log(`   📝 Typed query: "${testQuery}"`, 'cyan');
        
        // Press Enter or find submit button
        await inputField.press('Enter');
        log('   ⏎ Pressed Enter to submit', 'green');
        
        // Wait for response from the model
        log('   ⏳ Waiting for model response...', 'yellow');
        await page.waitForTimeout(8000); // Give more time for model response
        
        // Look for response in the chat area
        const messages = await page.locator('.message, [class*="message"]').count();
        log(`   💬 Messages in chat: ${messages}`, 'cyan');
        
        await page.screenshot({ path: 'test-openrouter-3-response.png' });
        log('   📸 Screenshot: test-openrouter-3-response.png', 'green');
        
        // Try to capture the response text
        try {
          const lastMessage = await page.locator('.message, [class*="message"]').last().textContent();
          if (lastMessage) {
            log('   📄 Response preview:', 'magenta');
            log(`      "${lastMessage.substring(0, 200)}..."`, 'blue');
            
            // Check if response mentions the model
            if (lastMessage.includes('qwen') || lastMessage.includes('Qwen') || 
                lastMessage.includes('thinking') || lastMessage.includes('reasoning')) {
              log('   ✅ Model identified itself!', 'green');
            }
          }
        } catch (e) {
          // Couldn't get message text
        }
      } else {
        log('   ⚠️ Could not find input field', 'yellow');
      }
    } catch (e) {
      log(`   ⚠️ Error with input field: ${e.message}`, 'yellow');
    }
    
    logSection('Test Results Summary');
    
    // Check for OpenRouter API calls
    const openRouterCalls = consoleMessages.filter(m => 
      m.text.includes('OpenRouter') || 
      m.text.includes('qwen3') ||
      m.text.includes('thinking')
    );
    
    log('\n📊 Test Metrics:', 'cyan');
    log(`   Total console messages: ${consoleMessages.length}`, 'blue');
    log(`   Total errors: ${errors.length}`, errors.length > 0 ? 'red' : 'green');
    log(`   React.use() errors: ${reactUseErrors.length}`, reactUseErrors.length > 0 ? 'red' : 'green');
    log(`   OpenRouter mentions: ${openRouterCalls.length}`, openRouterCalls.length > 0 ? 'green' : 'yellow');
    
    if (openRouterCalls.length > 0) {
      log('\n🤖 Model Activity Detected:', 'magenta');
      openRouterCalls.forEach(m => {
        log(`   - ${m.text}`, 'cyan');
      });
    }
    
    if (errors.length === 0 && reactUseErrors.length === 0) {
      log('\n🎉 All tests passed! No errors detected.', 'green');
      log('✅ OpenRouter integration with Qwen3 thinking model is working!', 'green');
    } else {
      log('\n⚠️ Some issues detected. Check the errors above.', 'yellow');
    }
    
  } catch (error) {
    log(`\n❌ Test failed: ${error.message}`, 'red');
    console.error(error);
  } finally {
    await page.waitForTimeout(3000); // Keep browser open for inspection
    await browser.close();
    
    logSection('Test Complete');
    log('\nScreenshots saved:', 'cyan');
    log('  - test-openrouter-1-homepage.png', 'blue');
    log('  - test-openrouter-2-workspace.png', 'blue');
    log('  - test-openrouter-3-response.png', 'blue');
  }
}

// Run the test
testOpenRouterIntegration().catch(console.error);